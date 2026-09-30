#!/usr/bin/env python3
"""Independently audit task rows, memory accounting, and paired primary result."""
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/canonical"
RHOS, DELAYS, HORIZONS = (0.0, 0.5, 0.9), (4, 16, 64), (1, 2, 4, 8, 16, 32, 64)
SEEDS = range(30, 60)
ARMS = {*(f"HORIZON_{h}" for h in HORIZONS), "ELIGIBILITY_TRACE", "EXACT_REPLAY"}
N_BOOT, BOOT_SEED, N_FEATURES = 20_000, 20261008, 64


def ci(values, salt=0):
    rng = np.random.default_rng(BOOT_SEED + salt)
    values = np.asarray(values)
    draws = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    means = values[draws].mean(axis=1)
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def main():
    with (OUT / "task_metrics.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2430
    lookup = {}
    for row in rows:
        key = (float(row["rho"]), int(row["seed"]), int(row["delay"]), row["arm"])
        assert key not in lookup
        lookup[key] = row
        accuracy = float(row["accuracy"])
        assert np.isfinite(accuracy) and 0 <= accuracy <= 1
        delay, arm = key[2], key[3]
        if arm == "ELIGIBILITY_TRACE":
            expected_memory = N_FEATURES
        elif arm == "EXACT_REPLAY":
            expected_memory = delay * N_FEATURES
        elif arm == "HORIZON_1":
            expected_memory = 0
        else:
            expected_memory = int(arm.split("_")[1]) * N_FEATURES
        assert int(row["active_history_float_values"]) == expected_memory
    assert len(lookup) == len(rows)
    assert all(ARMS <= {a for r, s, d, a in lookup if r == rho and s == seed and d == delay}
               for rho in RHOS for seed in SEEDS for delay in DELAYS)

    score = {key: float(row["accuracy"]) for key, row in lookup.items()}
    per_seed = np.asarray([
        np.mean([
            score[(rho, seed, delay, "ELIGIBILITY_TRACE")] - score[(rho, seed, delay, "HORIZON_1")]
            for rho in RHOS for delay in DELAYS
        ]) for seed in SEEDS
    ])
    summary = json.loads((OUT / "summary.json").read_text())
    primary = summary["primary"]
    assert abs(float(per_seed.mean()) - primary["mean"]) < 1e-12
    assert ci(per_seed) == primary["task_seed_bootstrap_95ci"]
    assert int((per_seed > 0).sum()) == primary["positive_seed_count"]
    assert primary["n_task_seeds"] == 30 and primary["seeds"] == [30, 59]
    receipt = {
        "status": "PASS",
        "rows": len(rows), "unique_condition_keys": len(lookup),
        "fresh_task_seed_range": [30, 59], "all_scores_finite_and_bounded": True,
        "memory_accounting_matches_contract": True,
        "primary_mean_trace_minus_horizon1": float(per_seed.mean()),
        "primary_task_seed_bootstrap_95ci": ci(per_seed),
        "positive_seed_count": int((per_seed > 0).sum()),
    }
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
