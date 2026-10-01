#!/usr/bin/env python3
"""Independent structural and summary verifier for the trace-horizon sweep."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M5_DELAYED_REWARD_TRACE_HORIZON_V1"
OUT = ROOT / "data/results" / NAME
MASTER_SEED = 20260930
SEEDS = tuple(range(61, 91))
DELAYS = (1, 4, 16, 64)
GAMMAS = (0.50, 0.75, 0.90, 0.98)
N_BOOT = 20_000
ARMS = tuple(f"TRACE_GAMMA_{g:.2f}" for g in GAMMAS) + ("EXACT_REPLAY", "NO_TRACE_CURRENT_32")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return math.isclose(a, b, rel_tol=0, abs_tol=tol)


def paired_ci(values: np.ndarray, rng: np.random.Generator, familywise: bool) -> tuple[float, float]:
    boot = values[rng.integers(0, len(values), size=(N_BOOT, len(values)))].mean(axis=1)
    alpha = 0.05 / 16 if familywise else 0.05
    return float(np.quantile(boot, alpha / 2)), float(np.quantile(boot, 1 - alpha / 2))


def main() -> None:
    preflight = json.loads((OUT / "PREFLIGHT.json").read_text())
    manifest = json.loads((OUT / "manifest.json").read_text())
    assert manifest["experiment"] == NAME
    assert manifest["contract_sha256"] == preflight["contract_sha256"]
    assert manifest["runner_sha256"] == preflight["runner_sha256"]
    assert sha256(ROOT / "summery" / NAME / "CONTRACT.md") == preflight["contract_sha256"]
    assert sha256(ROOT / "model" / NAME / "run_experiment.py") == preflight["runner_sha256"]
    for filename, item in manifest["outputs"].items():
        path = OUT / filename
        assert path.is_file() and path.stat().st_size == item["bytes"]
        assert sha256(path) == item["sha256"]

    with (OUT / "seed_metrics.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(SEEDS) * len(DELAYS) * len(ARMS)
    keys = [(int(r["seed"]), int(r["delay"]), r["arm"]) for r in rows]
    expected = {(s, d, a) for s in SEEDS for d in DELAYS for a in ARMS}
    assert len(set(keys)) == len(keys) and set(keys) == expected
    lookup = {key: float(row["heldout_expected_reward"]) for key, row in zip(keys, rows)}
    assert all(math.isfinite(v) and 0 <= v <= 1 for v in lookup.values())

    with (OUT / "paired_contrasts.csv").open(newline="", encoding="utf-8") as f:
        contrast_rows = list(csv.DictReader(f))
    assert len(contrast_rows) == 32
    rng = np.random.default_rng(MASTER_SEED + 20261001)
    expected_contrasts = []
    for delay in DELAYS:
        for arm in ARMS:
            if not arm.startswith("TRACE_"):
                continue
            for control in ("NO_TRACE_CURRENT_32", "EXACT_REPLAY"):
                effects = np.array([lookup[(seed, delay, arm)] - lookup[(seed, delay, control)] for seed in SEEDS])
                primary = control == "NO_TRACE_CURRENT_32"
                lo, hi = paired_ci(effects, rng, primary)
                expected_contrasts.append((delay, arm, control, float(effects.mean()), lo, hi, int(np.sum(effects > 0))))
    actual = {(int(r["delay"]), r["trace_arm"], r["control"]): r for r in contrast_rows}
    for delay, arm, control, mean, lo, hi, npos in expected_contrasts:
        row = actual[(delay, arm, control)]
        assert close(float(row["mean_difference"]), mean)
        assert close(float(row["ci95_low"]), lo) and close(float(row["ci95_high"]), hi)
        assert int(row["seed_positive"]) == npos and int(row["n_seeds"]) == len(SEEDS)

    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["n_seeds"] == len(SEEDS) and summary["seed_range"] == [SEEDS[0], SEEDS[-1]]
    assert summary["contrast_cells"] == len(contrast_rows)
    for arm in ARMS:
        mean = float(np.mean([lookup[(s, d, arm)] for s in SEEDS for d in DELAYS]))
        assert close(summary["arm_mean_across_delay_cells"][arm], mean)

    verification = {"status": "PASS", "seed_metric_rows": len(rows), "unique_seed_delay_arm_keys": len(set(keys)),
                    "contrast_rows_recomputed": len(contrast_rows), "output_files_hash_checked": len(manifest["outputs"]),
                    "task_seeds": len(SEEDS), "primary_familywise_cells": 16,
                    "scope": "artifact/summary verification; does not independently rerun model training"}
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VERIFICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
