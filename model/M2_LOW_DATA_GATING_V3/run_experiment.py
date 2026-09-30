#!/usr/bin/env python3
"""M2 state-gating probe with context-free, bilinear, and Kalman references."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
ID = "M2_LOW_DATA_GATING_V3"
OUT_DEFAULT = ROOT / "data/results" / ID
CONTRACT = ROOT / "summery" / ID / "CONTRACT.md"
SEEDS = tuple(range(72000, 72020))
SIZES = (16, 64, 256, 1024)
LEARNED = ("MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "LINEAR_BILINEAR_RNN")
ARMS = LEARNED + ("KALMAN_ORACLE",)
CONDITIONS = ("ALIGNED", "INDEPENDENT", "REVERSED")
T, NTEST, BATCH, UPDATES = 160, 256, 16, 250
NBOOT, BOOT_SEED = 20000, 20261003


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(seed, n):
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
    return x, q, eta, phi, sd_proc, sd_obs


def obs_coeff(q, condition):
    if condition == "ALIGNED":
        return (q > 0).astype(np.float32)
    if condition == "INDEPENDENT":
        return np.full(q.shape, .5, np.float32)
    if condition == "REVERSED":
        return (q < 0).astype(np.float32)
    raise ValueError(condition)


def observations(x, q, eta, sd_obs, condition):
    return obs_coeff(q, condition) * x + sd_obs[:, None] * eta


class Model:
    def __init__(self, arm):
        self.arm = arm
        init = {
            "MODE_GAIN_FILTER": [3., 0., 0., 0.],
            "CONSTANT_GAIN_FILTER": [3., 0., 0.],
            "LINEAR_BILINEAR_RNN": [.2, 0., .2, .4, 0.],
        }[arm]
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
        elif self.arm == "CONSTANT_GAIN_FILTER":
            rho = .999 * torch.sigmoid(self.raw[0])
            gain = torch.sigmoid(self.raw[1])
            bias = .2 * torch.tanh(self.raw[2])
            for t in range(steps):
                pred = rho * h
                h = pred + gain * (y[:, t] - pred) + bias
                out.append(h)
        else:
            wy, wq, wyq = .5 * torch.tanh(self.raw[:3])
            wh, whq = .4 * torch.tanh(self.raw[3]), .4 * torch.tanh(self.raw[4])
            for t in range(steps):
                h = wy * y[:, t] + wq * q[:, t] + wyq * y[:, t] * q[:, t] + wh * h + whq * q[:, t] * h
                out.append(h)
        return torch.stack(out, dim=1)


def kalman(y, q, phi, sd_proc, sd_obs, condition):
    n, steps = y.shape
    hcoef = obs_coeff(q, condition)
    mean = np.zeros(n, dtype=np.float64)
    var = np.zeros(n, dtype=np.float64)
    out = np.zeros((n, steps), dtype=np.float32)
    for t in range(steps):
        if t:
            mean = phi * mean
            var = phi * phi * var + sd_proc * sd_proc
        ht = hcoef[:, t]
        gain = var * ht / (ht * ht * var + sd_obs * sd_obs)
        mean = mean + gain * (y[:, t] - ht * mean)
        var = (1. - gain * ht) * var
        out[:, t] = mean
    return out


def train_one(arm, y, q, x, batch_seed):
    model = Model(arm)
    opt = torch.optim.Adam(model.parameters(), lr=.02)
    rng = np.random.default_rng(batch_seed)
    ty, tq, tx = (torch.from_numpy(a) for a in (y, q, x))
    start = time.perf_counter()
    losses = []
    for _ in range(UPDATES):
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
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def paired_effect(rows, a, b, cond, size=None):
    # Difference MSE(b) - MSE(a), paired by training seed; episodes are nested.
    seed_values = []
    for seed in SEEDS:
        sizes = (size,) if size is not None else SIZES
        ds = []
        for ntrain in sizes:
            ma = []; mb = []
            for r in rows:
                if int(r["training_seed"]) != seed or int(r["train_size"]) != ntrain or r["condition"] != cond:
                    continue
                if r["arm"] == a: ma.append(float(r["episode_mse"]))
                elif r["arm"] == b: mb.append(float(r["episode_mse"]))
            if len(ma) != NTEST or len(mb) != NTEST:
                raise ValueError(f"incomplete paired grid: seed={seed}, n={ntrain}, condition={cond}")
            ds.append(float(np.mean(mb) - np.mean(ma)))
        seed_values.append(float(np.mean(ds)))
    vals = np.asarray(seed_values)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(vals), size=(NBOOT, len(vals)))
    ci = np.quantile(vals[idx].mean(axis=1), [.025, .975])
    return {"mean_b_minus_a_mse": float(vals.mean()), "seed_bootstrap_ci95": [float(ci[0]), float(ci[1])],
            "positive_seed_count": int((vals > 0).sum()), "per_seed": vals.tolist()}


def means_by(rows):
    out = {}
    for n in SIZES:
        out[str(n)] = {}
        for c in CONDITIONS:
            out[str(n)][c] = {}
            for arm in ARMS:
                vals = [float(r["episode_mse"]) for r in rows if int(r["train_size"]) == n
                        and r["condition"] == c and r["arm"] == arm]
                out[str(n)][c][arm] = float(np.mean(vals))
    return out


def preflight(out):
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise FileExistsError(f"preflight requires an empty output directory: {out}")
    checks = []
    y = torch.zeros((2, 4)); q = torch.tensor([[1., -1., 1., -1.], [-1., 1., -1., 1.]])
    for arm in LEARNED:
        m = Model(arm); pred = m.rollout(y, q)
        assert pred.shape == y.shape and torch.isfinite(pred).all()
        checks.append({"arm": arm, "parameter_count": sum(p.numel() for p in m.parameters()), "finite": True})
    checks.append({"arm": "KALMAN_ORACLE", "parameter_count": 0, "finite": True})
    config = {"seeds": [SEEDS[0], SEEDS[-1]], "train_sizes": SIZES, "conditions": CONDITIONS,
              "arms": ARMS, "test_sequences_per_seed_condition": NTEST, "sequence_length": T,
              "updates": UPDATES, "batch_size": BATCH, "bootstrap_resamples": NBOOT,
              "bootstrap_seed": BOOT_SEED}
    payload = {"experiment_id": ID, "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_BENCHMARK",
               "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
               "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)), "config": config,
               "preflight_checks": checks, "outcomes_computed": False}
    (out / "PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    pfpath = out / "PREFLIGHT.json"
    if not pfpath.exists(): raise FileNotFoundError("run --preflight first")
    pf = json.loads(pfpath.read_text())
    if pf["contract_sha256"] != sha(CONTRACT) or pf["runner_sha256"] != sha(Path(__file__)):
        raise RuntimeError("contract or runner changed after preflight")
    if any((out / n).exists() for n in ("episode_metrics.csv", "training_metrics.csv", "summary.json")):
        raise FileExistsError(f"refusing to overwrite existing outputs: {out}")
    torch.set_num_threads(1)
    train_rows, eval_rows = [], []
    for si, seed in enumerate(SEEDS):
        xpool, qpool, noise, _, _, sdobs = generate(seed * 37 + 29, max(SIZES))
        ypool = observations(xpool, qpool, noise, sdobs, "ALIGNED")
        ex, eq, en, phi, sdproc, esdobs = generate(930000 + seed, NTEST)
        eval_y = {c: observations(ex, eq, en, esdobs, c) for c in CONDITIONS}
        for ni, ntrain in enumerate(SIZES):
            for ai, arm in enumerate(LEARNED):
                model, seconds, lastloss, firstloss = train_one(
                    arm, ypool[:ntrain], qpool[:ntrain], xpool[:ntrain], 10000000 + seed * 101 + ni * 11)
                nparam = sum(p.numel() for p in model.parameters())
                train_rows.append({"training_seed": seed, "train_size": ntrain, "arm": arm,
                                   "parameter_count": nparam, "optimizer_updates": UPDATES,
                                   "batch_size": BATCH, "sample_tokens": UPDATES * BATCH * T,
                                   "training_seconds": seconds, "initial_batch_loss": firstloss,
                                   "final_10_update_loss": lastloss,
                                   "parameters_json": json.dumps(model.raw.detach().numpy().tolist())})
                with torch.no_grad():
                    for c in CONDITIONS:
                        pred = model.rollout(torch.from_numpy(eval_y[c]), torch.from_numpy(eq)).numpy()
                        mse = np.mean((pred - ex) ** 2, axis=1)
                        for ep, v in enumerate(mse):
                            eval_rows.append({"training_seed": seed, "train_size": ntrain,
                                              "condition": c, "episode_id": ep, "arm": arm,
                                              "episode_mse": float(v)})
            for c in CONDITIONS:
                pred = kalman(eval_y[c], eq, phi, sdproc, esdobs, c)
                mse = np.mean((pred - ex) ** 2, axis=1)
                for ep, v in enumerate(mse):
                    eval_rows.append({"training_seed": seed, "train_size": ntrain,
                                      "condition": c, "episode_id": ep, "arm": "KALMAN_ORACLE",
                                      "episode_mse": float(v)})
        print(f"completed control-calibration seed {seed} ({si + 1}/{len(SEEDS)})", flush=True)
    write_csv(out / "episode_metrics.csv", eval_rows)
    write_csv(out / "training_metrics.csv", train_rows)
    summary = {
        "primary_aligned_bilinear_minus_mode_equal_train_size_mean": paired_effect(eval_rows, "MODE_GAIN_FILTER", "LINEAR_BILINEAR_RNN", "ALIGNED"),
        "context_ablation_aligned_constant_minus_mode_equal_train_size_mean": paired_effect(eval_rows, "MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "ALIGNED"),
        "contrasts_by_condition_and_train_size": {c: {str(n): {
            "bilinear_minus_mode": paired_effect(eval_rows, "MODE_GAIN_FILTER", "LINEAR_BILINEAR_RNN", c, n),
            "constant_minus_mode": paired_effect(eval_rows, "MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", c, n),
        } for n in SIZES} for c in CONDITIONS},
        "mean_mse_by_train_size_condition_arm": means_by(eval_rows),
        "training_time_seconds_by_arm": {a: float(np.mean([float(r["training_seconds"]) for r in train_rows if r["arm"] == a])) for a in LEARNED},
        "experiment_id": ID, "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_BENCHMARK",
        "training_seeds": list(SEEDS), "train_sizes": list(SIZES), "conditions": list(CONDITIONS),
        "arms": list(ARMS), "primary_unit": "paired_training_seed", "test_sequences_per_seed_condition": NTEST,
        "updates_per_fit": UPDATES, "batch_size": BATCH, "sample_tokens_per_fit": UPDATES * BATCH * T,
        "parameter_count": {a: (sum(p.numel() for p in Model(a).parameters()) if a in LEARNED else 0) for a in ARMS},
        "bootstrap_resamples": NBOOT, "bootstrap_seed": BOOT_SEED}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    files = ("PREFLIGHT.json", "episode_metrics.csv", "training_metrics.csv", "summary.json")
    manifest = {"experiment_id": ID, "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
                "sha256": {n: sha(out / n) for n in files}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--preflight", action="store_true")
    args = ap.parse_args(); out = args.output_dir.resolve()
    print(json.dumps(preflight(out) if args.preflight else run(out), indent=2))
