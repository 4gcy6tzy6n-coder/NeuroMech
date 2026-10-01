#!/usr/bin/env python3
"""Independent structure, paired-contrast, yoke, and artifact verification."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ID = "M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1"
DEFAULT = ROOT / "data/results" / ID / "canonical"
CONTRACT = ROOT / "summery" / ID / "CONTRACT.md"
RUNNER = ROOT / "model" / ID / "run_experiment.py"
BASE_RUNNER = ROOT / "model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/run_experiment.py"
SEEDS = tuple(range(420000, 420032))
HAZARDS = (1 / 240, 1 / 120, 1 / 40)
MISSING = (0.25, 0.50, 0.75)
TRAIN_HAZARD, TRAIN_MISSING = 1 / 120, 0.50
NTEST, STEPS, BOOTSTRAPS, BOOT_SEED = 256, 240, 10_000, 20261029
ARMS = {"SENSORY_SELF", "SENSORY_CROSS_AGENT_YOKE", "OUTPUT_SITE_PERSISTENCE",
        "NO_FEEDBACK", "GENERIC_RNN_1H", "ORACLE_RELATIVE_ERROR"}
LEARNED = {"SENSORY_SELF", "OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "GENERIC_RNN_1H"}
CONTRAST_ARMS = ("OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "GENERIC_RNN_1H", "ORACLE_RELATIVE_ERROR")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def crossed_bootstrap(matrix: np.ndarray, rng: np.random.Generator) -> dict:
    draws = np.empty(BOOTSTRAPS, dtype=np.float64)
    for start in range(0, BOOTSTRAPS, 200):
        count = min(200, BOOTSTRAPS - start)
        seeds = rng.integers(0, matrix.shape[0], size=(count, matrix.shape[0]))
        episodes = rng.integers(0, matrix.shape[1], size=(count, matrix.shape[1]))
        draws[start:start + count] = matrix[seeds[:, :, None], episodes[:, None, :]].mean(axis=(1, 2))
    return {
        "mean": float(matrix.mean()),
        "ci95": [float(x) for x in np.quantile(draws, [0.025, 0.975])],
        "positive_seed_blocks": int(np.sum(matrix.mean(axis=1) > 0)),
        "n_seed_blocks": int(matrix.shape[0]),
        "n_episodes_per_seed": int(matrix.shape[1]),
    }


def assert_summary(got: dict, expected: dict) -> None:
    for key in ("mean",):
        if not np.isclose(got[key], expected[key], atol=1e-12, rtol=0):
            raise ValueError(f"summary {key} mismatch: {got[key]} vs {expected[key]}")
    if not np.allclose(got["ci95"], expected["ci95"], atol=1e-12, rtol=0):
        raise ValueError("bootstrap interval mismatch")
    for key in ("positive_seed_blocks", "n_seed_blocks", "n_episodes_per_seed"):
        if got[key] != expected[key]:
            raise ValueError(f"summary {key} mismatch")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=DEFAULT)
    args = parser.parse_args()
    out = args.results_dir.resolve()
    preflight = json.loads((out / "PREFLIGHT.json").read_text())
    manifest = json.loads((out / "RUN_MANIFEST.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    if preflight["outcomes_computed"] is not False:
        raise ValueError("preflight incorrectly claims to be outcome blind")
    expected_hashes = {"contract_sha256": sha(CONTRACT), "runner_sha256": sha(RUNNER),
                       "base_runner_sha256": sha(BASE_RUNNER)}
    for key, value in expected_hashes.items():
        if preflight[key] != value:
            raise ValueError(f"preflight source hash mismatch: {key}")
    for key, value in expected_hashes.items():
        manifest_key = key.replace("contract_", "contract_").replace("runner_", "runner_")
        if manifest[manifest_key] != value:
            raise ValueError(f"run manifest source hash mismatch: {manifest_key}")
    for name, record in manifest["files"].items():
        path = out / name
        if path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
            raise ValueError(f"artifact hash/size mismatch: {name}")

    episode_rows = read_csv(out / "episode_results.csv")
    fits = read_csv(out / "training_results.csv")
    audits = read_csv(out / "yoke_signal_audit.csv")
    expected_rows = len(SEEDS) * len(HAZARDS) * len(MISSING) * NTEST * len(ARMS)
    if len(episode_rows) != expected_rows:
        raise ValueError(f"episode row count mismatch: {len(episode_rows)} != {expected_rows}")
    if len(fits) != len(SEEDS) * len(LEARNED):
        raise ValueError("training-fit row count mismatch")
    if len(audits) != len(SEEDS) * len(HAZARDS) * len(MISSING):
        raise ValueError("yoke audit row count mismatch")

    lookup: dict[tuple, float] = {}
    for row in episode_rows:
        key = (int(row["training_seed"]), float(row["hazard"]), float(row["missing_rate"]),
               int(row["episode_id"]), row["arm"])
        if key[0] not in SEEDS or key[1] not in HAZARDS or key[2] not in MISSING or not 0 <= key[3] < NTEST or key[4] not in ARMS:
            raise ValueError(f"out-of-grid result row: {key}")
        if key in lookup:
            raise ValueError(f"duplicate result key: {key}")
        for name in ("tracking_mse", "tracking_mae", "action_energy"):
            value = float(row[name])
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"invalid {name}")
        lookup[key] = float(row["tracking_mse"])
    if len(lookup) != expected_rows:
        raise ValueError("missing episode-arm keys")

    for fit in fits:
        if int(fit["training_seed"]) not in SEEDS or fit["arm"] not in LEARNED:
            raise ValueError("unexpected training fit row")
        if (int(fit["parameter_count"]) != 3 or int(fit["updates"]) != 100 or
                int(fit["batch_size"]) != 16 or int(fit["sequence_steps_per_fit"]) != 100 * 16 * STEPS):
            raise ValueError("parameter count or training budget mismatch")
        params = json.loads(fit["parameters_json"])
        if len(params) != 3 or not np.isfinite(params).all():
            raise ValueError("invalid fitted parameters")

    for audit in audits:
        if audit["all_timestep_marginals_match"] != "True" or audit["donor_assignment_is_derangement"] != "True":
            raise ValueError("yoke marginal/identity audit failed")
        if int(audit["steps_checked"]) != STEPS:
            raise ValueError("unexpected number of time steps checked")
        assignment = np.asarray(json.loads(audit["donor_assignment_json"]), dtype=np.int64)
        if len(assignment) != NTEST or not np.array_equal(np.sort(assignment), np.arange(NTEST)):
            raise ValueError("donor mapping is not a bijection")
        if np.any(assignment == np.arange(NTEST)):
            raise ValueError("donor mapping contains a self-pair")

    seed_order = sorted(SEEDS)
    primary = np.array([[lookup[(seed, TRAIN_HAZARD, TRAIN_MISSING, ep, "SENSORY_CROSS_AGENT_YOKE")] -
                         lookup[(seed, TRAIN_HAZARD, TRAIN_MISSING, ep, "SENSORY_SELF")]
                         for ep in range(NTEST)] for seed in seed_order])
    rng = np.random.default_rng(BOOT_SEED)
    assert_summary(summary["primary"], crossed_bootstrap(primary, rng))
    contrast_results = {}
    for arm in CONTRAST_ARMS:
        matrix = np.array([[lookup[(seed, TRAIN_HAZARD, TRAIN_MISSING, ep, arm)] -
                            lookup[(seed, TRAIN_HAZARD, TRAIN_MISSING, ep, "SENSORY_SELF")]
                            for ep in range(NTEST)] for seed in seed_order])
        expected = crossed_bootstrap(matrix, rng)
        assert_summary(summary["direct_control_contrasts_vs_sensory_self"][arm], expected)
        contrast_results[arm] = expected

    expected_yoke_checks = {
        "n_seed_condition_blocks": len(audits),
        "marginals_match_at_each_time_step": True,
        "all_donor_assignments_are_derangements": True,
        "time_steps_checked": len(audits) * STEPS,
    }
    if summary["yoke_checks"] != expected_yoke_checks:
        raise ValueError("summary yoke audit does not match the audit table")
    if manifest["episode_rows"] != expected_rows or manifest["training_rows"] != len(fits) or manifest["yoke_audit_rows"] != len(audits):
        raise ValueError("manifest row counts mismatch")

    print(json.dumps({
        "status": "PASS",
        "verified_episode_rows": len(episode_rows),
        "verified_training_fits": len(fits),
        "verified_yoke_blocks": len(audits),
        "primary": summary["primary"],
        "direct_control_contrasts": contrast_results,
        "source_hashes": expected_hashes,
    }, indent=2))


if __name__ == "__main__":
    main()
