#!/usr/bin/env python3
"""Verify hashes, seed coverage, paired episodes, and metrics for transfer V2."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = "M5_CEREBELLAR_SOURCE_LTD_TRANSFER_V2"
OUT = ROOT / "data/results" / EXP
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
ACQUISITION = RAW.parent / "ACQUISITION_MANIFEST.json"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
RUNNER = ROOT / "model" / EXP / "run_experiment.py"
ARMS = {"BIO_CF_LTD", "BIO_NO_TRACE", "BIO_CF_TIME_SHUFFLED", "BIO_CELL_SHUFFLED",
        "GENERIC_RBF_CF_LTD", "SHUFFLED_BIO_CF_LTD", "UNIFORM_POOL", "EMPIRICAL_TIMER"}
MAPPINGS = {"ALIGNED", "REVERSED"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    manifest = json.loads((OUT / "run_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    assert manifest["experiment_id"] == EXP
    assert manifest["raw_sha256"] == digest(RAW)
    assert manifest["raw_sha256_matches_dryad"] is True
    assert manifest["acquisition_manifest_sha256"] == digest(ACQUISITION)
    assert manifest["contract_sha256"] == digest(CONTRACT)
    assert manifest["runner_sha256"] == digest(RUNNER)
    for name, recorded in manifest["outputs"].items():
        path = OUT / name
        assert path.is_file() and path.stat().st_size == recorded["bytes"], name
        assert digest(path) == recorded["sha256"], name

    episodes = read_csv(OUT / "episode_results.csv")
    seeds = read_csv(OUT / "task_seed_results.csv")
    assert len(episodes) == 12 * 2 * 500 * len(ARMS)
    assert len(seeds) == 12 * 2 * len(ARMS)
    paired = defaultdict(dict)
    targets = defaultdict(set)
    cues = defaultdict(set)
    for row in episodes:
        key = (row["task_seed"], row["mapping"], row["episode_index"])
        paired[key][row["arm"]] = float(row["absolute_error_s"])
        targets[key].add(float(row["true_reward_time_s"]))
        cues[key].add(row["cue"])
        assert row["arm"] in ARMS and row["mapping"] in MAPPINGS
        assert math.isfinite(float(row["estimated_reward_time_s"]))
        assert float(row["absolute_error_s"]) >= 0
    assert len(paired) == 12 * 2 * 500
    for key, arm_rows in paired.items():
        assert set(arm_rows) == ARMS, key
        assert len(targets[key]) == 1 and len(cues[key]) == 1, key

    for row in summary["summary_rows"]:
        assert row["arm"] in ARMS and row["mapping"] in MAPPINGS
        assert row["n_task_seeds"] == 12
        for key in ("mean_seed_mae_s", "bootstrap95_low_s", "bootstrap95_high_s"):
            assert math.isfinite(float(row[key]))
    result = {"verification": "PASS", "output_hashes": len(manifest["outputs"]),
              "episode_rows": len(episodes), "paired_episode_sets": len(paired),
              "task_seed_rows": len(seeds), "arm_count": len(ARMS),
              "mappings": sorted(MAPPINGS), "contract_runner_raw_hashes": "PASS"}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
