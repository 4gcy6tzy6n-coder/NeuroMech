#!/usr/bin/env python3
"""Independent integrity and pairing checks for the CF-LTD held-out readout."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = "M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1"
OUT = ROOT / "data/results" / EXP
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
ACQUISITION = RAW.parent / "ACQUISITION_MANIFEST.json"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
RUNNER = ROOT / "model" / EXP / "run_experiment.py"
EXPECTED_GROUP_SESSIONS = {"1-s expert": 5, "2-s novice / 1-s expert": 5, "2-s expert": 6}
METHODS = {"CF_LTD", "UNIFORM", "CELL_SHUFFLED", "CF_TIME_SHUFFLED", "RIDGE_REFERENCE"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as stream:
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
        assert path.is_file(), f"missing output: {name}"
        assert path.stat().st_size == recorded["bytes"], f"size mismatch: {name}"
        assert digest(path) == recorded["sha256"], f"hash mismatch: {name}"

    trial_rows = read_csv("heldout_trial_results.csv")
    split_rows = read_csv("session_split_results.csv")
    session_rows = read_csv("session_summary.csv")
    weight_rows = read_csv("ltd_weights.csv")
    assert len(trial_rows) == summary["trial_rows"]
    assert len(split_rows) == summary["split_rows"]
    assert set(EXPECTED_GROUP_SESSIONS) == {r["group"] for r in session_rows}
    for group, n in EXPECTED_GROUP_SESSIONS.items():
        assert len({r["session_index"] for r in session_rows if r["group"] == group}) == n

    for rows, numeric_fields in (
        (trial_rows, ("pearson_r", "r_squared", "reward_delay_s")),
        (split_rows, ("mean_test_trial_r2", "median_test_trial_r2")),
        (weight_rows, ("source_ltd_weight", "cell_shuffled_weight", "cf_time_shuffled_weight")),
    ):
        for row in rows:
            for field in numeric_fields:
                if row.get(field) in (None, "", "nan", "NaN"):
                    continue
                assert math.isfinite(float(row[field])), (field, row)
    for row in trial_rows:
        r2 = float(row["r_squared"])
        assert -1e-12 <= r2 <= 1 + 1e-12
        assert row["method"] in METHODS

    paired: dict[tuple[str, str, str, str], dict[str, float]] = defaultdict(dict)
    for row in trial_rows:
        key = (row["group"], row["session_index"], row["split"], row["source_trial_index"])
        paired[key][row["method"]] = float(row["r_squared"])
    for key, methods in paired.items():
        assert set(methods) == METHODS, (key, methods.keys())
    split_method_sets: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in split_rows:
        if row["status"] == "OK":
            split_method_sets[(row["group"], row["session_index"], row["split"])].add(row["method"])
    for key, methods in split_method_sets.items():
        assert methods == METHODS, (key, methods)

    session_scores: dict[tuple[str, str, str], float] = {}
    for row in session_rows:
        session_scores[(row["group"], row["session_index"], row["method"])] = float(row["mean_split_trial_r2"])
    session_differences = {}
    for control in ("UNIFORM", "CF_TIME_SHUFFLED", "CELL_SHUFFLED", "RIDGE_REFERENCE"):
        diffs = []
        for group, n in EXPECTED_GROUP_SESSIONS.items():
            for session in range(1, n + 1):
                left = session_scores.get((group, str(session), "CF_LTD"))
                right = session_scores.get((group, str(session), control))
                if left is not None and right is not None:
                    diffs.append(left - right)
        session_differences[control] = {
            "sessions_compared": len(diffs),
            "cf_ltd_higher_count": sum(v > 0 for v in diffs),
            "mean_paired_difference": sum(diffs) / len(diffs),
        }
    result = {
        "verification": "PASS",
        "verified_output_hashes": len(manifest["outputs"]),
        "heldout_trial_rows": len(trial_rows),
        "split_result_rows": len(split_rows),
        "weight_rows": len(weight_rows),
        "paired_trial_records": len(paired),
        "paired_session_differences_descriptive_only": session_differences,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
