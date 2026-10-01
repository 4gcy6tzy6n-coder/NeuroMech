#!/usr/bin/env python3
"""Independent integrity, memory-accounting, and estimand checks."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "results" / "M5_DELAYED_REWARD_MEMORY_FRONTIER_V1" / "canonical"
SEEDS = set(range(30, 60))
DELAYS = {1, 4, 16, 64}
CAPACITY = {"EXACT_FIFO_32": 1, "EXACT_FIFO_128": 4,
            "EXACT_FIFO_512": 16, "EXACT_FIFO_2048": 64}
ARMS = {"ELIGIBILITY_TRACE_32", *CAPACITY, "NO_TRACE_CURRENT_32", "EXACT_REPLAY"}
N_TRAIN = 6000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name: str):
    with (OUT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def boot(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(20260930 + 992)
    idx = rng.integers(0, len(values), size=(20_000, len(values)))
    return [float(x) for x in np.quantile(values[idx].mean(axis=1), [0.025, 0.975])]


def main() -> None:
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    summary = json.loads((OUT / "summary.json").read_text())
    for name, expected in manifest["outputs_sha256"].items():
        assert sha(OUT / name) == expected, f"output hash mismatch: {name}"

    metrics = rows("task_metrics.csv")
    coverage = rows("update_coverage.csv")
    trajectory = rows("training_reward_trajectory.csv")
    contrasts = rows("primary_contrasts.csv")
    per_seed = rows("per_seed_primary.csv")
    expected_n = len(SEEDS) * len(DELAYS) * len(ARMS)
    assert len(metrics) == expected_n == 840
    assert len(coverage) == expected_n
    assert len(trajectory) == len(SEEDS) * len(DELAYS) * len(ARMS) * 12
    assert len(contrasts) == len(ARMS) - 1
    assert len(per_seed) == len(SEEDS)

    m = {}
    for r in metrics:
        key = (int(r["seed"]), int(r["delay"]), r["arm"])
        assert key[0] in SEEDS and key[1] in DELAYS and key[2] in ARMS and key not in m
        y = float(r["heldout_expected_reward"])
        assert math.isfinite(y) and 0 <= y <= 1
        if key[2] in {"ELIGIBILITY_TRACE_32", "EXACT_FIFO_32", "NO_TRACE_CURRENT_32"}:
            expected_state = 32
        elif key[2] in CAPACITY:
            expected_state = min(CAPACITY[key[2]], key[1]) * 32
        else:
            expected_state = key[1] * 32
        assert int(r["active_credit_state_values"]) == expected_state
        m[key] = r

    c = {}
    for r in coverage:
        key = (int(r["seed"]), int(r["delay"]), r["arm"])
        assert key not in c
        n = int(r["updates_applied"])
        assert 0 <= n <= N_TRAIN and int(r["updates_possible"]) == N_TRAIN
        if key[2] in CAPACITY:
            expected = N_TRAIN if CAPACITY[key[2]] >= key[1] else CAPACITY[key[2]]
        elif key[2] == "NO_TRACE_CURRENT_32":
            # Current-score updates are unavailable during the D-step flush.
            expected = N_TRAIN - key[1]
        else:
            expected = N_TRAIN
        assert n == expected, (key, n, expected)
        assert abs(float(r["update_coverage"]) - expected / N_TRAIN) < 1e-12
        c[key] = r

    # If the FIFO can preserve every pending score, it must exactly reproduce replay.
    for seed in SEEDS:
        for delay in DELAYS:
            replay = float(m[(seed, delay, "EXACT_REPLAY")]["heldout_expected_reward"])
            for arm, capacity in CAPACITY.items():
                if capacity >= delay:
                    value = float(m[(seed, delay, arm)]["heldout_expected_reward"])
                    assert value == replay, (seed, delay, arm, value, replay)

    effects = np.array([
        np.mean([float(m[(seed, d, "ELIGIBILITY_TRACE_32")]["heldout_expected_reward"])
                 - float(m[(seed, d, "EXACT_FIFO_32")]["heldout_expected_reward"])
                 for d in sorted(DELAYS)])
        for seed in sorted(SEEDS)
    ])
    mean = float(effects.mean())
    interval = boot(effects)
    assert abs(mean - summary["primary_mean_difference"]) < 1e-12
    assert interval == summary["primary_paired_seed_bootstrap_95ci"]
    assert int(np.sum(effects > 0)) == summary["positive_task_seeds"]
    assert [float(x["trace_minus_fifo32_mean_over_delays"]) for x in per_seed] == [float(v) for v in effects]
    print(json.dumps({"status": "PASS", "task_metric_rows": len(metrics),
                      "update_coverage_rows": len(coverage), "trajectory_rows": len(trajectory),
                      "primary_mean_recomputed": mean, "primary_ci_recomputed": interval,
                      "capacity_sufficient_fifo_matches_replay": True}, indent=2))


if __name__ == "__main__":
    main()
