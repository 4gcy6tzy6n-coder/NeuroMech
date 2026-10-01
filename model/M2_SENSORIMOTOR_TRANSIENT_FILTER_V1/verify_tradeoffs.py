#!/usr/bin/env python3
"""Independently recompute and verify the post-run M2 trade-off contrasts."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_SENSORIMOTOR_TRANSIENT_FILTER_V1"
INPUT = ROOT / "data/results" / NAME / "canonical/seed_summary.csv"
OUTPUT = ROOT / "data/results" / NAME / "POSTRUN_TRADEOFF_CONTRASTS.csv"
ANALYSIS = ROOT / "data/results" / NAME / "POSTRUN_TRADEOFF_ANALYSIS.json"
RESULT = ROOT / "data/results" / NAME / "POSTRUN_TRADEOFF_VERIFICATION.json"
CONDITIONS = ("CLEAN_STABLE", "TRANSIENT_PULSE", "LONG_PULSE", "SUSTAINED_SWITCH", "COMBINED_STRESS")
METRICS = ("movement_mae", "movement_mse", "command_energy", "mean_switch_latency_steps", "pulse_window_mae")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0, abs_tol=1e-12)


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8") as f:
        source = list(csv.DictReader(f))
    with OUTPUT.open(newline="", encoding="utf-8") as f:
        published = list(csv.DictReader(f))
    by_key = {(int(r["seed_block"]), r["arm"], r["condition"]): r for r in source}
    output_map = {(r["condition"], r["metric"]): r for r in published}
    assert len(source) == 700 and len(by_key) == 700
    assert len(published) == 24 and len(output_map) == 24
    checked = 0
    for ci, condition in enumerate(CONDITIONS):
        for mi, metric in enumerate(METRICS):
            values = []
            for block in range(20):
                a = by_key[(block, "SENSORY_SITE_1D", condition)][metric]
                b = by_key[(block, "OUTPUT_SITE_1D", condition)][metric]
                if a in ("", "nan", "None") or b in ("", "nan", "None"):
                    continue
                values.append(float(b) - float(a))
            actual = output_map.get((condition, metric))
            if not values:
                assert actual is None
                continue
            assert actual is not None
            v = np.asarray(values, dtype=np.float64)
            rng = np.random.default_rng(7_310_001 + ci * 100 + mi)
            boot = v[rng.integers(0, len(v), size=(50_000, len(v)))].mean(axis=1)
            expected = {
                "mean_difference": float(v.mean()),
                "median_difference": float(np.median(v)),
                "ci95_low": float(np.quantile(boot, 0.025)),
                "ci95_high": float(np.quantile(boot, 0.975)),
                "n_seed_blocks": len(v),
                "positive_seed_blocks": int((v > 0).sum()),
                "negative_seed_blocks": int((v < 0).sum()),
            }
            for key, value in expected.items():
                assert close(float(actual[key]), float(value)) if isinstance(value, float) else int(actual[key]) == value
            checked += 1

    analysis = json.loads(ANALYSIS.read_text())
    assert analysis["input"]["sha256"] == sha256(INPUT)
    assert analysis["output"]["sha256"] == sha256(OUTPUT)
    result = {
        "status": "PASS",
        "input_seed_summary_rows": len(source),
        "paired_contrasts_recomputed": checked,
        "published_contrast_rows": len(published),
        "checks": "means, medians, seed-block bootstrap intervals, sign counts, and source/output hashes",
        "scope": "post-result exploratory secondary analysis only; no multiplicity adjustment",
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
