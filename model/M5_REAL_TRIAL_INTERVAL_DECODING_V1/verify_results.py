#!/usr/bin/env python3
"""Verify prediction coverage, training-mean baseline, session metrics, and hashes."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME = "M5_REAL_TRIAL_INTERVAL_DECODING_V1"
OUT = ROOT / "data/results" / NAME / "canonical"
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
ACQUISITION = RAW.parent / "ACQUISITION_MANIFEST.json"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
RUNNER = ROOT / "model" / NAME / "run_experiment.py"
FOLDS = 5
ARMS = {"BIO_CF_LTD", "BIO_NO_TRACE", "CF_EVENT_YOKED", "GRC_TIME_SHUFFLED", "CELL_SHUFFLED", "RAW_GRC_PCA16_RIDGE", "TRAINING_MEAN"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0, abs_tol=1e-11)


def main() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text())
    assert manifest["experiment"] == NAME
    assert manifest["raw_sha256"] == sha256(RAW)
    assert manifest["acquisition_manifest_sha256"] == sha256(ACQUISITION)
    assert manifest["contract_sha256"] == sha256(CONTRACT)
    assert manifest["runner_sha256"] == sha256(RUNNER)
    for filename, meta in manifest["outputs"].items():
        path = OUT / filename
        assert path.is_file() and path.stat().st_size == meta["bytes"]
        assert sha256(path) == meta["sha256"]

    predictions = read_csv(OUT / "heldout_predictions.csv")
    fits = read_csv(OUT / "fold_fit_manifest.csv")
    inventory = read_csv(OUT / "session_inventory.csv")
    session_summary = read_csv(OUT / "session_summary.csv")
    group_summary = read_csv(OUT / "group_summary.csv")
    assert predictions and inventory
    trial_rows: dict[tuple[str, int, int], list[dict[str, str]]] = defaultdict(list)
    session_trial_arm: dict[tuple[str, int, int, str], dict[str, str]] = {}
    for row in predictions:
        assert row["arm"] in ARMS
        assert all(math.isfinite(float(row[k])) for k in ("target_delay_s", "predicted_delay_s", "absolute_error_s", "baseline_absolute_error_s"))
        assert float(row["absolute_error_s"]) >= 0 and float(row["baseline_absolute_error_s"]) >= 0
        key = (row["group"], int(row["session_index"]), int(row["source_trial_index"]))
        trial_rows[key].append(row)
        fold_key = (*key, row["arm"])
        assert fold_key not in session_trial_arm
        session_trial_arm[fold_key] = row
    expected_keys = {(r["group"], int(r["session_index"])) for r in inventory}
    assert len(expected_keys) == len(inventory)
    for key, rows in trial_rows.items():
        assert {r["arm"] for r in rows} == ARMS and len(rows) == len(ARMS), key
        assert len({int(r["fold"]) for r in rows}) == 1
        assert len({float(r["target_delay_s"]) for r in rows}) == 1
        assert len({float(r["baseline_absolute_error_s"]) for r in rows}) == 1
    for group, session in expected_keys:
        session_keys = [key for key in trial_rows if key[:2] == (group, session)]
        assert len(session_keys) == int(next(r["eligible_trials"] for r in inventory if r["group"] == group and int(r["session_index"]) == session))
        folds = [int(trial_rows[key][0]["fold"]) for key in session_keys]
        assert set(folds) == set(range(FOLDS))

    # Validate the fold-specific session-mean baseline using only the other four folds.
    for group, session in expected_keys:
        keys = [key for key in trial_rows if key[:2] == (group, session)]
        targets_by_trial = {int(key[2]): float(trial_rows[key][0]["target_delay_s"]) for key in keys}
        folds_by_trial = {int(key[2]): int(trial_rows[key][0]["fold"]) for key in keys}
        for trial_index in targets_by_trial:
            test_fold = folds_by_trial[trial_index]
            train_values = [y for other, y in targets_by_trial.items() if folds_by_trial[other] != test_fold]
            train_mean = sum(train_values) / len(train_values)
            base_error = abs(train_mean - targets_by_trial[trial_index])
            for row in trial_rows[(group, session, trial_index)]:
                assert close(float(row["baseline_absolute_error_s"]), base_error)

    assert len(fits) == len(inventory) * FOLDS * 6
    fit_keys = [(r["group"], int(r["session_index"]), int(r["fold"]), r["arm"]) for r in fits]
    assert len(set(fit_keys)) == len(fit_keys)
    assert all(r["arm"] in ARMS - {"TRAINING_MEAN"} for r in fits)

    # Recompute the canonical session table and compare all stored summaries.
    calc_session = {}
    for group, session in expected_keys:
        for arm in ARMS:
            rows = [r for key, rs in trial_rows.items() if key[:2] == (group, session) for r in rs if r["arm"] == arm]
            errors = [float(r["absolute_error_s"]) for r in rows]
            bases = [float(r["baseline_absolute_error_s"]) for r in rows]
            base = sum(bases) / len(bases)
            mae = sum(errors) / len(errors)
            calc_session[(group, session, arm)] = (len(rows), mae, base, (base - mae) / max(base, 1e-12))
    stored_session = {(r["group"], int(r["session_index"]), r["arm"]): r for r in session_summary}
    assert set(stored_session) == set(calc_session)
    for key, (n, mae, base, frac) in calc_session.items():
        row = stored_session[key]
        assert int(row["n_heldout_trials"]) == n
        assert close(float(row["mean_absolute_error_s"]), mae)
        assert close(float(row["training_mean_baseline_mae_s"]), base)
        assert close(float(row["fraction_baseline_mae_reduced"]), frac)
    for row in group_summary:
        group, arm = row["group"], row["arm"]
        matches = [v for (g, _, a), v in calc_session.items() if g == group and a == arm]
        assert int(row["n_sessions"]) == len(matches)
        assert close(float(row["mean_session_mae_s"]), sum(v[1] for v in matches) / len(matches))

    result = {"status": "PASS", "heldout_prediction_rows": len(predictions),
              "unique_heldout_trial_keys": len(trial_rows), "session_count": len(inventory),
              "session_arm_summaries_recomputed": len(session_summary), "group_arm_summaries_checked": len(group_summary),
              "fold_fit_records": len(fits), "manifest_outputs_hash_checked": len(manifest["outputs"]),
              "scope": "data and summary integrity; does not independently rerun source model fitting"}
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
