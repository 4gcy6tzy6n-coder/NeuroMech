#!/usr/bin/env python3
"""Independent integrity and primary-estimand recomputation for M2 V4."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V4"
DEV = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3/development_calibration.csv"
METRICS = ("mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s", "fraction_forward_runs_ge_30s")
SCALES = (0.75, 1.00, 1.25)
SEEDS = range(320000, 320200)
BOOT_SEED = 20261004
N_BOOT = 20_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def expected_calibration(dev: list[dict[str, str]]) -> dict[float, float]:
    chosen = {}
    for scale in SCALES:
        cell = [r for r in dev if float(r["noise_scale"]) == scale]
        target_rows = [r for r in cell if r["arm"] == "SENSORY_SITE_FB"]
        target = {m: np.mean([float(r[m]) for r in target_rows]) for m in METRICS}
        candidates = sorted({float(r["motor_only_feedback"]) for r in cell if r["arm"].startswith("MOTOR_ONLY_")})
        means = {c: {m: np.mean([float(r[m]) for r in cell if r["arm"] == f"MOTOR_ONLY_{c:.3f}"]) for m in METRICS} for c in candidates}
        sd = {m: np.std([means[c][m] for c in candidates], ddof=0) for m in METRICS}
        score = {c: sum(((means[c][m] - target[m]) / sd[m]) ** 2 if sd[m] else 0.0 for m in METRICS) for c in candidates}
        chosen[scale] = min(candidates, key=lambda c: (score[c], c))
    return chosen


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    results = parser.parse_args().results_dir.expanduser().resolve()
    metrics_path = results / "heldout_simulation_metrics.csv"
    summary_path = results / "summary.json"
    manifest_path = results / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    summary = json.loads(summary_path.read_text())
    heldout = rows(metrics_path)
    dev = rows(DEV)
    expected = expected_calibration(dev)
    actual = {float(k): float(v) for k, v in manifest["selected_motor_feedback"].items()}

    assert len(heldout) == 1800, f"expected 1800 rows, found {len(heldout)}"
    keys = {(int(r["seed_block"]), float(r["noise_scale"]), r["arm"]) for r in heldout}
    expected_keys = {(seed, scale, arm) for seed in SEEDS for scale in SCALES for arm in ("SENSORY_SITE_FB", "MOTOR_MULTI_STAT_MATCHED", "NO_FEEDBACK")}
    assert keys == expected_keys, "held-out key set mismatch or duplicate key"
    assert actual == expected, f"calibration mismatch: {actual} != {expected}"
    assert manifest["rows"] == len(heldout)
    contract_path = ROOT / "summery/M2_FEEDBACK_SITE_SPECIFICITY_V4/CONTRACT.md"
    assert manifest["inputs"]["contract_sha256"] == sha256(contract_path), "current contract hash mismatch"
    assert manifest["output_sha256"][metrics_path.name] == sha256(metrics_path)
    assert manifest["output_sha256"][summary_path.name] == sha256(summary_path)

    lookup = {(int(r["seed_block"]), float(r["noise_scale"]), r["arm"]): r for r in heldout}
    scale_diffs = []
    for scale in SCALES:
        d = np.array([float(lookup[(s, scale, "SENSORY_SITE_FB")]["warm_direction_index"]) -
                      float(lookup[(s, scale, "MOTOR_MULTI_STAT_MATCHED")]["warm_direction_index"]) for s in SEEDS])
        scale_diffs.append(d)
    pooled = np.stack(scale_diffs, axis=1).mean(axis=1)
    rng = np.random.default_rng(BOOT_SEED)
    indexes = rng.integers(0, len(pooled), size=(N_BOOT, len(pooled)))
    ci = np.quantile(pooled[indexes].mean(axis=1), [.025, .975]).tolist()
    assert np.isclose(float(summary["primary"]["mean"]), pooled.mean(), atol=1e-12)
    assert np.allclose(summary["primary"]["ci95_seed_block_bootstrap"], ci, atol=1e-12)
    assert summary["primary"]["positive_seed_blocks"] == int((pooled > 0).sum())
    verification = {
        "status": "PASS",
        "checks": ["row_count", "unique_complete_seed_scale_arm_keys", "development_only_calibration_recomputed", "contract_hash_and_recorded_preformat_hash", "output_hashes", "primary_estimand_and_bootstrap_recomputed"],
        "heldout_rows": len(heldout),
        "selected_motor_feedback": {str(k): v for k, v in expected.items()},
        "primary_mean_recomputed": float(pooled.mean()),
        "primary_ci95_recomputed": [float(x) for x in ci],
        "positive_seed_blocks_recomputed": int((pooled > 0).sum()),
        "metrics_sha256": sha256(metrics_path),
    }
    (results / "POSTRUN_VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
