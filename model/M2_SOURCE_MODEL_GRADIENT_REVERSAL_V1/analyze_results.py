#!/usr/bin/env python3
"""Summarize paired seed-block results for gradient-reversal stress tests."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

DEFAULT_RESULTS = Path(__file__).resolve().parents[2] / "data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/canonical"
ARMS = ("SENSORY_SITE_FB", "OUTPUT_SITE_FB", "NO_FEEDBACK")
INTERVALS = (0.0, 40.0, 20.0, 10.0, 5.0)
PRIMARY_INTERVAL = 20.0
METRICS = (
    "aligned_progress_rate",
    "forward_occupancy",
    "mean_forward_run_s",
    "p90_forward_run_s",
    "mean_switch_recovery_lag_s",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def paired_summary(rows: list[dict[str, str]], interval: float, arm_a: str, arm_b: str,
                   metric: str, rng: np.random.Generator, n_boot: int = 20000) -> dict[str, object]:
    selected = [r for r in rows if float(r["reversal_interval_s"]) == interval]
    a = {int(r["seed_block"]): float(r[metric]) for r in selected if r["arm"] == arm_a}
    b = {int(r["seed_block"]): float(r[metric]) for r in selected if r["arm"] == arm_b}
    seeds = sorted(set(a) & set(b))
    diffs = np.asarray([a[s] - b[s] for s in seeds], dtype=np.float64)
    diffs = diffs[np.isfinite(diffs)]
    if not diffs.size:
        return {"n_seed_blocks": 0, "mean_difference": None, "ci95": [None, None], "positive_seed_blocks": 0}
    draws = rng.integers(0, diffs.size, size=(n_boot, diffs.size))
    means = diffs[draws].mean(axis=1)
    return {
        "n_seed_blocks": int(diffs.size),
        "mean_difference": float(diffs.mean()),
        "ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))],
        "positive_seed_blocks": int((diffs > 0).sum()),
        "negative_seed_blocks": int((diffs < 0).sum()),
    }


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    seed_ids = sorted({int(r["seed_block"]) for r in rows})
    rng = np.random.default_rng(20261013)
    means: dict[str, object] = {}
    contrasts: dict[str, object] = {}
    for interval in INTERVALS:
        per_arm = {}
        for arm in ARMS:
            arm_rows = [r for r in rows if float(r["reversal_interval_s"]) == interval and r["arm"] == arm]
            per_arm[arm] = {
                metric: (float(np.mean([float(r[metric]) for r in arm_rows]))
                         if np.isfinite(np.mean([float(r[metric]) for r in arm_rows])) else None)
                for metric in METRICS
            }
        means[str(interval)] = per_arm
        contrasts[str(interval)] = {
            "sensory_minus_output_progress": paired_summary(
                rows, interval, "SENSORY_SITE_FB", "OUTPUT_SITE_FB", "aligned_progress_rate", rng),
            "sensory_minus_no_feedback_progress": paired_summary(
                rows, interval, "SENSORY_SITE_FB", "NO_FEEDBACK", "aligned_progress_rate", rng),
            "output_minus_no_feedback_progress": paired_summary(
                rows, interval, "OUTPUT_SITE_FB", "NO_FEEDBACK", "aligned_progress_rate", rng),
        }
    return {
        "experiment_id": "M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1",
        "classification": "exploratory_source_derived_computational_stress_test",
        "primary_endpoint": "aligned_progress_rate",
        "primary_interval_s": PRIMARY_INTERVAL,
        "primary_contrast": contrasts[str(PRIMARY_INTERVAL)]["sensory_minus_output_progress"],
        "seed_block_count": len(seed_ids),
        "rows": len(rows),
        "means_by_interval_and_arm": means,
        "progress_contrasts_by_interval": contrasts,
        "bootstrap": {"unit": "paired simulation seed block", "resamples": 20000, "seed": 20261013},
        "interpretation": "Model simulation only; the output-site control is not calibrated to match run persistence. No biological inference or AI-transfer claim is made.",
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    rows = read_rows(args.results_dir / "seed_block_metrics.csv")
    summary = summarize(rows)
    summary_path = args.results_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    manifest_path = args.results_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"][summary_path.name] = sha256(summary_path)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary["primary_contrast"], indent=2))
    for interval in INTERVALS:
        print(f"interval={interval:g}s means={summary['means_by_interval_and_arm'][str(interval)]}")


if __name__ == "__main__":
    main()
