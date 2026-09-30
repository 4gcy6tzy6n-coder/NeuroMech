#!/usr/bin/env python3
"""Independent grid, oracle, paired-estimand and hash audit."""
import csv, hashlib, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/M2_SEQUENTIAL_DECISION_V1"
SEEDS = tuple(range(73000, 73020)); SIZES = (16, 64, 256, 1024)
CONDITIONS = ("ALIGNED", "INDEPENDENT", "REVERSED")
ARMS = ("MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "LINEAR_BILINEAR_RNN", "BAYES_ORACLE")
LEARNED = {"MODE_GAIN_FILTER": 4, "CONSTANT_GAIN_FILTER": 3, "LINEAR_BILINEAR_RNN": 5}
T, NTEST, NBOOT, BOOT_SEED = 32, 512, 20000, 20261004
MU, NOISE_SD, QSWITCH = .18, .7, .25


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="") as f: return list(csv.DictReader(f))


def independently_generate(seed):
    rng = np.random.default_rng(seed)
    target = rng.choice(np.array([-1., 1.], np.float32), NTEST)
    q = np.empty((NTEST, T), np.float32)
    q[:, 0] = rng.choice(np.array([-1., 1.], np.float32), NTEST)
    flips = rng.random((NTEST, T)) < QSWITCH
    noise = rng.standard_normal((NTEST, T)).astype(np.float32)
    for t in range(1, T): q[:, t] = np.where(flips[:, t], -q[:, t - 1], q[:, t - 1])
    return target, q, noise


def oracle_metrics(seed, condition):
    target, q, noise = independently_generate(950000 + seed)
    h = ((q > 0) if condition == "ALIGNED" else (q < 0) if condition == "REVERSED" else np.full(q.shape, .5)).astype(np.float32)
    y = h * (MU * target[:, None]) + NOISE_SD * noise
    logodds = np.sum((2. * MU / (NOISE_SD ** 2)) * h * y, axis=1)
    posterior = np.tanh(.5 * logodds)
    prob = np.clip((posterior + 1.) * .5, 0., 1.)
    label = (target > 0).astype(np.float32)
    correct = ((posterior >= 0) == (target > 0)).astype(np.int8)
    return correct, (posterior - target) ** 2, (prob - label) ** 2


def paired_seed_effect(rows, metric, a, b, condition):
    values = []
    for seed in SEEDS:
        bysize = []
        for size in SIZES:
            arows = [float(r[metric]) for r in rows if int(r["training_seed"]) == seed and int(r["train_size"]) == size and r["condition"] == condition and r["arm"] == a]
            brows = [float(r[metric]) for r in rows if int(r["training_seed"]) == seed and int(r["train_size"]) == size and r["condition"] == condition and r["arm"] == b]
            assert len(arows) == NTEST and len(brows) == NTEST
            bysize.append(float(np.mean(arows) - np.mean(brows)))
        values.append(float(np.mean(bysize)))
    v = np.asarray(values)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(v), size=(NBOOT, len(v)))
    ci = np.quantile(v[idx].mean(axis=1), [.025, .975])
    return float(v.mean()), [float(ci[0]), float(ci[1])], int((v > 0).sum())


def main():
    rows = read_csv(OUT / "episode_metrics.csv"); fits = read_csv(OUT / "training_metrics.csv")
    assert len(rows) == len(SEEDS) * len(SIZES) * len(CONDITIONS) * len(ARMS) * NTEST
    assert len(fits) == len(SEEDS) * len(SIZES) * len(LEARNED)
    values = {}
    for r in rows:
        assert int(r["correct"]) in (0, 1)
        assert all(np.isfinite(float(r[k])) for k in ("terminal_mse", "brier"))
        assert 0 <= float(r["brier"]) <= 1
        key = (int(r["training_seed"]), int(r["train_size"]), r["condition"], int(r["episode_id"]), r["arm"])
        assert key not in values
        values[key] = r
    for seed in SEEDS:
        for size in SIZES:
            for condition in CONDITIONS:
                for ep in range(NTEST):
                    for arm in ARMS: assert (seed, size, condition, ep, arm) in values
    for row in fits:
        assert int(row["parameter_count"]) == LEARNED[row["arm"]]
        assert int(row["sample_tokens"]) == 250 * 16 * T
        assert np.isfinite(float(row["training_seconds"]))
    # Regenerate held-out target/context/noise streams and independently recompute the Bayes reference.
    for seed in SEEDS:
        for condition in CONDITIONS:
            expected = oracle_metrics(seed, condition)
            for size in SIZES:
                for ep in range(NTEST):
                    actual = values[(seed, size, condition, ep, "BAYES_ORACLE")]
                    assert int(actual["correct"]) == int(expected[0][ep])
                    assert np.isclose(float(actual["terminal_mse"]), expected[1][ep], atol=1e-7)
                    assert np.isclose(float(actual["brier"]), expected[2][ep], atol=1e-7)
    mean, ci, pos = paired_seed_effect(rows, "correct", "MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "ALIGNED")
    summary = json.loads((OUT / "summary.json").read_text())
    p = summary["primary_aligned_mode_minus_constant_accuracy"]
    assert abs(mean - p["mean_a_minus_b"]) < 1e-12 and np.allclose(ci, p["seed_bootstrap_ci95"], atol=1e-12)
    assert pos == p["positive_seed_count"]
    m = json.loads((OUT / "manifest.json").read_text())
    assert m["runner_sha256"] == sha(ROOT / "model/M2_SEQUENTIAL_DECISION_V1/run_experiment.py")
    assert m["contract_sha256"] == sha(ROOT / "summery/M2_SEQUENTIAL_DECISION_V1/CONTRACT.md")
    for name, digest in m["sha256"].items(): assert sha(OUT / name) == digest
    report = {"status": "PASS", "episode_rows": len(rows), "fit_rows": len(fits),
              "paired_seed_units": len(SEEDS), "primary_accuracy_difference": mean,
              "primary_ci95": ci, "positive_seeds": pos, "oracle_regeneration": "PASS",
              "artifact_hashes": "PASS"}
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
