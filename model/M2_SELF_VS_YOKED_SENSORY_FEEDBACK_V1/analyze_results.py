#!/usr/bin/env python3
"""Summarize paired self-contingent versus yoked source-model results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = ROOT / "data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical"
ARMS = ("SELF_CONTINGENT", "CROSS_AGENT_YOKED", "NO_FEEDBACK")
INTERVALS = (0.0, 40.0, 20.0, 10.0, 5.0)
PRIMARY_INTERVAL = 20.0
BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 20261015


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def paired_values(rows: list[dict[str, str]], interval: float, metric: str,
                  arm_a: str, arm_b: str) -> np.ndarray:
    selected = [row for row in rows if float(row["reversal_interval_s"]) == interval]
    a = {int(row["seed_block"]): float(row[metric]) for row in selected if row["arm"] == arm_a}
    b = {int(row["seed_block"]): float(row[metric]) for row in selected if row["arm"] == arm_b}
    seeds = sorted(set(a) & set(b))
    return np.asarray([a[seed] - b[seed] for seed in seeds], dtype=np.float64)


def bootstrap(values: np.ndarray, rng: np.random.Generator) -> list[float]:
    indices = rng.integers(0, values.size, size=(BOOTSTRAPS, values.size))
    means = values[indices].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    seed_ids = sorted({int(row["seed_block"]) for row in rows})
    by_interval: dict[str, object] = {}
    for interval in INTERVALS:
        selected = [row for row in rows if float(row["reversal_interval_s"]) == interval]
        arm_means = {}
        for arm in ARMS:
            arm_rows = [row for row in selected if row["arm"] == arm]
            arm_means[arm] = {
                metric: float(np.mean([float(row[metric]) for row in arm_rows]))
                for metric in ("aligned_progress_rate", "forward_occupancy", "mean_forward_run_s", "p90_forward_run_s")
            }
        differences = {}
        for comparator in ("CROSS_AGENT_YOKED", "NO_FEEDBACK"):
            delta = paired_values(rows, interval, "aligned_progress_rate", "SELF_CONTINGENT", comparator)
            rng = np.random.default_rng(
                BOOTSTRAP_SEED if interval == PRIMARY_INTERVAL and comparator == "CROSS_AGENT_YOKED"
                else BOOTSTRAP_SEED + int(interval * 100) + (0 if comparator == "CROSS_AGENT_YOKED" else 1)
            )
            differences[f"self_minus_{comparator.lower()}_progress"] = {
                "mean": float(delta.mean()),
                "ci95_seed_block_bootstrap": bootstrap(delta, rng),
                "positive_seed_blocks": int((delta > 0).sum()),
                "negative_seed_blocks": int((delta < 0).sum()),
                "n_seed_blocks": int(delta.size),
            }
        by_interval[str(interval)] = {"arm_means": arm_means, "contrasts": differences}
    primary = by_interval[str(PRIMARY_INTERVAL)]["contrasts"]["self_minus_cross_agent_yoked_progress"]
    return {
        "experiment_id": "M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1",
        "classification": "retrospective_exploratory_source_model_mechanism_probe",
        "primary_endpoint": "environment-aligned displacement rate (model-distance units/s)",
        "primary_interval_s": PRIMARY_INTERVAL,
        "primary_contrast": primary,
        "seed_block_count": len(seed_ids),
        "rows": len(rows),
        "means_and_contrasts_by_interval": by_interval,
        "bootstrap": {"unit": "paired simulation seed block", "resamples": BOOTSTRAPS, "seed": BOOTSTRAP_SEED},
        "interpretation": (
            "Simulation-only comparison. The yoke reassigns paired self-arm feedback traces across agents, "
            "preserving the instantaneous population distribution but breaking recipient-specific contingency. "
            "No biological validation or AI-transfer claim is made."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    out = args.results_dir.expanduser().resolve()
    rows = read_rows(out / "seed_block_metrics.csv")
    summary_path = out / "summary.json"
    summary_path.write_text(json.dumps(summarize(rows), indent=2) + "\n")
    manifest_path = out / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"][summary_path.name] = sha256(summary_path)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(json.loads(summary_path.read_text())["primary_contrast"], indent=2))


if __name__ == "__main__":
    main()
