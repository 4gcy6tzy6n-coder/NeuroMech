#!/usr/bin/env python3
"""Independent structural and arithmetic checks for the continuous tracking run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_CONTINUOUS_TRACKING_MOTOR_STATE_TRANSFER_V1"
DEFAULT_OUT = ROOT / "data/results" / NAME / "canonical"
ARMS = ("GRU_SELF_MOTOR", "GRU_ZERO_MOTOR", "GRU_ACTION_COPY", "GRU_YOKED_MOTOR")
PROFILES = ("TRAIN_LIKE", "LONG_MISSING_BURSTS", "LOW_MISSING", "FAST_TARGET")


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
    episodes = read_csv(out / "episode_metrics.csv")
    seeds = read_csv(out / "seed_summary.csv")
    summary = json.loads((out / "summary.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    yokes = json.loads((out / "yoke_distribution_check.json").read_text())["checks"]

    assert len(fits) == 32 * len(ARMS)
    assert len(episodes) == 32 * len(ARMS) * len(PROFILES) * 128
    assert len(seeds) == 32 * len(ARMS) * len(PROFILES)
    assert {r["arm"] for r in fits} == set(ARMS)
    assert {r["arm"] for r in episodes} == set(ARMS)
    assert {r["profile"] for r in episodes} == set(PROFILES)
    assert all(int(r["parameter_count"]) == 378 and int(r["updates"]) == 100 for r in fits)

    groups: dict[tuple[int, str, str], list[dict[str, str]]] = {}
    seen = set()
    for row in episodes:
        key = (int(row["seed_block"]), row["arm"], row["profile"], int(row["episode_id"]))
        assert key not in seen, f"duplicate row: {key}"
        seen.add(key)
        groups.setdefault(key[:3], []).append(row)
        for field in ("tracking_mse", "tracking_rmse", "command_energy", "missing_fraction"):
            assert np.isfinite(float(row[field]))
        assert float(row["tracking_mse"]) >= 0 and float(row["command_energy"]) >= 0
        assert 0 <= float(row["missing_fraction"]) <= 1
    assert all(len(rows) == 128 for rows in groups.values())

    metrics = ("tracking_mse", "tracking_rmse", "command_energy", "missing_fraction")
    recomputed: dict[tuple[int, str, str], dict[str, float]] = {}
    for key, rows in groups.items():
        recomputed[key] = {m: float(np.mean([float(r[m]) for r in rows])) for m in metrics}
    for row in seeds:
        key = (int(row["seed_block"]), row["arm"], row["profile"])
        assert key in recomputed
        assert int(row["n_episodes"]) == 128
        for metric in metrics:
            assert np.isclose(float(row[metric]), recomputed[key][metric], rtol=1e-11, atol=1e-12)

    def contrast(a: str, b: str) -> list[float]:
        return [recomputed[(block, a, "LONG_MISSING_BURSTS")]["tracking_mse"] -
                recomputed[(block, b, "LONG_MISSING_BURSTS")]["tracking_mse"] for block in range(32)]

    contrast_records = (
        ("primary_seed_block_values", "primary_contrast_summary", contrast("GRU_SELF_MOTOR", "GRU_ACTION_COPY")),
        ("secondary_self_minus_zero", "secondary_self_minus_zero_summary", contrast("GRU_SELF_MOTOR", "GRU_ZERO_MOTOR")),
        ("secondary_self_minus_yoke", "secondary_self_minus_yoke_summary", contrast("GRU_SELF_MOTOR", "GRU_YOKED_MOTOR")),
    )
    for values_key, summary_key, values in contrast_records:
        assert np.allclose(values, summary[values_key], rtol=1e-11, atol=1e-12)
        assert np.isclose(np.mean(values), summary[summary_key]["mean"], rtol=1e-11, atol=1e-12)

    assert len(yokes) == 32 * len(PROFILES)
    assert all(x["no_fixed_points"] and x["exact_per_time_per_coordinate_match"] for x in yokes)
    assert summary["yoke_checks_passed"] is True
    for filename, details in manifest["outputs"].items():
        path = out / filename
        assert path.stat().st_size == int(details["bytes"])
        assert sha256(path) == details["sha256"]
    for rel, expected in ((f"summery/{NAME}/CONTRACT.md", manifest["contract_sha256"]),
                          (f"model/{NAME}/run_experiment.py", manifest["runner_sha256"]),
                          (f"model/{NAME}/verify_results.py", manifest["verifier_sha256"])):
        assert sha256(ROOT / rel) == expected

    return {"status": "PASS", "fit_records": len(fits), "episode_rows": len(episodes),
            "seed_summary_rows": len(seeds), "yoke_checks": len(yokes),
            "checks": ["row/arm/profile completeness", "parameter/update matching",
                       "episode metric validity", "seed-summary recomputation",
                       "primary and secondary contrast recomputation", "exact yoke distribution checks",
                       "manifest and source hashes"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_OUT)
    print(json.dumps(verify(parser.parse_args().results_dir), indent=2))


if __name__ == "__main__":
    main()
