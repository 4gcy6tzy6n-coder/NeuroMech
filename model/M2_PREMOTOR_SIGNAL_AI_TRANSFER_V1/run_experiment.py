#!/usr/bin/env python3
"""Artificial transfer probe for a short-horizon premotor-like predictive cue."""
from __future__ import annotations

import argparse, csv, hashlib, json, platform, time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_PREMOTOR_SIGNAL_AI_TRANSFER_V1"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
OUT_DEFAULT = ROOT / "data/results" / EXP
SEEDS = tuple(range(62000, 62020))
SIZES = (32, 128, 512)
Q_CONDITIONS = {"ALIGNED": 0.72, "UNINFORMATIVE": 0.50, "REVERSED": 0.28}
TRAIN_Q = 0.72
T, HORIZON, HIDDEN = 80, 4, 2
NTEST, BATCH, UPDATES, LR = 128, 16, 160, 0.01
HAZARD, OBS_SD, VISIBLE_RUN = 0.05, 1.25, 4
BOOT, BOOT_SEED = 20000, 20261014
LEARNED = ("PREMOTOR_FILTER", "NO_CUE_FILTER", "GRU_CUE", "GRU_NO_CUE")
ALL_ARMS = LEARNED + ("CUE_ONLY", "PREMOTOR_FILTER_YOKED_CUE", "GRU_CUE_YOKED_CUE")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def generate(seed, n):
    state_rng, flip_rng, obs_rng, vis_rng, vis0_rng, cue_rng = [
        np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(6)]
    state = np.empty((n, T), np.float32)
    state[:, 0] = state_rng.choice(np.array([-1., 1.], np.float32), n)
    flips = flip_rng.random((n, T)) < HAZARD
    for t in range(1, T):
        state[:, t] = np.where(flips[:, t], -state[:, t - 1], state[:, t - 1])
    visible = np.empty((n, T), np.float32)
    visible[:, 0] = vis0_rng.integers(0, 2, n)
    vis_draw = vis_rng.random((n, T))
    p_change = 1.0 / VISIBLE_RUN
    for t in range(1, T):
        visible[:, t] = np.where(visible[:, t - 1] > 0,
                                 (vis_draw[:, t] >= p_change).astype(np.float32),
                                 (vis_draw[:, t] < p_change).astype(np.float32))
    observation = (state + obs_rng.normal(0, OBS_SD, (n, T)).astype(np.float32)) * visible
    target = state[:, HORIZON:].copy()
    cue_draw = cue_rng.random(target.shape)
    cues = {}
    for name, q in Q_CONDITIONS.items():
        cues[name] = np.where(cue_draw < q, target, -target).astype(np.float32)
    return observation[:, :-HORIZON], visible[:, :-HORIZON], target, cues


