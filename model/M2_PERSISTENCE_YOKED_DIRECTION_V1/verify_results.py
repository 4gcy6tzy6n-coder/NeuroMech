#!/usr/bin/env python3
"""Independently verify M2 marginal-persistence yoke outputs and contrasts."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/results/M2_PERSISTENCE_YOKED_DIRECTION_V1"
CONTRACT = ROOT / "summery/M2_PERSISTENCE_YOKED_DIRECTION_V1/CONTRACT.md"
SOURCE_MODEL = ROOT / "model/M2_PERSISTENCE_YOKED_DIRECTION_V1/source_model.py"
RUNNER = ROOT / "model/M2_PERSISTENCE_YOKED_DIRECTION_V1/run_experiment.py"
AUTHOR = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m"
V5_SUMMARY = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5/summary.json"
SCALES = (0.75, 1.00, 1.25)
SEEDS = range(360000, 360200)
BOOT_SEED = 20261006
N_BOOT = 20_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def bootstrap(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOT_SEED)
    ix = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    means = values[ix].mean(axis=1)
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def main() -> None:
    manifest = json.loads((RESULTS / "run_manifest.json").read_text())
    summary = json.loads((RESULTS / "summary.json").read_text())
    heldout = read_csv(RESULTS / "heldout_metrics.csv")
    dev = read_csv(RESULTS / "development_summary.csv")
    libraries = json.loads((RESULTS / "development_bout_library.json").read_text())

    expected_arms = {"SENSORY_SITE_FB", "MOTOR_MULTI_STAT_MATCHED", "MARGINAL_PERSISTENCE_YOKE", "NO_FEEDBACK"}
    keys = {(int(r["seed_block"]), float(r["noise_scale"]), r["arm"]) for r in heldout}
    expected_keys = {(seed, scale, arm) for seed in SEEDS for scale in SCALES for arm in expected_arms}
    assert len(heldout) == 2400 and keys == expected_keys, "held-out seed × scale × arm set mismatch"
    assert len(dev) == 120, "expected 40 development blocks × 3 scales"
    assert "warm_direction_index" not in dev[0], "development table should not expose direction outcome"
    assert set(libraries) == {str(s) for s in SCALES}
    for value in libraries.values():
        assert value["forward"] and value["reverse"]
        assert all(isinstance(n, int) and n > 0 for k in ("forward", "reverse") for n in value[k])

    v5 = json.loads(V5_SUMMARY.read_text())
    expected_coeffs = {float(scale): float(value["selected_motor_feedback"]) for scale, value in v5["calibration"].items()}
    recorded_coeffs = {float(k): float(v) for k, v in manifest["motor_only_coefficients_from_v5"].items()}
    assert recorded_coeffs == expected_coeffs
    assert manifest["inputs"]["contract_sha256"] == sha256(CONTRACT)
    assert manifest["inputs"]["source_model_sha256"] == sha256(SOURCE_MODEL)
    assert manifest["inputs"]["runner_sha256"] == sha256(RUNNER)
    assert manifest["inputs"]["author_matlab_sha256"] == sha256(AUTHOR)
    assert manifest["inputs"]["v5_summary_sha256"] == sha256(V5_SUMMARY)
    author_text = AUTHOR.read_text(errors="replace")
    source_text = SOURCE_MODEL.read_text()
    assert "lagi=max(1,(ti-delti))" in author_text
    assert "x_then = x_hist[max(0, t - delay_steps)]" in source_text
    for filename, digest in manifest["output_sha256"].items():
        assert sha256(RESULTS / filename) == digest, f"output hash mismatch: {filename}"

    lookup = {(int(r["seed_block"]), float(r["noise_scale"]), r["arm"]): r for r in heldout}
    yoke_diffs, scalar_diffs = [], []
    for scale in SCALES:
        dy = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "MARGINAL_PERSISTENCE_YOKE")]["warm_direction_index"])
            for seed in SEEDS
        ])
        ds = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "MOTOR_MULTI_STAT_MATCHED")]["warm_direction_index"])
            for seed in SEEDS
        ])
        yoke_diffs.append(dy)
        scalar_diffs.append(ds)
        yoke_persistence = {
            metric: float(np.mean([
                float(lookup[(seed, scale, "SENSORY_SITE_FB")][metric])
                - float(lookup[(seed, scale, "MARGINAL_PERSISTENCE_YOKE")][metric])
                for seed in SEEDS
            ]))
            for metric in ("mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s", "fraction_forward_runs_ge_30s", "forward_occupancy")
        }
        expected_persistence = summary["heldout_by_noise_scale"][str(scale)]["sensory_minus_yoke_persistence_summary_means"]
        assert all(np.isclose(yoke_persistence[k], expected_persistence[k], atol=1e-12) for k in yoke_persistence)

    pooled_yoke = np.stack(yoke_diffs, axis=1).mean(axis=1)
    pooled_scalar = np.stack(scalar_diffs, axis=1).mean(axis=1)
    assert np.isclose(summary["primary"]["mean"], pooled_yoke.mean(), atol=1e-12)
    assert np.allclose(summary["primary"]["ci95_seed_block_bootstrap"], bootstrap(pooled_yoke), atol=1e-12)
    assert summary["primary"]["positive_seed_blocks"] == int((pooled_yoke > 0).sum())
    assert np.isclose(summary["secondary_scalar_control"]["mean"], pooled_scalar.mean(), atol=1e-12)
    assert np.allclose(summary["secondary_scalar_control"]["ci95_seed_block_bootstrap"], bootstrap(pooled_scalar), atol=1e-12)

    verification = {
        "status": "PASS",
        "checks": ["complete_seed_scale_arm_rows", "development_outcome_blind_columns", "positive_development_bout_libraries", "V5_coefficient_provenance", "corrected_author_delay_index", "contract_source_runner_author_source_and_output_hashes", "heldout_persistence_contrasts_recomputed", "primary_and_scalar_bootstrap_recomputed"],
        "development_rows": len(dev), "heldout_rows": len(heldout),
        "development_bout_counts": {scale: {k: len(v[k]) for k in ("forward", "reverse")} for scale, v in libraries.items()},
        "primary_mean_recomputed": float(pooled_yoke.mean()),
        "primary_ci95_recomputed": bootstrap(pooled_yoke),
        "primary_positive_blocks_recomputed": int((pooled_yoke > 0).sum()),
        "heldout_metrics_sha256": sha256(RESULTS / "heldout_metrics.csv"),
    }
    (RESULTS / "POSTRUN_VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
