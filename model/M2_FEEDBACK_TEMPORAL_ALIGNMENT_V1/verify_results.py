#!/usr/bin/env python3
"""Independently validate the canonical M2 temporal-alignment run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_FEEDBACK_TEMPORAL_ALIGNMENT_V1"
DEFAULT_OUT = ROOT / "data/results" / NAME / "canonical"
ARMS = ("SELF_SENSORY", "LAG1_SENSORY", "LAG4_SENSORY", "CROSS_AGENT_YOKED_SENSORY", "SELF_OUTPUT", "NO_FEEDBACK", "GENERIC_RNN_1D", "GRU_8")
CONDITIONS = ("SLOW_TRANSIENT", "FAST_TRANSIENT", "SLOW_CLEAN", "FAST_CLEAN")
PARAMS = {"SELF_SENSORY": 4, "LAG1_SENSORY": 4, "LAG4_SENSORY": 4, "CROSS_AGENT_YOKED_SENSORY": 4, "SELF_OUTPUT": 4, "NO_FEEDBACK": 3, "GENERIC_RNN_1D": 6, "GRU_8": 297}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(out: Path) -> dict[str, object]:
    required = ("fit_manifest.csv", "test_episode_metrics.csv", "test_seed_summary.csv", "feedback_distribution_check.json", "summary.json", "manifest.json")
    missing = [name for name in required if not (out / name).is_file()]
    if missing:
        raise AssertionError(f"missing result artifacts: {missing}")

    fits = read_csv(out / "fit_manifest.csv")
    episodes = read_csv(out / "test_episode_metrics.csv")
    seeds = read_csv(out / "test_seed_summary.csv")
    summary = json.loads((out / "summary.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    yoke = json.loads((out / "feedback_distribution_check.json").read_text())

    assert len(fits) == 32 * len(ARMS), f"unexpected fit rows: {len(fits)}"
    assert len(episodes) == 32 * len(ARMS) * len(CONDITIONS) * 128, f"unexpected episode rows: {len(episodes)}"
    assert len(seeds) == 32 * len(ARMS) * len(CONDITIONS), f"unexpected seed summary rows: {len(seeds)}"
    assert set(r["arm"] for r in fits) == set(ARMS)
    assert set(r["condition"] for r in episodes) == set(CONDITIONS)
    assert set(r["arm"] for r in episodes) == set(ARMS)

    counts: dict[tuple[int, str], int] = {}
    episode_ids: dict[tuple[int, str, int], set[int]] = {}
    for row in episodes:
        block, arm, condition = int(row["seed_block"]), row["arm"], row["condition"]
        key = (block, arm, condition)
        counts[key] = counts.get(key, 0) + 1
        ekey = (block, condition, int(row["episode_id"]))
        episode_ids.setdefault(ekey, set()).add(arm)
        for metric in ("movement_mse", "movement_mae", "state_accuracy", "command_energy"):
            value = float(row[metric])
            assert np.isfinite(value), f"nonfinite {metric}: {key}"
            if metric in ("movement_mse", "command_energy"):
                assert value >= 0, f"negative {metric}: {key}"
        assert 0.0 <= float(row["state_accuracy"]) <= 1.0
    assert all(n == 128 for n in counts.values())
    assert all(arms == set(ARMS) for arms in episode_ids.values())

    for block in range(32):
        block_fits = [r for r in fits if int(r["seed_block"]) == block]
        assert len(block_fits) == len(ARMS)
        assert {r["arm"]: int(r["parameter_count"]) for r in block_fits} == PARAMS
        assert all(int(r["updates"]) == 100 for r in block_fits)

    # Recompute episode-to-seed aggregation from the raw evaluation rows.
    recomputed: dict[tuple[int, str, str], dict[str, float]] = {}
    metrics = ("movement_mse", "movement_mae", "state_accuracy", "command_energy", "mean_switch_latency_steps")
    for block in range(32):
        for arm in ARMS:
            for condition in CONDITIONS:
                rows = [r for r in episodes if int(r["seed_block"]) == block and r["arm"] == arm and r["condition"] == condition]
                values = {}
                for metric in metrics:
                    arr = np.asarray([float(r[metric]) for r in rows], dtype=float)
                    values[metric] = float(np.nanmean(arr))
                recomputed[(block, arm, condition)] = values
    for row in seeds:
        key = (int(row["seed_block"]), row["arm"], row["condition"])
        assert key in recomputed
        for metric, value in recomputed[key].items():
            assert np.isclose(float(row[metric]), value, rtol=1e-11, atol=1e-12, equal_nan=True), (key, metric, row[metric], value)

    primary = [recomputed[(block, "LAG4_SENSORY", "SLOW_TRANSIENT")]["movement_mse"] -
               recomputed[(block, "SELF_SENSORY", "SLOW_TRANSIENT")]["movement_mse"] for block in range(32)]
    stored = [float(r["lag4_minus_self_movement_mse"]) for r in summary["primary_seed_block_values"]]
    assert np.allclose(primary, stored, rtol=1e-11, atol=1e-12)
    assert np.isclose(np.mean(primary), float(summary["primary_contrast_summary"]["mean"]), rtol=1e-11, atol=1e-12)

    checks = yoke["checks"]
    assert len(checks) == 32 * len(CONDITIONS)
    assert all(x["exact_instantaneous_population_distribution_match"] for x in checks)
    assert all(x["donor_mapping_has_no_fixed_points"] for x in checks)
    assert summary["primary_distribution_match_checks_passed"] is True

    for filename, details in manifest["outputs"].items():
        path = out / filename
        assert path.is_file(), f"manifest output missing: {filename}"
        assert path.stat().st_size == int(details["bytes"]), f"size mismatch: {filename}"
        assert sha256(path) == details["sha256"], f"hash mismatch: {filename}"
    for artifact, expected in (("CONTRACT.md", manifest["contract_sha256"]),
                               ("run_experiment.py", manifest["runner_sha256"]),
                               ("verify_results.py", manifest["verifier_sha256"])):
        path = ROOT / ("summery" if artifact == "CONTRACT.md" else "model") / NAME / artifact
        assert sha256(path) == expected, f"source hash mismatch: {artifact}"

    return {"status": "PASS", "fit_records": len(fits), "episode_rows": len(episodes),
            "seed_summary_rows": len(seeds), "primary_seed_blocks": len(primary),
            "yoke_distribution_checks": len(checks), "checks": [
                "artifact inventory and row coverage", "parameter/update counts", "finite episode metrics",
                "recomputed seed summaries and primary contrast", "population-matched yoke checks",
                "manifest output and source hashes"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(verify(args.results_dir), indent=2))


if __name__ == "__main__":
    main()