class PremotorFilter(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.w = torch.nn.Parameter(torch.tensor([0.8, 0.3, 0.0, 1.0, 0.6, 0.0], dtype=torch.float32))

    def forward(self, obs, visible, cue):
        h = torch.zeros(obs.shape[0], dtype=obs.dtype, device=obs.device)
        logits = []
        for t in range(obs.shape[1]):
            h = torch.tanh(self.w[0] * h + self.w[1] * obs[:, t] + self.w[2] * visible[:, t])
            logits.append(self.w[3] * h + self.w[4] * cue[:, t] + self.w[5])
        return torch.stack(logits, dim=1)


class TinyGRU(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.cell = torch.nn.GRUCell(3, HIDDEN)
        self.readout = torch.nn.Linear(HIDDEN, 1)

    def forward(self, obs, visible, cue):
        h = torch.zeros(obs.shape[0], HIDDEN, dtype=obs.dtype, device=obs.device)
        logits = []
        for t in range(obs.shape[1]):
            h = self.cell(torch.stack((obs[:, t], visible[:, t], cue[:, t]), dim=1), h)
            logits.append(self.readout(h).squeeze(1))
        return torch.stack(logits, dim=1)


def build(arm):
    return PremotorFilter() if arm in ("PREMOTOR_FILTER", "NO_CUE_FILTER") else TinyGRU()


def model_input(arm, obs, visible, cue):
    if arm in ("NO_CUE_FILTER", "GRU_NO_CUE"):
        return torch.zeros_like(cue)
    return cue


def preflight(out):
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"preflight requires an empty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    obs, vis, target, cues = generate(19, 8)
    checks = []
    for i, arm in enumerate(LEARNED):
        torch.manual_seed(9100 + i)
        model = build(arm)
        to = torch.from_numpy(obs); tv = torch.from_numpy(vis); tc = torch.from_numpy(cues["ALIGNED"])
        ty = torch.from_numpy(target)
        logits = model(to, tv, model_input(arm, to, tv, tc))
        loss = F.binary_cross_entropy_with_logits(logits, (ty > 0).float())
        loss.backward()
        checks.append({"arm": arm, "parameter_count": sum(p.numel() for p in model.parameters()),
                       "finite_loss": bool(torch.isfinite(loss)),
                       "finite_gradients": all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters()),
                       "output_shape": list(logits.shape)})
    payload = {"experiment_id": EXP, "outcomes_computed": False,
               "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
               "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
               "seeds": [SEEDS[0], SEEDS[-1]], "sizes": SIZES, "test_episodes": NTEST,
               "conditions": Q_CONDITIONS, "arms": ALL_ARMS, "checks": checks}
    (out / "PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


def train_one(arm, obs, vis, target, cue, seed):
    torch.manual_seed(seed)
    model = build(arm)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    rng = np.random.default_rng(seed + 991)
    to, tv, ty, tc = map(torch.from_numpy, (obs, vis, target, cue))
    losses = []
    start = time.perf_counter()
    for _ in range(UPDATES):
        ix = torch.from_numpy(rng.integers(0, len(target), BATCH))
        c = model_input(arm, to[ix], tv[ix], tc[ix])
        logits = model(to[ix], tv[ix], c)
        loss = F.binary_cross_entropy_with_logits(logits, (ty[ix] > 0).float())
        optimizer.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0); optimizer.step()
        losses.append(float(loss.detach()))
    return model, {"training_seconds": time.perf_counter() - start,
                   "initial_loss": losses[0], "final_10_update_loss": float(np.mean(losses[-10:])),
                   "parameter_count": sum(p.numel() for p in model.parameters())}


def score_episode(logits, target):
    y = (target > 0).astype(np.int8)
    if np.unique(y).size < 2:
        return {"auc": None, "brier": float(np.mean((1. / (1. + np.exp(-np.clip(logits, -30, 30))) - y) ** 2)),
                "n_positive": int(y.sum()), "n_negative": int(len(y) - y.sum())}
    p = 1. / (1. + np.exp(-np.clip(logits, -30, 30)))
    return {"auc": float(roc_auc_score(y, logits)), "brier": float(np.mean((p - y) ** 2)),
            "n_positive": int(y.sum()), "n_negative": int(len(y) - y.sum())}


def effect(rows, arm_a, arm_b, size, condition):
    by_seed = []
    for seed in SEEDS:
        means = {}
        for arm in (arm_a, arm_b):
            vals = [float(r["auc"]) for r in rows if int(r["training_seed"]) == seed and
                    int(r["train_size"]) == size and r["condition"] == condition and r["arm"] == arm and r["auc"] is not None]
            means[arm] = float(np.mean(vals)) if vals else np.nan
        if np.isfinite(means[arm_a]) and np.isfinite(means[arm_b]):
            by_seed.append(means[arm_a] - means[arm_b])
    x = np.asarray(by_seed)
    if not len(x):
        return {"status": "NOT_ESTIMABLE", "per_seed": []}
    rng = np.random.default_rng(BOOT_SEED)
    samples = x[rng.integers(0, len(x), (BOOT, len(x)))].mean(axis=1)
    ci = np.quantile(samples, [0.025, 0.975])
    return {"status": "DESCRIPTIVE_SEED_BLOCK_BOOTSTRAP", "arm_a_minus_arm_b": float(x.mean()),
            "seed_bootstrap_95pct_interval": [float(ci[0]), float(ci[1])],
            "positive_seed_count": int((x > 0).sum()), "seed_blocks": len(x), "per_seed": x.tolist()}


def run(out):
    pre = json.loads((out / "PREFLIGHT.json").read_text())
    if pre["contract_sha256"] != sha(CONTRACT) or pre["runner_sha256"] != sha(Path(__file__)):
        raise RuntimeError("contract or runner changed after preflight")
    if any((out / n).exists() for n in ("episode_metrics.csv", "training_metrics.csv", "summary.json")):
        raise FileExistsError(f"refusing to overwrite existing result files in {out}")
    torch.set_num_threads(1)
    episode_rows, fit_rows = [], []
    for sidx, seed in enumerate(SEEDS):
        obs_train, vis_train, target_train, cues_train = generate(seed * 83 + 17, max(SIZES))
        obs_test, vis_test, target_test, cues_test = generate(880000 + seed, NTEST)
        for ntrain in SIZES:
            for aidx, arm in enumerate(LEARNED):
                model, train_info = train_one(arm, obs_train[:ntrain], vis_train[:ntrain], target_train[:ntrain],
                                              cues_train["ALIGNED"][:ntrain], 7000000 + seed * 11 + ntrain + aidx)
                fit_rows.append({"training_seed": seed, "train_size": ntrain, "arm": arm,
                                 "optimizer_updates": UPDATES, "batch_size": BATCH,
                                 "sample_tokens": UPDATES * BATCH * (T - HORIZON), **train_info})
                model.eval()
                with torch.no_grad():
                    for condition, cue_np in cues_test.items():
                        c0 = torch.from_numpy(cue_np)
                        if arm in ("PREMOTOR_FILTER", "GRU_CUE"):
                            for label, c_np in ((arm, cue_np), (arm + "_YOKED_CUE", np.roll(cue_np, 1, axis=0))):
                                cc = torch.from_numpy(c_np)
                                logits = model(torch.from_numpy(obs_test), torch.from_numpy(vis_test), cc).numpy()
                                for ep in range(NTEST):
                                    m = score_episode(logits[ep], target_test[ep])
                                    episode_rows.append({"training_seed": seed, "test_seed": 880000 + seed,
                                        "train_size": ntrain, "condition": condition, "episode_id": ep,
                                        "arm": label, **m})
                        else:
                            cc = model_input(arm, torch.from_numpy(obs_test), torch.from_numpy(vis_test), c0)
                            logits = model(torch.from_numpy(obs_test), torch.from_numpy(vis_test), cc).numpy()
                            for ep in range(NTEST):
                                m = score_episode(logits[ep], target_test[ep])
                                episode_rows.append({"training_seed": seed, "test_seed": 880000 + seed,
                                    "train_size": ntrain, "condition": condition, "episode_id": ep,
                                    "arm": arm, **m})
            for condition, cue_np in cues_test.items():
                for ep in range(NTEST):
                    m = score_episode(cue_np[ep] * 1.1, target_test[ep])
                    episode_rows.append({"training_seed": seed, "test_seed": 880000 + seed,
                        "train_size": ntrain, "condition": condition, "episode_id": ep,
                        "arm": "CUE_ONLY", **m})
        print(f"completed train/test seed block {seed} ({sidx + 1}/{len(SEEDS)})", flush=True)
    for name, rows in (("episode_metrics.csv", episode_rows), ("training_metrics.csv", fit_rows)):
        with (out / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    summary = {"experiment_id": EXP, "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_TRANSFER_PROBE",
               "primary_condition": "ALIGNED", "primary_train_size": 128,
               "primary_metric": "mean per-episode AUC, unit aggregated by paired train/test seed block",
               "primary_contrasts": {
                   "cue_value_structured": effect(episode_rows, "PREMOTOR_FILTER", "NO_CUE_FILTER", 128, "ALIGNED"),
                   "structured_vs_generic": effect(episode_rows, "PREMOTOR_FILTER", "GRU_CUE", 128, "ALIGNED"),
                   "cue_value_generic": effect(episode_rows, "GRU_CUE", "GRU_NO_CUE", 128, "ALIGNED"),
                   "recipient_contingency_structured": effect(episode_rows, "PREMOTOR_FILTER", "PREMOTOR_FILTER_YOKED_CUE", 128, "ALIGNED")},
               "contrasts_by_train_size_condition": {}, "arm_means": {},
               "training": {"seeds": list(SEEDS), "sizes": list(SIZES), "conditions": Q_CONDITIONS,
                            "updates": UPDATES, "batch": BATCH, "sample_tokens_per_fit": UPDATES * BATCH * (T - HORIZON),
                            "hidden_units": HIDDEN, "optimizer": "Adam", "learning_rate": LR},
               "parameter_counts": {r["arm"]: r["parameter_count"] for r in fit_rows if r["train_size"] == SIZES[0] and r["training_seed"] == SEEDS[0]},
               "scorable_episode_counts": {}}
    for ntrain in SIZES:
        summary["contrasts_by_train_size_condition"][str(ntrain)] = {}
        summary["arm_means"][str(ntrain)] = {}
        for condition in Q_CONDITIONS:
            summary["contrasts_by_train_size_condition"][str(ntrain)][condition] = {
                "structured_minus_no_cue": effect(episode_rows, "PREMOTOR_FILTER", "NO_CUE_FILTER", ntrain, condition),
                "structured_minus_generic_gru": effect(episode_rows, "PREMOTOR_FILTER", "GRU_CUE", ntrain, condition),
                "generic_cue_minus_no_cue": effect(episode_rows, "GRU_CUE", "GRU_NO_CUE", ntrain, condition),
                "structured_minus_yoked": effect(episode_rows, "PREMOTOR_FILTER", "PREMOTOR_FILTER_YOKED_CUE", ntrain, condition)}
            summary["arm_means"][str(ntrain)][condition] = {}
            for arm in ALL_ARMS:
                vals = [r["auc"] for r in episode_rows if r["train_size"] == ntrain and r["condition"] == condition and r["arm"] == arm and r["auc"] is not None]
                summary["arm_means"][str(ntrain)][condition][arm] = float(np.mean(vals)) if vals else None
                summary["scorable_episode_counts"][f"{ntrain}|{condition}|{arm}"] = len(vals)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    files = ("PREFLIGHT.json", "episode_metrics.csv", "training_metrics.csv", "summary.json")
    manifest = {"experiment_id": EXP, "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
                "sha256": {name: sha(out / name) for name in files}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary["primary_contrasts"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args(); output = args.output_dir.resolve()
    preflight(output) if args.preflight else run(output)
