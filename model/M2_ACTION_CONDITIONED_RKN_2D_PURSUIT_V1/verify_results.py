#!/usr/bin/env python3
"""Independent structural and arithmetic checks for the pursuit experiment."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "data" / "results" / "M2_ACTION_CONDITIONED_RKN_2D_PURSUIT_V1" / "canonical"
SEEDS = list(range(76100, 76124))
ARMS = {"MODE_GAIN", "BILINEAR_RNN_8P", "ACRKN_L1", "MODE_GAIN_ACTION_YOKE", "KALMAN_ORACLE"}
CONDITIONS = {"ALIGNED", "REVERSED"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", nargs="?", type=Path, default=DEFAULT)
    parser.add_argument("--allow-pilot", action="store_true")
    args = parser.parse_args()
    root = args.result_dir.resolve()
    manifest = json.loads((root / "run_manifest.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    assert manifest["experiment_id"] == "M2_ACTION_CONDITIONED_RKN_2D_PURSUIT_V1"
    seeds = list(range(manifest["seed_range_used"][0], manifest["seed_range_used"][1] + 1))
    pilot = len(seeds) != len(SEEDS)
    assert not pilot or args.allow_pilot, "pilot verification requires --allow-pilot"
    assert seeds == SEEDS[:len(seeds)]
    expected_rows = len(seeds) * 2 * 256 * len(ARMS)
    assert manifest["episode_rows"] == expected_rows
    assert summary["rows"] == expected_rows
    for filename, expected in manifest["output_sha256"].items():
        assert sha256(root / filename) == expected, f"checksum mismatch: {filename}"

    episode = rows(root / "episode_metrics.csv")
    assert len(episode) == expected_rows
    key = {}
    counts = {}
    for row in episode:
        seed, condition, ep, arm = int(row["training_seed"]), row["condition"], int(row["episode_id"]), row["arm"]
        assert seed in seeds and condition in CONDITIONS and arm in ARMS and 0 <= ep < 256
        k = (seed, condition, ep, arm)
        assert k not in key, f"duplicate row: {k}"
        key[k] = row
        counts[(seed, condition, arm)] = counts.get((seed, condition, arm), 0) + 1
        for metric in ("final_distance", "success", "mean_distance", "steps_to_success"):
            value = float(row[metric])
            assert math.isfinite(value), f"non-finite {metric}: {k}"
        assert float(row["success"]) in (0.0, 1.0)
        assert 0 <= float(row["steps_to_success"]) <= 32
    assert all(v == 256 for v in counts.values())

    fit = rows(root / "training_metrics.csv")
    assert len(fit) == len(seeds) * 3
    assert {row["arm"] for row in fit} == {"MODE_GAIN", "BILINEAR_RNN_8P", "ACRKN_L1"}
    for row in fit:
        expected_params = 8 if row["arm"] in {"MODE_GAIN", "BILINEAR_RNN_8P"} else None
        assert expected_params is None or int(row["parameter_count"]) == expected_params
        assert int(row["parameter_count"]) > 0
        assert int(row["updates"]) == 200 and int(row["sequence_tokens_per_fit"]) == 102400
        assert math.isfinite(float(row["training_seconds"]))

    audits = rows(root / "yoke_audit.csv")
    assert len(audits) == len(seeds) * 2
    assert all(row["donor_is_derangement"] == "True" and row["donated_move_marginal_exact"] == "True"
               for row in audits)

    diffs = [float(key[(s, "ALIGNED", e, "ACRKN_L1")]["final_distance"]) -
             float(key[(s, "ALIGNED", e, "MODE_GAIN")]["final_distance"])
             for s in seeds for e in range(256)]
    observed = sum(diffs) / len(diffs)
    recorded = summary["primary"]["mean_left_minus_right"]
    assert abs(observed - recorded) < 1e-10, (observed, recorded)
    print(json.dumps({"status": "PASS", "pilot": pilot, "seeds": len(seeds),
                      "episode_rows": len(episode), "training_fits": len(fit),
                      "primary_mean_recomputed": observed}, indent=2))


if __name__ == "__main__":
    main()
