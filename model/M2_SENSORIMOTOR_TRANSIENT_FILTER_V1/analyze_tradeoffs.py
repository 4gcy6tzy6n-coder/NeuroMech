#!/usr/bin/env python3
"""Post-result paired seed-block contrasts for M2 feedback-placement tradeoffs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_SENSORIMOTOR_TRANSIENT_FILTER_V1"
INPUT = ROOT / "data/results" / NAME / "canonical/seed_summary.csv"
DEFAULT_OUT = ROOT / "data/results" / NAME / "POSTRUN_TRADEOFF_CONTRASTS.csv"
CONDITIONS = ("CLEAN_STABLE", "TRANSIENT_PULSE", "LONG_PULSE", "SUSTAINED_SWITCH", "COMBINED_STRESS")
METRICS = ("movement_mae", "movement_mse", "command_energy", "mean_switch_latency_steps", "pulse_window_mae")
ARMS = ("SENSORY_SITE_1D", "OUTPUT_SITE_1D")
N_BLOCKS = 20
BOOTSTRAPS = 50_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    with INPUT.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    index = {(int(r["seed_block"]), r["arm"], r["condition"]): r for r in rows}
    if len(index) != len(rows) or len(rows) != N_BLOCKS * 7 * len(CONDITIONS):
        raise ValueError("unexpected seed summary keys or row count")

    out_rows = []
    summary = {}
    for ci, condition in enumerate(CONDITIONS):
        summary[condition] = {}
        for mi, metric in enumerate(METRICS):
            values = []
            for block in range(N_BLOCKS):
                sensory = index[(block, "SENSORY_SITE_1D", condition)][metric]
                output = index[(block, "OUTPUT_SITE_1D", condition)][metric]
                if sensory in ("", "nan", "None") or output in ("", "nan", "None"):
                    continue
                values.append(float(output) - float(sensory))
            if not values:
                summary[condition][metric] = None
                continue
            v = np.asarray(values, dtype=np.float64)
            rng = np.random.default_rng(7_310_001 + ci * 100 + mi)
            boot = v[rng.integers(0, len(v), size=(BOOTSTRAPS, len(v)))].mean(axis=1)
            record = {
                "condition": condition,
                "metric": metric,
                "contrast": "OUTPUT_SITE_1D minus SENSORY_SITE_1D",
                "mean_difference": float(v.mean()),
                "median_difference": float(np.median(v)),
                "ci95_low": float(np.quantile(boot, 0.025)),
                "ci95_high": float(np.quantile(boot, 0.975)),
                "n_seed_blocks": int(len(v)),
                "positive_seed_blocks": int((v > 0).sum()),
                "negative_seed_blocks": int((v < 0).sum()),
            }
            out_rows.append(record)
            summary[condition][metric] = record

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(out_rows)
    manifest = {
        "experiment": NAME,
        "classification": "post-result exploratory secondary analysis; no multiplicity correction; does not alter frozen primary result",
        "contrast": "OUTPUT_SITE_1D minus SENSORY_SITE_1D, paired within seed block and condition",
        "conditions": CONDITIONS,
        "metrics": METRICS,
        "bootstrap_replicates": BOOTSTRAPS,
        "bootstrap_unit": "paired training/task seed block",
        "input": {"path": str(INPUT.relative_to(ROOT)), "sha256": sha256(INPUT), "bytes": INPUT.stat().st_size},
        "output": {"path": str(args.output.relative_to(ROOT)), "sha256": sha256(args.output), "bytes": args.output.stat().st_size},
        "analysis_script": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha256(Path(__file__))},
        "verification_script": {
            "path": str((ROOT / "model" / NAME / "verify_tradeoffs.py").relative_to(ROOT)),
            "sha256": sha256(ROOT / "model" / NAME / "verify_tradeoffs.py"),
        },
        "contrasts": summary,
        "limitations": [
            "Conditions and metrics beyond the original transient-pulse primary are exploratory.",
            "Intervals are descriptive across multiple contrasts; no multiplicity adjustment was applied.",
            "The synthetic task does not validate or refute the biological RIM-AIY finding.",
        ],
    }
    manifest_path = args.output.with_name("POSTRUN_TRADEOFF_ANALYSIS.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"status": "COMPLETE", "contrasts": len(out_rows), "manifest": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
