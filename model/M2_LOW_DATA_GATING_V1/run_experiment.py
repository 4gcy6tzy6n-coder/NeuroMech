#!/usr/bin/env python3
"""Equal-parameter low-data probe of M2-inspired state-conditioned updating."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
ID = "M2_LOW_DATA_GATING_V1"
OUT_DEFAULT = ROOT / "data/results" / ID
CONTRACT = ROOT / "summery" / ID / "CONTRACT.md"
SEEDS = tuple(range(70000, 70020))
TRAIN_SIZES = (16, 64, 256, 1024)
ARMS = ("MODE_GAIN_FILTER", "GENERIC_RNN_1D")
CONDITIONS = ("ALIGNED", "INDEPENDENT", "REVERSED")
T, NTEST, BATCH, UPDATES = 160, 256, 16, 250
NBOOT, BOOT_SEED = 20000, 20261001


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(seed: int, n: int):
    rng = np.random.default_rng(seed)
    phi = rng.uniform(.84, .96, n).astype(np.float32)
    sd_proc = rng.uniform(.08, .18, n).astype(np.float32)
    sd_obs = rng.uniform(.15, .35, n).astype(np.float32)
    x = np.zeros((n, T), np.float32)
    q = np.empty((n, T), np.float32)
    q[:, 0] = rng.choice(np.array([-1, 1], np.int8), n)
    eps = rng.standard_normal((n, T)).astype(np.float32)
    eta = rng.standard_normal((n, T)).astype(np.float32)
    flips = rng.random((n, T)) < .05
    for t in range(1, T):
        x[:, t] = phi * x[:, t - 1] + sd_proc * eps[:, t]
        q[:, t] = np.where(flips[:, t], -q[:, t - 1], q[:, t - 1])
    return x, q, eta, sd_obs


def observations(x, q, eta, sd_obs, condition):
    if condition == "ALIGNED":
        h = (q > 0).astype(np.float32)
    elif condition == "INDEPENDENT":
        h = np.full(q.shape, .5, np.float32)
    elif condition == "REVERSED":
        h = (q < 0).astype(np.float32)
    else:
        raise ValueError(condition)
    return h * x + sd_obs[:, None] * eta


class ScalarModel:
    def __init__(self, arm):
        self.arm = arm
        init = [3., 0., 0., 0.] if arm == "MODE_GAIN_FILTER" else [.5, 0., .7, 0.]
        self.raw = torch.nn.Parameter(torch.tensor(init, dtype=torch.float32))

    def parameters(self):
        return [self.raw]

    def rollout(self, y, q):
        n, steps = y.shape
        h = torch.zeros(n, dtype=y.dtype)
        out = []
        if self.arm == "MODE_GAIN_FILTER":
            rho = .999 * torch.sigmoid(self.raw[0])
            gp = torch.sigmoid(self.raw[1] + self.raw[2])
            gm = torch.sigmoid(self.raw[1] - self.raw[2])
            bias = .2 * torch.tanh(self.raw[3])
            for t in range(steps):
                pred = rho * h
                gain = torch.where(q[:, t] > 0, gp, gm)
                h = pred + gain * (y[:, t] - pred) + bias
                out.append(h)
        else:
            for t in range(steps):
                h = torch.tanh(self.raw[0] * y[:, t] + self.raw[1] * q[:, t] + self.raw[2] * h + self.raw[3])
                out.append(h)
        return torch.stack(out, dim=1)


def train_one(arm, y, q, x, batch_seed):
    torch.manual_seed(111)
    model = ScalarModel(arm)
    opt = torch.optim.Adam(model.parameters(), lr=.02)
    rng = np.random.default_rng(batch_seed)
    ty, tq, tx = (torch.from_numpy(a) for a in (y, q, x))
    losses = []
    start = time.perf_counter()
    for step in range(UPDATES):
        idx = torch.from_numpy(rng.integers(0, len(x), size=BATCH))
        pred = model.rollout(ty[idx], tq[idx])
        loss = ((pred - tx[idx]) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.)
        opt.step()
        losses.append(float(loss.detach()))
    return model, time.perf_counter() - start, float(np.mean(losses[-10:])), losses[0]


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"empty rows for {path}")
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def preflight(out):
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise FileExistsError(f"preflight requires an empty output directory: {out}")
    checks = []
    for arm in ARMS:
        m = ScalarModel(arm)
        assert sum(p.numel() for p in m.parameters()) == 4
        yy = torch.zeros((2, 4)); qq = torch.tensor([[1., -1., 1., -1.], [-1., -1., 1., 1.]])
        pred = m.rollout(yy, qq)
        assert pred.shape == yy.shape and torch.isfinite(pred).all()
        checks.append({"arm": arm, "parameter_count": 4, "output_shape": list(pred.shape), "finite": True})
    config = {"training_seeds": [SEEDS[0], SEEDS[-1]], "train_sizes": TRAIN_SIZES, "conditions": CONDITIONS,
              "test_sequences_per_seed_condition": NTEST, "sequence_length": T, "batch_size": BATCH,
              "optimizer_updates": UPDATES, "optimizer": "Adam(lr=0.02)", "bootstrap_resamples": NBOOT,
              "bootstrap_seed": BOOT_SEED}
    payload = {"experiment_id": ID, "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_BENCHMARK",
               "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
               "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)), "config": config,
               "preflight_checks": checks, "outcomes_computed": False}
    (out / "PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    pre = out / "PREFLIGHT.json"
    if not pre.exists():
        raise FileNotFoundError("run --preflight before outcome computation")
    pf = json.loads(pre.read_text())
    if pf["contract_sha256"] != sha(CONTRACT) or pf["runner_sha256"] != sha(Path(__file__)):
        raise RuntimeError("contract or runner changed after preflight")
    if any((out / n).exists() for n in ("episode_metrics.csv", "training_metrics.csv", "summary.json")):
        raise FileExistsError(f"refusing to overwrite existing experiment outputs: {out}")
    torch.set_num_threads(1)
    train_rows, eval_rows = [], []
    # Every training seed gets nested training pools and a paired, shared test set.
    for si, seed in enumerate(SEEDS):
        tx, tq, tnoise, tsd = generate(seed * 31 + 9, max(TRAIN_SIZES))
        ty = observations(tx, tq, tnoise, tsd, "ALIGNED")
        ex, eq, enoise, esd = generate(900000 + seed, NTEST)
        ey = {c: observations(ex, eq, enoise, esd, c) for c in CONDITIONS}
        for ni, ntrain in enumerate(TRAIN_SIZES):
            xpool, qpool, ypool = tx[:ntrain], tq[:ntrain], ty[:ntrain]
            for ai, arm in enumerate(ARMS):
                model, elapsed, final_loss, first_loss = train_one(
                    arm, ypool, qpool, xpool, 8000000 + seed * 101 + ni * 7)
                train_rows.append({"training_seed": seed, "train_size": ntrain, "arm": arm,
                                   "parameter_count": 4, "optimizer_updates": UPDATES,
                                   "batch_size": BATCH, "sample_tokens": UPDATES * BATCH * T,
                                   "training_seconds": elapsed, "initial_batch_loss": first_loss,
                                   "final_10_update_loss": final_loss,
                                   "parameters_json": json.dumps(model.raw.detach().numpy().tolist())})
                with torch.no_grad():
                    for cond in CONDITIONS:
                        pred = model.rollout(torch.from_numpy(ey[cond]), torch.from_numpy(eq))
                        mse = ((pred - torch.from_numpy(ex)) ** 2).mean(dim=1).numpy()
                        for ep, v in enumerate(mse):
                            eval_rows.append({"training_seed": seed, "train_size": ntrain,
                                              "condition": cond, "episode_id": ep, "arm": arm,
                                              "episode_mse": float(v)})
        print(f"completed paired sample-efficiency seed {seed} ({si + 1}/{len(SEEDS)})", flush=True)
    write_csv(out / "training_metrics.csv", train_rows)
    write_csv(out / "episode_metrics.csv", eval_rows)
    summary = summarize(eval_rows)
    summary.update({"experiment_id": ID, "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_BENCHMARK",
                    "primary_unit": "paired_training_seed", "training_seeds": list(SEEDS),
                    "train_sizes": list(TRAIN_SIZES), "test_sequences_per_seed_condition": NTEST,
                    "conditions": list(CONDITIONS), "parameter_count_each_arm": 4,
                    "optimizer_updates_each_fit": UPDATES, "batch_size": BATCH,
                    "sample_tokens_each_fit": UPDATES * BATCH * T,
                    "bootstrap_resamples": NBOOT, "bootstrap_seed": BOOT_SEED})
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    files = ("PREFLIGHT.json", "episode_metrics.csv", "training_metrics.csv", "summary.json")
    manifest = {"experiment_id": ID, "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
                "sha256": {n: sha(out / n) for n in files}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return summary


def summarize(rows):
    # Preserve episode and training-seed pairing in the seed bootstrap.
    by = {}
    for r in rows:
        key = (int(r["training_seed"]), int(r["train_size"]), r["condition"], r["arm"])
        by.setdefault(key, []).append(float(r["episode_mse"]))
    means = {k: float(np.mean(v)) for k, v in by.items()}
    per_seed = []
    for seed in SEEDS:
        row = {"training_seed": seed}
        for ntrain in TRAIN_SIZES:
            for cond in CONDITIONS:
                mode = means[(seed, ntrain, cond, ARMS[0])]
                generic = means[(seed, ntrain, cond, ARMS[1])]
                row[f"{cond}_{ntrain}_mode_mse"] = mode
                row[f"{cond}_{ntrain}_generic_mse"] = generic
                row[f"{cond}_{ntrain}_generic_minus_mode"] = generic - mode
        row["aligned_equal_size_mean_generic_minus_mode"] = float(np.mean([
            row[f"ALIGNED_{n}_generic_minus_mode"] for n in TRAIN_SIZES]))
        per_seed.append(row)
    primary = np.array([r["aligned_equal_size_mean_generic_minus_mode"] for r in per_seed])
    rng = np.random.default_rng(BOOT_SEED)
    indices = rng.integers(0, len(primary), size=(NBOOT, len(primary)))
    ci = np.quantile(primary[indices].mean(axis=1), [.025, .975]).tolist()
    effects = {}
    for cond in CONDITIONS:
        effects[cond] = {}
        for ntrain in TRAIN_SIZES:
            values = np.array([r[f"{cond}_{ntrain}_generic_minus_mode"] for r in per_seed])
            eci = np.quantile(values[indices].mean(axis=1), [.025, .975]).tolist()
            effects[cond][str(ntrain)] = {"mean_generic_minus_mode_mse": float(values.mean()),
                                         "seed_bootstrap_ci95": [float(eci[0]), float(eci[1])],
                                         "positive_seed_count": int((values > 0).sum()),
                                         "mode_gain_mse": means_mean(means, cond, ntrain, ARMS[0]),
                                         "generic_rnn_mse": means_mean(means, cond, ntrain, ARMS[1])}
    return {"primary_aligned_equal_train_size_mean_generic_minus_mode_mse": {
                "mean": float(primary.mean()), "seed_bootstrap_ci95": [float(ci[0]), float(ci[1])],
                "positive_seed_count": int((primary > 0).sum())},
            "effects_by_condition_and_training_size": effects,
            "per_training_seed_primary": per_seed}


def means_mean(means, condition, ntrain, arm):
    return float(np.mean([means[(seed, ntrain, condition, arm)] for seed in SEEDS]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--preflight", action="store_true")
    args = ap.parse_args()
    out = args.output_dir.resolve()
    print(json.dumps(preflight(out) if args.preflight else run(out), indent=2))
