#!/usr/bin/env python3
"""Verify archived self-versus-yoked results, keys, yoke checks, and hashes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = ROOT / "data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical"
SEEDS = tuple(range(20261016, 20261116))
INTERVALS = (0.0, 40.0, 20.0, 10.0, 5.0)
ARMS = ("SELF_CONTINGENT", "CROSS_AGENT_YOKED", "NO_FEEDBACK")
BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 20261015


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    out = args.results_dir.expanduser().resolve()
    rows_path = out / "seed_block_metrics.csv"
    with rows_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected = {(seed, interval, arm) for seed in SEEDS for interval in INTERVALS for arm in ARMS}
    observed = {(int(row["seed_block"]), float(row["reversal_interval_s"]), row["arm"]) for row in rows}
    if len(rows) != len(expected) or observed != expected:
        raise SystemExit(f"FAIL: row-key mismatch; expected {len(expected)} observed {len(rows)}")
    numeric = ("aligned_progress_rate", "forward_occupancy", "mean_forward_run_s", "p90_forward_run_s")
    if not all(np.isfinite(float(row[key])) for row in rows for key in numeric):
        raise SystemExit("FAIL: non-finite metric found")

    check_path = out / "feedback_distribution_check.json"
    checks = json.loads(check_path.read_text())["checks"]
    expected_checks = {(seed, interval) for seed in SEEDS for interval in INTERVALS}
    observed_checks = {(int(check["seed_block"]), float(check["reversal_interval_s"])) for check in checks}
    if observed_checks != expected_checks or len(checks) != len(expected_checks):
        raise SystemExit("FAIL: feedback-check key mismatch")
    if not all(check["donor_mapping_is_derangement"] for check in checks):
        raise SystemExit("FAIL: at least one donor mapping includes self")
    if not all(check["instantaneous_population_feedback_distribution_exact"] and
               check["max_sorted_feedback_value_difference"] == 0.0 for check in checks):
        raise SystemExit("FAIL: instantaneous feedback marginal was not exactly preserved")

    by_arm = {}
    for row in rows:
        if float(row["reversal_interval_s"]) == 20.0:
            by_arm.setdefault(row["arm"], {})[int(row["seed_block"])] = float(row["aligned_progress_rate"])
    diffs = np.asarray([by_arm["SELF_CONTINGENT"][seed] - by_arm["CROSS_AGENT_YOKED"][seed]
                        for seed in SEEDS])
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, diffs.size, size=(BOOTSTRAPS, diffs.size))
    boot = diffs[indices].mean(axis=1)
    summary = json.loads((out / "summary.json").read_text())
    primary = summary["primary_contrast"]
    actual_ci = [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]
    if not np.isclose(primary["mean"], diffs.mean(), rtol=0, atol=1e-15):
        raise SystemExit("FAIL: primary contrast mean differs from raw rows")
    if not np.allclose(primary["ci95_seed_block_bootstrap"], actual_ci, rtol=0, atol=1e-15):
        raise SystemExit("FAIL: primary bootstrap interval differs from raw rows")
    if primary["positive_seed_blocks"] != int((diffs > 0).sum()):
        raise SystemExit("FAIL: primary positive-block count differs from raw rows")

    manifest_path = out / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    inputs = {
        "summery/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/CONTRACT.md": ROOT / "summery/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/CONTRACT.md",
        "model/M2_FEEDBACK_SITE_SPECIFICITY_V5/source_model.py": ROOT / "model/M2_FEEDBACK_SITE_SPECIFICITY_V5/source_model.py",
        "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m": ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m",
        "model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/run_experiment.py": ROOT / "model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/run_experiment.py",
        "model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/analyze_results.py": ROOT / "model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/analyze_results.py",
        "model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/verify_results.py": ROOT / "model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/verify_results.py",
    }
    for rel, path in inputs.items():
        if manifest["input_sha256"].get(rel) != sha256(path):
            raise SystemExit(f"FAIL: input hash mismatch: {rel}")
    for name, expected_hash in manifest["output_sha256"].items():
        if sha256(out / name) != expected_hash:
            raise SystemExit(f"FAIL: output hash mismatch: {name}")
    print(json.dumps({"status": "PASS", "rows": len(rows), "feedback_checks": len(checks),
                      "primary_mean": float(diffs.mean()), "primary_ci95": actual_ci,
                      "positive_seed_blocks": int((diffs > 0).sum())}, indent=2))


if __name__ == "__main__":
    main()
