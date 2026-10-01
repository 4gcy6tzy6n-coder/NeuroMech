#!/usr/bin/env python3
"""Independently verify M2 self-contingent feedback transfer outputs."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1"
OUT = ROOT / "data/results" / NAME / "canonical"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
RUNNER = ROOT / "model" / NAME / "run_experiment.py"
ARMS = ("SELF_SENSORY", "CROSS_AGENT_YOKED_SENSORY", "SELF_OUTPUT", "NO_FEEDBACK", "GENERIC_RNN_1D", "GRU_8")
PARAMS = {"SELF_SENSORY": 4, "CROSS_AGENT_YOKED_SENSORY": 4, "SELF_OUTPUT": 4,
          "NO_FEEDBACK": 3, "GENERIC_RNN_1D": 6, "GRU_8": 297}
CONDITIONS = ("SLOW_TRANSIENT", "FAST_TRANSIENT", "SLOW_CLEAN", "FAST_CLEAN")
METRICS = ("movement_mse", "movement_mae", "state_accuracy", "command_energy", "mean_switch_latency_steps")
N_BLOCKS, N_TEST, T, BOOTSTRAPS = 32, 128, 96, 20_000
PRIMARY_SEED = 8_765_432


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bootstrap(values: list[float], seed: int) -> dict[str, float | int]:
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    sample = v[rng.integers(0, len(v), size=(BOOTSTRAPS, len(v)))].mean(axis=1)
    return {"mean": float(v.mean()), "median": float(np.median(v)),
            "ci95_low": float(np.quantile(sample, .025)), "ci95_high": float(np.quantile(sample, .975)),
            "n_seed_blocks": int(len(v))}


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=1e-11)


def main() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text())
    assert manifest["experiment"] == NAME
    assert manifest["contract_sha256"] == sha256(CONTRACT)
    assert manifest["runner_sha256"] == sha256(RUNNER)
    assert manifest["verifier_sha256"] == sha256(Path(__file__))
    for filename, meta in manifest["outputs"].items():
        p = OUT / filename
        assert p.is_file() and p.stat().st_size == meta["bytes"] and sha256(p) == meta["sha256"]

    fits = read_csv(OUT / "fit_manifest.csv")
    episodes = read_csv(OUT / "test_episode_metrics.csv")
    seed_rows = read_csv(OUT / "test_seed_summary.csv")
    summary = json.loads((OUT / "summary.json").read_text())
    checks = json.loads((OUT / "feedback_distribution_check.json").read_text())["checks"]
    assert len(fits) == N_BLOCKS * len(ARMS)
    assert len(episodes) == N_BLOCKS * len(ARMS) * len(CONDITIONS) * N_TEST
    assert len(seed_rows) == N_BLOCKS * len(ARMS) * len(CONDITIONS)
    assert len(checks) == N_BLOCKS * len(CONDITIONS)

    fit_keys = set()
    for row in fits:
        key = (int(row["seed_block"]), row["arm"])
        assert key not in fit_keys and row["arm"] in ARMS
        fit_keys.add(key)
        params = json.loads(row["learned_parameters"])
        assert len(params) == PARAMS[row["arm"]] == int(row["parameter_count"])
        assert int(row["updates"]) == 100 and int(row["batch_size_trajectories"]) == 32
        assert int(row["sequence_length"]) == T

    row_keys = set()
    episode_groups: dict[tuple[int, str, str], list[dict[str, str]]] = defaultdict(list)
    yoke_maps: dict[tuple[int, str], dict[int, int]] = defaultdict(dict)
    for row in episodes:
        block, ep = int(row["seed_block"]), int(row["episode_id"])
        assert row["arm"] in ARMS and row["condition"] in CONDITIONS and 0 <= ep < N_TEST
        key = (block, row["arm"], row["condition"], ep)
        assert key not in row_keys
        row_keys.add(key)
        episode_groups[key[:3]].append(row)
        if row["arm"] == "CROSS_AGENT_YOKED_SENSORY":
            yoke_maps[(block, row["condition"])][ep] = int(row["yoke_donor_episode_id"])
        else:
            assert row["yoke_donor_episode_id"] == ""
        assert all(math.isfinite(float(row[m])) for m in METRICS if row[m] not in ("nan", ""))

    for (block, condition), mapping in yoke_maps.items():
        assert len(mapping) == N_TEST and all(k != v for k, v in mapping.items())
        assert set(mapping.values()) == set(range(N_TEST))

    check_map = {}
    for row in checks:
        key = (int(row["seed_block"]), row["condition"])
        assert key not in check_map
        check_map[key] = row
        assert row["donor_mapping_has_no_fixed_points"] is True
        assert row["exact_instantaneous_population_distribution_match"] is True
        assert close(float(row["max_sorted_feedback_difference"]), 0.0)
        a, b = row["self_sorted_feedback_sha256_by_step"], row["yoke_sorted_feedback_sha256_by_step"]
        assert len(a) == len(b) == T and a == b

    seed_map = {}
    for row in seed_rows:
        key = (int(row["seed_block"]), row["arm"], row["condition"])
        assert key not in seed_map
        seed_map[key] = row
        group = episode_groups[key]
        assert len(group) == N_TEST and int(row["n_episodes"]) == N_TEST
        for metric in METRICS:
            vals = [float(r[metric]) for r in group if r[metric] not in ("nan", "")]
            expected = float(np.mean(vals)) if vals else float("nan")
            actual = float(row[metric]) if row[metric] not in ("nan", "") else float("nan")
            assert (math.isnan(expected) and math.isnan(actual)) or close(expected, actual)

    primary = []
    for block in range(N_BLOCKS):
        yoke = float(seed_map[(block, "CROSS_AGENT_YOKED_SENSORY", "SLOW_TRANSIENT")]["movement_mse"])
        self_value = float(seed_map[(block, "SELF_SENSORY", "SLOW_TRANSIENT")]["movement_mse"])
        primary.append(yoke - self_value)
    expected = bootstrap(primary, PRIMARY_SEED)
    for key, value in expected.items():
        assert close(float(summary["primary_contrast_summary"][key]), float(value))
    actual_primary = summary["primary_seed_block_values"]
    assert len(actual_primary) == N_BLOCKS
    for i, row in enumerate(actual_primary):
        assert int(row["seed_block"]) == i and close(float(row["yoked_minus_self_movement_mse"]), primary[i])
    assert summary["primary_distribution_match_checks_passed"] is True

    result = {"status": "PASS", "fit_records": len(fits), "test_episode_rows": len(episodes),
              "test_seed_summary_rows": len(seed_rows), "population_distribution_checks": len(checks),
              "primary_seed_blocks_recomputed": len(primary), "hashed_outputs_checked": len(manifest["outputs"]),
              "scope": "artifact hashes, row coverage, parameters, exact yoke mapping/distribution, seed aggregation, primary bootstrap"}
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
