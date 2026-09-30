#!/usr/bin/env python3
"""Independently verify M2 full-trajectory replay rows and primary estimates."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/results/M2_STATE_TRAJECTORY_REPLAY_V1"
CONTRACT = ROOT / "summery/M2_STATE_TRAJECTORY_REPLAY_V1/CONTRACT.md"
SOURCE_MODEL = ROOT / "model/M2_STATE_TRAJECTORY_REPLAY_V1/source_model.py"
RUNNER = ROOT / "model/M2_STATE_TRAJECTORY_REPLAY_V1/run_experiment.py"
AUTHOR = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m"
V5_SUMMARY = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5/summary.json"
SCALES = (0.75, 1.00, 1.25)
SEEDS = range(380000, 380200)
BOOT_SEED = 20261007
N_BOOT = 20_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def bootstrap(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    means = values[idx].mean(axis=1)
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def main() -> None:
    manifest = json.loads((RESULTS / "run_manifest.json").read_text())
    summary = json.loads((RESULTS / "summary.json").read_text())
    heldout = rows(RESULTS / "heldout_metrics.csv")
    dev = rows(RESULTS / "development_modes_summary.csv")
    library = json.loads((RESULTS / "development_mode_trace_library.json").read_text())
    arms = {"SENSORY_SITE_FB", "MOTOR_MULTI_STAT_MATCHED", "FULL_TRAJECTORY_REPLAY", "NO_FEEDBACK"}
    expected = {(seed, scale, arm) for seed in SEEDS for scale in SCALES for arm in arms}
    keys = {(int(r["seed_block"]), float(r["noise_scale"]), r["arm"]) for r in heldout}
    assert len(heldout) == 2400 and keys == expected, "incomplete or duplicate held-out rows"
    assert len(dev) == 120 and "warm_direction_index" not in dev[0], "development table must be outcome-blind"
    assert set(library) == {str(s) for s in SCALES}
    for scale, traces in library.items():
        assert len(traces) == 2000, f"expected 2,000 development trajectories at {scale}"
        assert all(len(trace) == 188 and all(0 <= int(byte) <= 255 for byte in trace) for trace in traces)

    v5 = json.loads(V5_SUMMARY.read_text())
    expected_coeffs = {float(k): float(v["selected_motor_feedback"]) for k, v in v5["calibration"].items()}
    assert {float(k): float(v) for k,v in manifest["motor_coefficients_from_v5"].items()} == expected_coeffs
    assert manifest["inputs"]["contract_sha256"] == sha256(CONTRACT)
    assert manifest["inputs"]["source_model_sha256"] == sha256(SOURCE_MODEL)
    assert manifest["inputs"]["runner_sha256"] == sha256(RUNNER)
    assert manifest["inputs"]["author_matlab_sha256"] == sha256(AUTHOR)
    assert manifest["inputs"]["v5_summary_sha256"] == sha256(V5_SUMMARY)
    assert "lagi=max(1,(ti-delti))" in AUTHOR.read_text(errors="replace")
    assert "x_then = x_hist[max(0, t - delay_steps)]" in SOURCE_MODEL.read_text()
    for filename, digest in manifest["output_sha256"].items():
        assert sha256(RESULTS / filename) == digest, f"output hash mismatch: {filename}"

    # Recompute all yoke rows from the packed development library and recorded seed rule.
    source_spec = importlib.util.spec_from_file_location("replay_source_for_verification", SOURCE_MODEL)
    source = importlib.util.module_from_spec(source_spec); source_spec.loader.exec_module(source)
    runner_spec = importlib.util.spec_from_file_location("replay_runner_for_verification", RUNNER)
    runner = importlib.util.module_from_spec(runner_spec); runner_spec.loader.exec_module(runner)
    lookup = {(int(r["seed_block"]), float(r["noise_scale"]), r["arm"]): r for r in heldout}
    for seed in SEEDS:
        for scale in SCALES:
            recalculated = runner.replay(seed, scale, library[str(scale)], source)
            stored = lookup[(seed, scale, "FULL_TRAJECTORY_REPLAY")]
            for key, value in recalculated.items():
                if isinstance(value, (int, float)):
                    assert np.isclose(float(stored[key]), float(value), atol=1e-12), (seed, scale, key)

    replay_diffs, scalar_diffs = [], []
    for scale in SCALES:
        d_replay = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "FULL_TRAJECTORY_REPLAY")]["warm_direction_index"])
            for seed in SEEDS
        ])
        d_scalar = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "MOTOR_MULTI_STAT_MATCHED")]["warm_direction_index"])
            for seed in SEEDS
        ])
        replay_diffs.append(d_replay); scalar_diffs.append(d_scalar)
        persistence = {
            metric: float(np.mean([
                float(lookup[(seed, scale, "SENSORY_SITE_FB")][metric])
                - float(lookup[(seed, scale, "FULL_TRAJECTORY_REPLAY")][metric])
                for seed in SEEDS
            ]))
            for metric in ("mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s", "fraction_forward_runs_ge_30s",
                           "forward_occupancy", "mean_reverse_run_s", "median_reverse_run_s", "p90_reverse_run_s")
        }
        recorded = summary["heldout_by_noise_scale"][str(scale)]["sensory_minus_replay_persistence_summary_means"]
        assert all(np.isclose(persistence[k], recorded[k], atol=1e-12) for k in persistence)

    pooled = np.stack(replay_diffs, axis=1).mean(axis=1)
    scalar_pooled = np.stack(scalar_diffs, axis=1).mean(axis=1)
    assert np.isclose(summary["primary"]["mean"], pooled.mean(), atol=1e-12)
    assert np.allclose(summary["primary"]["ci95_seed_block_bootstrap"], bootstrap(pooled), atol=1e-12)
    assert summary["primary"]["positive_seed_blocks"] == int((pooled > 0).sum())
    assert np.isclose(summary["secondary_scalar_control"]["mean"], scalar_pooled.mean(), atol=1e-12)
    assert np.allclose(summary["secondary_scalar_control"]["ci95_seed_block_bootstrap"], bootstrap(scalar_pooled), atol=1e-12)

    verification = {
        "status": "PASS",
        "checks": ["complete_seed_scale_arm_rows", "outcome_blind_development_schema", "development_trace_library_cardinality_and_encoding", "V5_coefficient_provenance", "corrected_delay_index_source_mapping", "contract_source_runner_author_and_output_hashes", "all_600_replay_rows_regenerated", "heldout_persistence_differences_recomputed", "primary_and_scalar_bootstrap_recomputed"],
        "development_rows": len(dev), "heldout_rows": len(heldout),
        "development_traces_per_noise_scale": {scale: len(traces) for scale, traces in library.items()},
        "primary_mean_recomputed": float(pooled.mean()), "primary_ci95_recomputed": bootstrap(pooled),
        "positive_blocks_recomputed": int((pooled > 0).sum()),
        "heldout_metrics_sha256": sha256(RESULTS / "heldout_metrics.csv"),
    }
    (RESULTS / "POSTRUN_VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
