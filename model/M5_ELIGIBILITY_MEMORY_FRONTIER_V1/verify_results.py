#!/usr/bin/env python3
"""Check row integrity, memory accounting, update coverage, hashes, and primary contrast."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "results" / "M5_ELIGIBILITY_MEMORY_FRONTIER_V1" / "canonical"
FAMILIES = {"IID_GAUSSIAN", "AR1_GAUSSIAN", "SPARSE_SIGN"}
SEEDS = set(range(100, 130))
DELAYS = {1, 4, 16, 64}
ARMS = {"ELIGIBILITY_TRACE_64", "EXACT_FIFO_64", "EXACT_FIFO_256", "EXACT_FIFO_1024",
        "EXACT_FIFO_4096", "CURRENT_FEATURE_64", "EXACT_REPLAY_UNBOUNDED"}
CAP = {"EXACT_FIFO_64": 1, "EXACT_FIFO_256": 4, "EXACT_FIFO_1024": 16, "EXACT_FIFO_4096": 64}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    summary = json.loads((OUT / "summary.json").read_text())
    for name, expected in manifest["outputs_sha256"].items():
        assert sha(OUT / name) == expected, f"hash mismatch: {name}"
    metrics = read_csv(OUT / "task_metrics.csv")
    coverage = read_csv(OUT / "update_coverage.csv")
    paired = read_csv(OUT / "paired_contrasts.csv")
    expected_n = len(FAMILIES) * len(SEEDS) * len(DELAYS) * len(ARMS)
    assert len(metrics) == expected_n == manifest["row_counts"]["task_metrics"]
    assert len(coverage) == expected_n
    assert len(paired) == len(FAMILIES) * len(DELAYS) * (len(ARMS) - 1)

    by_key = {}
    for row in metrics:
        key = (row["generator"], int(row["seed"]), int(row["delay"]), row["arm"])
        assert key[0] in FAMILIES and key[1] in SEEDS and key[2] in DELAYS and key[3] in ARMS
        assert key not in by_key
        by_key[key] = row
        acc, loss = float(row["test_accuracy"]), float(row["test_cross_entropy"])
        assert math.isfinite(acc) and 0 <= acc <= 1 and math.isfinite(loss)
        expected_state = (64 if key[3] in {"ELIGIBILITY_TRACE_64", "CURRENT_FEATURE_64"}
                          else min(CAP[key[3]], key[2]) * 64 if key[3] in CAP
                          else key[2] * 64)
        assert int(row["active_feature_state_values"]) == expected_state, (key, row["active_feature_state_values"], expected_state)
    assert len(by_key) == expected_n

    cov_by_key = {}
    for row in coverage:
        key = (row["generator"], int(row["seed"]), int(row["delay"]), row["arm"])
        assert key not in cov_by_key
        cov_by_key[key] = row
        rate = float(row["update_coverage"])
        assert 0 <= rate <= 1 and int(row["label_updates_possible"]) == 3000
        if row["arm"] in CAP:
            expected_updates = 3000 if CAP[row["arm"]] >= key[2] else CAP[row["arm"]]
            expected = expected_updates / 3000
            assert abs(rate - expected) < 1e-12, (key, rate, expected)
        else:
            assert rate == 1.0
    assert len(cov_by_key) == expected_n

    # Independently recompute the equally weighted generator/task-seed primary mean.
    diffs = []
    for family in sorted(FAMILIES):
        for seed in sorted(SEEDS):
            cell = []
            for delay in sorted(DELAYS):
                trace = float(by_key[(family, seed, delay, "ELIGIBILITY_TRACE_64")]["test_accuracy"])
                fifo = float(by_key[(family, seed, delay, "EXACT_FIFO_64")]["test_accuracy"])
                cell.append(trace - fifo)
            diffs.append(sum(cell) / len(cell))
    recomputed = sum(diffs) / len(diffs)
    assert abs(recomputed - summary["primary_mean_difference"]) < 1e-12
    print(json.dumps({"status": "PASS", "task_metric_rows": len(metrics),
                      "coverage_rows": len(coverage), "paired_contrast_rows": len(paired),
                      "primary_mean_recomputed": recomputed}, indent=2))


if __name__ == "__main__":
    main()
