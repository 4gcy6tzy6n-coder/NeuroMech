#!/usr/bin/env python3
"""Independently audit M2 GRU motor-feedback ablation outputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_GRU_MOTOR_FEEDBACK_ABLATION_V1"
DEFAULT_OUT = ROOT / "data/results" / NAME / "canonical"
ARMS = ("GRU_SELF_MOTOR", "GRU_ZERO_MOTOR", "GRU_YOKED_MOTOR")
CONDITIONS = ("SLOW_TRANSIENT", "FAST_TRANSIENT", "SLOW_CLEAN", "FAST_CLEAN")


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
    fits = read_csv(out / "fit_manifest.csv")
    episodes = read_csv(out / "test_episode_metrics.csv")
    seeds = read_csv(out / "test_seed_summary.csv")
    summary = json.loads((out / "summary.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    yoke = json.loads((out / "yoke_distribution_check.json").read_text())["checks"]

    assert len(fits) == 32 * len(ARMS)
    assert len(episodes) == 32 * len(ARMS) * len(CONDITIONS) * 128
    assert len(seeds) == 32 * len(ARMS) * len(CONDITIONS)
    assert {r["arm"] for r in fits} == set(ARMS)
    assert {r["arm"] for r in episodes} == set(ARMS)
    assert {r["condition"] for r in episodes} == set(CONDITIONS)
    assert all(int(r["parameter_count"]) == 297 and int(r["updates"]) == 100 for r in fits)
    assert len({(int(r["seed_block"]), r["arm"]) for r in fits}) == len(fits)

    keys = set()
    by_group: dict[tuple[int, str, str], list[dict[str, str]]] = {}
    for r in episodes:
        key = (int(r["seed_block"]), r["arm"], r["condition"], int(r["episode_id"]))
        assert key not in keys, f"duplicate episode row: {key}"
        keys.add(key)
        by_group.setdefault(key[:3], []).append(r)
        assert all(np.isfinite(float(r[m])) for m in ("movement_mse", "movement_mae", "state_accuracy", "command_energy"))
        assert float(r["movement_mse"]) >= 0 and float(r["command_energy"]) >= 0
        assert 0 <= float(r["state_accuracy"]) <= 1
    assert all(len(rows) == 128 for rows in by_group.values())

    metrics = ("movement_mse", "movement_mae", "state_accuracy", "command_energy", "mean_switch_latency_steps")
    recomputed: dict[tuple[int, str, str], dict[str, float]] = {}
    for key, rows in by_group.items():
        recomputed[key] = {}
        for metric in metrics:
            recomputed[key][metric] = float(np.nanmean([float(r[metric]) for r in rows]))
    for row in seeds:
        key = (int(row["seed_block"]), row["arm"], row["condition"])
        assert key in recomputed
        for metric in metrics:
            assert np.isclose(float(row[metric]), recomputed[key][metric], rtol=1e-11, atol=1e-12, equal_nan=True)

    def contrast(a: str, b: str) -> list[float]:
        return [recomputed[(block, a, "SLOW_TRANSIENT")]["movement_mse"] -
                recomputed[(block, b, "SLOW_TRANSIENT")]["movement_mse"] for block in range(32)]

    for label, values in (("primary", contrast("GRU_SELF_MOTOR", "GRU_ZERO_MOTOR")),
                          ("secondary", contrast("GRU_SELF_MOTOR", "GRU_YOKED_MOTOR"))):
        stored = summary[f"{label}_seed_block_values"]
        assert np.allclose(values, stored, rtol=1e-11, atol=1e-12)
        stats = summary[f"{label}_contrast_summary"]
        assert np.isclose(np.mean(values), stats["mean"], rtol=1e-11, atol=1e-12)

    assert len(yoke) == 32 * len(CONDITIONS)
    assert all(r["exact_per_time_population_match"] and r["no_fixed_points"] for r in yoke)
    assert summary["yoke_checks_passed"] is True

    for filename, details in manifest["outputs"].items():
        path = out / filename
        assert path.stat().st_size == int(details["bytes"])
        assert sha256(path) == details["sha256"]
    for relative, expected in (("summery/" + NAME + "/CONTRACT.md", manifest["contract_sha256"]),
                               ("model/" + NAME + "/run_experiment.py", manifest["runner_sha256"]),
                               ("model/M2_FEEDBACK_TEMPORAL_ALIGNMENT_V1/run_experiment.py", manifest["task_source_sha256"])):
        assert sha256(ROOT / relative) == expected

    return {"status": "PASS", "fit_records": len(fits), "episode_rows": len(episodes),
            "seed_summary_rows": len(seeds), "yoke_checks": len(yoke),
            "checks": ["row/arm/condition completeness", "equal parameter/update counts",
                       "episode metric validity", "seed-summary recomputation", "primary and secondary contrast recomputation",
                       "exact yoke checks", "output and source hash validation"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_OUT)
    print(json.dumps(verify(parser.parse_args().results_dir), indent=2))


if __name__ == "__main__":
    main()
