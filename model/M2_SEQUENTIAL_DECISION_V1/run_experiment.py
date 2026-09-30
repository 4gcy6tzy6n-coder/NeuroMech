#!/usr/bin/env python3
"""M2-inspired state-gated integration on a new sequential decision task."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
ID = "M2_SEQUENTIAL_DECISION_V1"
OUT_DEFAULT = ROOT / "data/results" / ID
CONTRACT = ROOT / "summery" / ID / "CONTRACT.md"
SEEDS = tuple(range(73000, 73020))
SIZES = (16, 64, 256, 1024)
LEARNED = ("MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "LINEAR_BILINEAR_RNN")
ARMS = LEARNED + ("BAYES_ORACLE",)
CONDITIONS = ("ALIGNED", "INDEPENDENT", "REVERSED")
T, NTEST, BATCH, UPDATES = 32, 512, 16, 250
MU, NOISE_SD, QSWITCH = .18, .7, .25
NBOOT, BOOT_SEED = 20000, 20261004


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(seed, n):
    rng = np.random.default_rng(seed)
    target = rng.choice(np.array([-1., 1.], np.float32), n)
    q = np.empty((n, T), np.float32)
    q[:, 0] = rng.choice(np.array([-1., 1.], np.float32), n)
    flips = rng.random((n, T)) < QSWITCH
    noise = rng.standard_normal((n, T)).astype(np.float32)
    for t in range(1, T):
        q[:, t] = np.where(flips[:, t], -q[:, t - 1], q[:, t - 1])
    return target, q, noise


def context_gain(q, condition):
    if condition == "ALIGNED":
        return (q > 0).astype(np.float32)
    if condition == "INDEPENDENT":
        return np.full(q.shape, .5, np.float32)
    if condition == "REVERSED":
        return (q < 0).astype(np.float32)
    raise ValueError(condition)


def make_observation(target, q, noise, condition):
    return context_gain(q, condition) * (MU * target[:, None]) + NOISE_SD * noise


class Model:
    def __init__(self, arm):
        self.arm = arm
        init = {
            "MODE_GAIN_FILTER": [2.5, 0., 0., 0.],
            "CONSTANT_GAIN_FILTER": [2.5, 0., 0.],
            "LINEAR_BILINEAR_RNN": [.1, 0., .1, .4, 0.],
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


def bayes_posterior_mean(y, q, condition):
    gain = context_gain(q, condition)
    log_odds = np.sum((2. * MU / (NOISE_SD ** 2)) * gain * y, axis=1)
    return np.tanh(.5 * log_odds).astype(np.float32)


def metrics(pred, target):
    p = np.clip((pred + 1.) * .5, 0., 1.)
    label = (target > 0).astype(np.float32)
    return ((pred >= 0) == (target > 0)).astype(np.int8), (pred - target) ** 2, (p - label) ** 2


def train_one(arm, y, q, target, batch_seed):
    model = Model(arm)
    opt = torch.optim.Adam(model.parameters(), lr=.02)
    rng = np.random.default_rng(batch_seed)
    ty, tq, ts = torch.from_numpy(y), torch.from_numpy(q), torch.from_numpy(target)
    start = time.perf_counter()
    losses = []
    for _ in range(UPDATES):
        idx = torch.from_numpy(rng.integers(0, len(target), size=BATCH))
        pred = model.rollout(ty[idx], tq[idx])
        loss = ((pred - ts[idx, None]) ** 2).mean()
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.)
        opt.step(); losses.append(float(loss.detach()))
    return model, time.perf_counter() - start, float(np.mean(losses[-10:])), losses[0]


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def effect(rows, arm_a, arm_b, metric, condition, size=None):
    # Metric contrast arm_a - arm_b, paired by task-seed cluster.
    seed_values = []
    for seed in SEEDS:
        sizes = (size,) if size is not None else SIZES
        size_diffs = []
        for ntrain in sizes:
            vals = {}
            for arm in (arm_a, arm_b):
                vals[arm] = np.mean([float(r[metric]) for r in rows if int(r["training_seed"]) == seed
                    and int(r["train_size"]) == ntrain and r["condition"] == condition and r["arm"] == arm])
            size_diffs.append(vals[arm_a] - vals[arm_b])
        seed_values.append(float(np.mean(size_diffs)))
    x = np.asarray(seed_values)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(x), size=(NBOOT, len(x)))
    ci = np.quantile(x[idx].mean(axis=1), [.025, .975])
    return {"mean_a_minus_b": float(x.mean()), "seed_bootstrap_ci95": [float(ci[0]), float(ci[1])],
            "positive_seed_count": int((x > 0).sum()), "per_seed": x.tolist()}


def means(rows):
    out = {}
    for n in SIZES:
        out[str(n)] = {}
        for c in CONDITIONS:
            out[str(n)][c] = {}
            for arm in ARMS:
                rr = [r for r in rows if int(r["train_size"]) == n and r["condition"] == c and r["arm"] == arm]
                out[str(n)][c][arm] = {m: float(np.mean([float(r[m]) for r in rr]))
                                       for m in ("correct", "terminal_mse", "brier")}
    return out


def preflight(out):
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()): raise FileExistsError(f"preflight requires empty output dir: {out}")
    checks = []
    y = torch.zeros((2, 4)); q = torch.tensor([[1., -1., 1., -1.], [-1., 1., -1., 1.]])
    for arm in LEARNED:
        m = Model(arm); pred = m.rollout(y, q)
        assert pred.shape == y.shape and torch.isfinite(pred).all()
        checks.append({"arm": arm, "parameter_count": sum(p.numel() for p in m.parameters()), "finite": True})
    payload = {"experiment_id": ID, "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_TASK_TRANSFER",
               "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
               "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
               "seeds": [SEEDS[0], SEEDS[-1]], "train_sizes": SIZES, "conditions": CONDITIONS,
               "arms": ARMS, "sequence_length": T, "test_episodes_per_seed_condition": NTEST,
               "updates": UPDATES, "batch_size": BATCH, "sample_tokens_per_fit": UPDATES * BATCH * T,
               "bootstrap_resamples": NBOOT, "bootstrap_seed": BOOT_SEED,
               "preflight_checks": checks, "outcomes_computed": False}
    (out / "PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    p = out / "PREFLIGHT.json"
    if not p.exists(): raise FileNotFoundError("run --preflight first")
    pre = json.loads(p.read_text())
    if pre["contract_sha256"] != sha(CONTRACT) or pre["runner_sha256"] != sha(Path(__file__)):
        raise RuntimeError("contract or runner changed after preflight")
    if any((out / f).exists() for f in ("episode_metrics.csv", "training_metrics.csv", "summary.json")):
        raise FileExistsError(f"refusing to overwrite outputs: {out}")
    torch.set_num_threads(1)
    train_rows, rows = [], []
    for si, seed in enumerate(SEEDS):
        train_s, train_q, train_noise = generate(seed * 41 + 39, max(SIZES))
        train_y = make_observation(train_s, train_q, train_noise, "ALIGNED")
        test_s, test_q, test_noise = generate(950000 + seed, NTEST)
        test_y = {c: make_observation(test_s, test_q, test_noise, c) for c in CONDITIONS}
        for ni, ntrain in enumerate(SIZES):
            for arm in LEARNED:
                model, sec, last_loss, first_loss = train_one(
                    arm, train_y[:ntrain], train_q[:ntrain], train_s[:ntrain], 11000000 + seed * 103 + ni * 13)
                train_rows.append({"training_seed": seed, "train_size": ntrain, "arm": arm,
                    "parameter_count": sum(p.numel() for p in model.parameters()), "optimizer_updates": UPDATES,
                    "batch_size": BATCH, "sample_tokens": UPDATES * BATCH * T, "training_seconds": sec,
                    "initial_batch_loss": first_loss, "final_10_update_loss": last_loss,
                    "parameters_json": json.dumps(model.raw.detach().numpy().tolist())})
                with torch.no_grad():
                    pred = model.rollout(torch.from_numpy(test_y["ALIGNED"]), torch.from_numpy(test_q)).numpy()[:, -1]
                    # Evaluate the same fitted model on all three mappings below; reuse q and target/noise draws.
                    for c in CONDITIONS:
                        pc = pred if c == "ALIGNED" else model.rollout(
                            torch.from_numpy(test_y[c]), torch.from_numpy(test_q)).numpy()[:, -1]
                        corr, mse, brier = metrics(pc, test_s)
                        for ep in range(NTEST):
                            rows.append({"training_seed": seed, "train_size": ntrain, "condition": c,
                                "episode_id": ep, "arm": arm, "correct": int(corr[ep]),
                                "terminal_mse": float(mse[ep]), "brier": float(brier[ep])})
            for c in CONDITIONS:
                bp = bayes_posterior_mean(test_y[c], test_q, c)
                corr, mse, brier = metrics(bp, test_s)
                for ep in range(NTEST):
                    rows.append({"training_seed": seed, "train_size": ntrain, "condition": c,
                        "episode_id": ep, "arm": "BAYES_ORACLE", "correct": int(corr[ep]),
                        "terminal_mse": float(mse[ep]), "brier": float(brier[ep])})
        print(f"completed sequential-decision seed {seed} ({si + 1}/{len(SEEDS)})", flush=True)
    write_csv(out / "episode_metrics.csv", rows); write_csv(out / "training_metrics.csv", train_rows)
    summary = {
        "primary_aligned_mode_minus_constant_accuracy": effect(rows, "MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "correct", "ALIGNED"),
        "aligned_mode_minus_bilinear_accuracy": effect(rows, "MODE_GAIN_FILTER", "LINEAR_BILINEAR_RNN", "correct", "ALIGNED"),
        "contrasts_by_condition_and_size": {c: {str(n): {
            "mode_minus_constant_accuracy": effect(rows, "MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "correct", c, n),
            "mode_minus_bilinear_accuracy": effect(rows, "MODE_GAIN_FILTER", "LINEAR_BILINEAR_RNN", "correct", c, n),
        } for n in SIZES} for c in CONDITIONS},
        "mean_metrics_by_size_condition_arm": means(rows),
        "training_time_seconds_by_arm": {a: float(np.mean([float(r["training_seconds"]) for r in train_rows if r["arm"] == a])) for a in LEARNED},
        "experiment_id": ID, "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_TASK_TRANSFER",
        "training_seeds": list(SEEDS), "train_sizes": list(SIZES), "conditions": list(CONDITIONS),
        "arms": list(ARMS), "primary_unit": "paired_training_seed", "test_episodes_per_seed_condition": NTEST,
        "sequence_length": T, "updates_per_fit": UPDATES, "batch_size": BATCH,
        "sample_tokens_per_fit": UPDATES * BATCH * T,
        "parameter_count": {a: sum(p.numel() for p in Model(a).parameters()) for a in LEARNED} | {"BAYES_ORACLE": 0},
        "bootstrap_resamples": NBOOT, "bootstrap_seed": BOOT_SEED}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    files = ("PREFLIGHT.json", "episode_metrics.csv", "training_metrics.csv", "summary.json")
    manifest = {"experiment_id": ID, "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
                "sha256": {name: sha(out / name) for name in files}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--preflight", action="store_true"); args = ap.parse_args(); out = args.output_dir.resolve()
    print(json.dumps(preflight(out) if args.preflight else run(out), indent=2))
