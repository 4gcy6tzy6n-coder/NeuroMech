#!/usr/bin/env python3
"""Independent grid, pairing, estimand, and artifact checks for M2 V3."""
import csv, hashlib, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/M2_LOW_DATA_GATING_V3"
SEEDS = tuple(range(72000, 72020))
SIZES = (16, 64, 256, 1024)
CONDITIONS = ("ALIGNED", "INDEPENDENT", "REVERSED")
ARMS = ("MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "LINEAR_BILINEAR_RNN", "KALMAN_ORACLE")
NTEST, NBOOT, BOOT_SEED = 256, 20000, 20261003


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def effect(values):
    vals = np.asarray(values, dtype=float)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(vals), size=(NBOOT, len(vals)))
    ci = np.quantile(vals[idx].mean(axis=1), [.025, .975])
    return float(vals.mean()), [float(ci[0]), float(ci[1])], int((vals > 0).sum())


def independently_recompute_oracle(seed, condition):
    """Regenerate one test set and recompute its Kalman posterior independently."""
    rng = np.random.default_rng(930000 + seed)
    n, steps = NTEST, 160
    phi = rng.uniform(.84, .96, n).astype(np.float32)
    sd_proc = rng.uniform(.08, .18, n).astype(np.float32)
    sd_obs = rng.uniform(.15, .35, n).astype(np.float32)
    x = np.zeros((n, steps), np.float32)
    q = np.empty((n, steps), np.float32)
    q[:, 0] = rng.choice(np.array([-1, 1], np.int8), n)
    eps = rng.standard_normal((n, steps)).astype(np.float32)
    eta = rng.standard_normal((n, steps)).astype(np.float32)
    flips = rng.random((n, steps)) < .05
    for t in range(1, steps):
        x[:, t] = phi * x[:, t - 1] + sd_proc * eps[:, t]
        q[:, t] = np.where(flips[:, t], -q[:, t - 1], q[:, t - 1])
    if condition == "ALIGNED":
        hcoef = (q > 0).astype(np.float32)
    elif condition == "INDEPENDENT":
        hcoef = np.full(q.shape, .5, np.float32)
    else:
        hcoef = (q < 0).astype(np.float32)
    y = hcoef * x + sd_obs[:, None] * eta
    mean = np.zeros(n, np.float64); var = np.zeros(n, np.float64)
    pred = np.zeros((n, steps), np.float32)
    for t in range(steps):
        if t:
            mean = phi * mean
            var = phi * phi * var + sd_proc * sd_proc
        ht = hcoef[:, t]
        gain = var * ht / (ht * ht * var + sd_obs * sd_obs)
        mean = mean + gain * (y[:, t] - ht * mean)
        var = (1. - gain * ht) * var
        pred[:, t] = mean
    return np.mean((pred - x) ** 2, axis=1)


def main():
    ep = read_csv(OUT / "episode_metrics.csv")
    fit = read_csv(OUT / "training_metrics.csv")
    assert len(ep) == len(SEEDS) * len(SIZES) * len(CONDITIONS) * len(ARMS) * NTEST
    assert len(fit) == len(SEEDS) * len(SIZES) * 3
    vals = {}
    for r in ep:
        assert np.isfinite(float(r["episode_mse"]))
        key = (int(r["training_seed"]), int(r["train_size"]), r["condition"], int(r["episode_id"]), r["arm"])
        assert key not in vals
        vals[key] = float(r["episode_mse"])
    for s in SEEDS:
        for n in SIZES:
            for c in CONDITIONS:
                for i in range(NTEST):
                    for a in ARMS:
                        assert (s, n, c, i, a) in vals
    # Recompute the analytical reference from independently regenerated streams.
    for s in SEEDS:
        for c in CONDITIONS:
            oracle = independently_recompute_oracle(s, c)
            for n in SIZES:
                saved = np.array([vals[(s, n, c, i, "KALMAN_ORACLE")] for i in range(NTEST)])
                assert np.allclose(saved, oracle, rtol=1e-6, atol=1e-8), (s, n, c)
    expected_params = {"MODE_GAIN_FILTER": 4, "CONSTANT_GAIN_FILTER": 3, "LINEAR_BILINEAR_RNN": 5}
    for r in fit:
        assert int(r["parameter_count"]) == expected_params[r["arm"]]
        assert int(r["sample_tokens"]) == 16 * 250 * 160
        assert np.isfinite(float(r["training_seconds"]))

    primary_by_seed, ablation_by_seed = [], []
    for s in SEEDS:
        pds, ads = [], []
        for n in SIZES:
            for target, a, b in ((pds, "MODE_GAIN_FILTER", "LINEAR_BILINEAR_RNN"),
                                 (ads, "MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER")):
                ma = np.mean([vals[(s, n, "ALIGNED", i, a)] for i in range(NTEST)])
                mb = np.mean([vals[(s, n, "ALIGNED", i, b)] for i in range(NTEST)])
                target.append(float(mb - ma))
        primary_by_seed.append(float(np.mean(pds)))
        ablation_by_seed.append(float(np.mean(ads)))
    pmean, pci, ppos = effect(primary_by_seed)
    amean, aci, apos = effect(ablation_by_seed)
    summary = json.loads((OUT / "summary.json").read_text())
    p = summary["primary_aligned_bilinear_minus_mode_equal_train_size_mean"]
    a = summary["context_ablation_aligned_constant_minus_mode_equal_train_size_mean"]
    assert abs(pmean - p["mean_b_minus_a_mse"]) < 1e-10 and np.allclose(pci, p["seed_bootstrap_ci95"], atol=1e-10)
    assert ppos == p["positive_seed_count"]
    assert abs(amean - a["mean_b_minus_a_mse"]) < 1e-10 and np.allclose(aci, a["seed_bootstrap_ci95"], atol=1e-10)
    assert apos == a["positive_seed_count"]
    manifest = json.loads((OUT / "manifest.json").read_text())
    assert manifest["runner_sha256"] == sha(ROOT / "model/M2_LOW_DATA_GATING_V3/run_experiment.py")
    assert manifest["contract_sha256"] == sha(ROOT / "summery/M2_LOW_DATA_GATING_V3/CONTRACT.md")
    for name, digest in manifest["sha256"].items():
        assert sha(OUT / name) == digest, name
    report = {"status": "PASS", "episode_rows": len(ep), "training_fit_rows": len(fit),
              "paired_seed_units": len(SEEDS), "primary_mean": pmean, "primary_ci95": pci,
              "primary_positive_seeds": ppos, "context_ablation_mean": amean,
              "context_ablation_ci95": aci, "artifact_hashes": "PASS"}
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
