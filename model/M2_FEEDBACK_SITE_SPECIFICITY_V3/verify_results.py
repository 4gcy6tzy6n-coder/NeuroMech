#!/usr/bin/env python3
"""Independently recompute M2 V3 primary contrasts and provenance checks."""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3"
CONTRACT = ROOT / "summery/M2_FEEDBACK_SITE_SPECIFICITY_V3/CONTRACT.md"
RUNNER_DIR = Path(__file__).parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=OUT)
    OUT = parser.parse_args().results_dir.expanduser().resolve()
    summary = json.loads((OUT / "summary.json").read_text())
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    runner = RUNNER_DIR / manifest.get("runner_file", "run_experiment.py")
    with (OUT / "heldout_simulation_metrics.csv").open() as stream:
        rows = list(csv.DictReader(stream))

    keys = [(int(r["seed_block"]), float(r["noise_scale"]), r["arm"]) for r in rows]
    if len(rows) != 1800 or len(set(keys)) != 1800:
        raise ValueError("held-out result rows or seed×scale×arm keys are incomplete")
    if len({r[0] for r in keys}) != 200:
        raise ValueError("expected exactly 200 held-out seed blocks")

    lookup = {(int(r["seed_block"]), float(r["noise_scale"]), r["arm"]): r for r in rows}
    scales = (0.75, 1.00, 1.25)
    seeds = range(311000, 311200)
    differences = []
    per_scale = {}
    for scale in scales:
        contrast = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "MOTOR_ONLY_MATCHED")]["warm_direction_index"])
            for seed in seeds
        ])
        differences.append(contrast)
        reported = summary["heldout_by_noise_scale"][str(scale)]["sensory_site_minus_motor_only_direction_index"]
        if abs(float(contrast.mean()) - reported["mean"]) > 1e-12:
            raise ValueError(f"reported mean does not reproduce at noise scale {scale}")
        positives = int((contrast > 0).sum())
        if positives != reported["positive_seed_blocks"]:
            raise ValueError(f"positive seed count does not reproduce at noise scale {scale}")
        per_scale[str(scale)] = {"mean": float(contrast.mean()), "positive_seed_blocks": positives}

    pooled = np.stack(differences, axis=1).mean(axis=1)
    rng = np.random.default_rng(20261003)
    sample_indices = rng.integers(0, pooled.size, size=(20_000, pooled.size))
    interval = np.quantile(pooled[sample_indices].mean(axis=1), [0.025, 0.975]).tolist()
    if abs(float(pooled.mean()) - summary["primary"]["mean"]) > 1e-12:
        raise ValueError("primary mean does not reproduce")
    if np.max(np.abs(np.asarray(interval) - np.asarray(summary["primary"]["ci95"]))) > 1e-12:
        raise ValueError("primary bootstrap interval does not reproduce")

    for name, expected in manifest["output_sha256"].items():
        if sha256(OUT / name) != expected:
            raise ValueError(f"manifest output hash mismatch: {name}")
    if sha256(CONTRACT) != manifest["contract_sha256"]:
        raise ValueError("contract hash mismatch")
    if not runner.is_file() or sha256(runner) != manifest["runner_sha256"]:
        raise ValueError("runner hash mismatch")

    verification = {
        "status": "PASS",
        "rows": len(rows),
        "unique_seed_scale_arm_keys": len(set(keys)),
        "primary_mean": float(pooled.mean()),
        "primary_ci95": interval,
        "per_scale": per_scale,
        "contract_hash_matches": True,
        "runner_hash_matches": True,
        "verified_runner_file": runner.name,
        "manifest_output_hashes_match": True,
    }
    path = OUT / "POSTRUN_VERIFICATION.json"
    path.write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
