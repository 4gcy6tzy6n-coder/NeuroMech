#!/usr/bin/env python3
"""Independent structural and estimand checks for M2_LOW_DATA_GATING_V1."""
import csv, hashlib, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/M2_LOW_DATA_GATING_V2"
SEEDS = tuple(range(71000, 71020))
SIZES = (16, 64, 256, 1024)
CONDITIONS = ("ALIGNED", "INDEPENDENT", "REVERSED")
ARMS = ("MODE_GAIN_FILTER", "GENERIC_BILINEAR_RNN_1D")
NTEST, NBOOT, BOOT_SEED = 256, 20000, 20261002


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main():
    episodes = read_csv(OUT / "episode_metrics.csv")
    train = read_csv(OUT / "training_metrics.csv")
    expected_episode_rows = len(SEEDS) * len(SIZES) * len(CONDITIONS) * len(ARMS) * NTEST
    expected_train_rows = len(SEEDS) * len(SIZES) * len(ARMS)
    assert len(episodes) == expected_episode_rows, (len(episodes), expected_episode_rows)
    assert len(train) == expected_train_rows, (len(train), expected_train_rows)
    assert all(np.isfinite(float(r["episode_mse"])) for r in episodes)
    assert all(int(r["parameter_count"]) == 4 and int(r["sample_tokens"]) == 16 * 250 * 160 for r in train)
    # Each model pair must use the same held-out episode IDs and complete metric grid.
    grid = set()
    values = {}
    for r in episodes:
        key = (int(r["training_seed"]), int(r["train_size"]), r["condition"], int(r["episode_id"]), r["arm"])
        assert key not in grid
        grid.add(key)
        values[key] = float(r["episode_mse"])
    for s in SEEDS:
        for n in SIZES:
            for c in CONDITIONS:
                for ep in range(NTEST):
                    assert (s, n, c, ep, ARMS[0]) in values and (s, n, c, ep, ARMS[1]) in values
    contrasts = {}
    for s in SEEDS:
        ds = []
        for n in SIZES:
            arr = []
            for ep in range(NTEST):
                arr.append(values[(s, n, "ALIGNED", ep, ARMS[1])] - values[(s, n, "ALIGNED", ep, ARMS[0])])
            ds.append(float(np.mean(arr)))
        contrasts[s] = float(np.mean(ds))
    primary = np.array([contrasts[s] for s in SEEDS])
    rng = np.random.default_rng(BOOT_SEED)
    indices = rng.integers(0, len(primary), size=(NBOOT, len(primary)))
    ci = np.quantile(primary[indices].mean(axis=1), [.025, .975]).tolist()
    summary = json.loads((OUT / "summary.json").read_text())
    expected = summary["primary_aligned_equal_train_size_mean_generic_minus_mode_mse"]
    assert abs(primary.mean() - expected["mean"]) < 1e-10
    assert np.allclose(ci, expected["seed_bootstrap_ci95"], atol=1e-10)
    assert int((primary > 0).sum()) == expected["positive_seed_count"]
    manifest = json.loads((OUT / "manifest.json").read_text())
    for name, digest in manifest["sha256"].items():
        assert sha(OUT / name) == digest, name
    report = {"status": "PASS", "episode_rows": len(episodes), "training_fit_rows": len(train),
              "paired_seed_units": len(SEEDS), "primary_mean": float(primary.mean()),
              "primary_seed_bootstrap_ci95": [float(ci[0]), float(ci[1])],
              "positive_seed_count": int((primary > 0).sum()), "artifact_hashes": "PASS"}
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
