#!/usr/bin/env python3
"""Independently validate key coverage, hashes, and primary paired contrast."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from analyze_results import summarize

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = ROOT / "data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/canonical"
ARMS = {"SENSORY_SITE_FB", "OUTPUT_SITE_FB", "NO_FEEDBACK"}
INTERVALS = {0.0, 40.0, 20.0, 10.0, 5.0}


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
    result_dir = args.results_dir.expanduser().resolve()
    with (result_dir / "seed_block_metrics.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    keys = [(int(r["seed_block"]), float(r["reversal_interval_s"]), r["arm"]) for r in rows]
    seed_blocks = sorted({key[0] for key in keys})
    expected = {(seed, interval, arm) for seed in range(seed_blocks[0], seed_blocks[-1] + 1)
                for interval in INTERVALS for arm in ARMS}
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise SystemExit("FAIL: duplicate, missing, or unexpected seed/interval/arm keys")
    for row in rows:
        for metric in ("aligned_progress_rate", "forward_occupancy", "mean_forward_run_s", "p90_forward_run_s"):
            value = float(row[metric])
            if not math.isfinite(value):
                raise SystemExit(f"FAIL: non-finite {metric}")

    manifest_path = result_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if len(rows) != manifest["rows"] or len(seed_blocks) != 100:
        raise SystemExit("FAIL: row count or seed-block count does not match run manifest")
    for relative, digest in manifest["input_sha256"].items():
        path = ROOT / relative
        if not path.exists() or sha256(path) != digest:
            raise SystemExit(f"FAIL: source hash mismatch: {relative}")
    for name, digest in manifest["output_sha256"].items():
        path = result_dir / name
        if not path.exists() or sha256(path) != digest:
            raise SystemExit(f"FAIL: output hash mismatch: {name}")

    calculated = summarize(rows)
    stored = json.loads((result_dir / "summary.json").read_text())
    expected_primary = calculated["primary_contrast"]
    actual_primary = stored["primary_contrast"]
    if expected_primary != actual_primary:
        raise SystemExit("FAIL: primary paired-bootstrap contrast does not reproduce")
    if stored["rows"] != len(rows) or stored["seed_block_count"] != len(seed_blocks):
        raise SystemExit("FAIL: summary count fields do not match CSV")

    print(json.dumps({
        "status": "PASS",
        "unique_seed_interval_arm_keys": len(keys),
        "seed_blocks": len(seed_blocks),
        "primary_interval_recomputed": True,
        "input_and_csv_hashes": "PASS",
    }, indent=2))


if __name__ == "__main__":
    main()
