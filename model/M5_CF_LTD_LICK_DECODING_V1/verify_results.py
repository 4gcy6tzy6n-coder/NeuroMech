#!/usr/bin/env python3
"""Independently audit coverage, fold assignment, targets, metrics, and hashes."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np
from scipy.signal import lfilter
from sklearn.metrics import average_precision_score
from sklearn.model_selection import KFold, StratifiedKFold

ROOT = Path(__file__).resolve().parents[2]
NAME = "M5_CF_LTD_LICK_DECODING_V1"
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
ACQUISITION = RAW.parent / "ACQUISITION_MANIFEST.json"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
RUNNER = ROOT / "model" / NAME / "run_experiment.py"
SOURCE_HELPER = ROOT / "model/M5_REAL_TRIAL_INTERVAL_DECODING_V1/run_experiment.py"
OUT = ROOT / "data/results" / NAME / "canonical"
FOLDS = 5
SEED = 20261001
LABEL_START = 0.05
LABEL_END = 0.20
CENSOR_GAP = 0.05
GROUPS = (("1-s expert", 0, 1.0, 0.75),
          ("2-s novice / 1-s expert", 1, 2.0, 1.75),
          ("2-s expert", 2, 2.0, 1.75))
ARMS = ("TIME_LICK_HISTORY", "CF_LTD", "CF_NO_TRACE", "CF_EVENT_YOKED",
        "CF_TIME_SHUFFLED", "CF_CELL_SHUFFLED", "RAW_GRC_PC1", "RAW_GRC_PC16")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def vec(session: h5py.Group, name: str) -> np.ndarray:
    return np.asarray(session[name][()]).reshape(-1)


def scalar(session: h5py.Group, name: str) -> float:
    return float(vec(session, name)[0])


def expected_samples() -> tuple[dict[tuple[str, int], dict[int, int]],
                                 dict[tuple[str, int, int, int], int],
                                 dict[tuple[str, int], int]]:
    trial_folds: dict[tuple[str, int], dict[int, int]] = {}
    sample_labels: dict[tuple[str, int, int, int], int] = {}
    eligible_counts: dict[tuple[str, int], int] = {}
    with h5py.File(RAW, "r") as h5:
        for group, gi, expected_delay, min_delay in GROUPS:
            sessions = h5[h5["groups"][0, gi]]
            for si in range(sessions.shape[1]):
                session_index = si + 1
                s = h5[sessions[0, si]]
                n_trials = int(s["rewarded"].size)
                all_ids = np.arange(n_trials)
                reward = vec(s, "rewarded").astype(bool)
                good = vec(s, "goodmvdir").astype(bool)
                mvlen = vec(s, "mvlen")
                dtb = scalar(s, "dtb")
                delay = (vec(s, "rewtimes") - vec(s, "midpt")) * dtb
                tmpxx = vec(s, "tmpxx").astype(np.float64)
                reward_lick = np.asarray(s["rewAlgn/lick"][:, all_ids], dtype=np.float64)
                smooth = lfilter(np.ones(300) / 300.0, [1.0], reward_lick, axis=0)
                lick_qc = np.max(smooth[(tmpxx >= -1.75) & (tmpxx <= 1.75)], axis=0) < 0.99
                keep = (((reward & good & (delay > min_delay))
                         | (~reward & good & (mvlen > 6) & (delay > min_delay))) & lick_qc)
                if "laser" in s["rewAlgn"]:
                    laser = np.asarray(s["rewAlgn/laser"][:, all_ids], dtype=bool)
                    laser_win = (tmpxx >= -2.0) & (tmpxx <= 2.0)
                    keep &= ~np.any(laser[laser_win], axis=0)
                global_ids = np.flatnonzero(keep)
                if len(global_ids) < FOLDS:
                    raise AssertionError(f"not enough eligible trials for 5-fold audit: {group} {session_index}")
                reward_eligible = reward[global_ids]
                seed = SEED + gi * 100_000 + session_index
                counts = np.bincount(reward_eligible.astype(np.int8), minlength=2)
                if np.count_nonzero(counts) == 2 and np.all(counts >= FOLDS):
                    splitter = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=seed)
                    iterator = splitter.split(np.zeros(len(global_ids)), reward_eligible)
                else:
                    splitter = KFold(n_splits=FOLDS, shuffle=True, random_state=seed)
                    iterator = splitter.split(np.zeros(len(global_ids)))
                folds = np.full(len(global_ids), -1, dtype=np.int8)
                for fold, (_, test_local) in enumerate(iterator):
                    folds[test_local] = fold
                trial_folds[(group, session_index)] = {int(global_ids[i] + 1): int(folds[i])
                                                       for i in range(len(global_ids))}
                eligible_counts[(group, session_index)] = len(global_ids)

                cb_axis = vec(s, "tmpxCb").astype(np.float64)
                beh_axis = tmpxx
                lick = np.asarray(s["midAlgn/lick"][:, global_ids], dtype=np.uint8).T
                candidate = np.flatnonzero((cb_axis >= 0.0) & (cb_axis <= expected_delay - 0.25))
                for local, global_id in enumerate(global_ids):
                    onset_ix = np.flatnonzero(np.diff(lick[local].astype(np.int16)) > 0) + 1
                    onsets = beh_axis[onset_ix]
                    times = cb_axis[candidate]
                    allowed = times + LABEL_END < delay[global_id] - CENSOR_GAP
                    for frame, t in zip(candidate[allowed], times[allowed]):
                        lower, upper = t + LABEL_START, t + LABEL_END
                        lo = np.searchsorted(onsets, lower, side="right")
                        hi = np.searchsorted(onsets, upper, side="right")
                        key = (group, session_index, int(global_id + 1), int(round(float(t) * 1_000_000)))
                        sample_labels[key] = int(hi > lo)
    return trial_folds, sample_labels, eligible_counts


def main() -> None:
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    pinned = {"raw": sha256(RAW), "manifest": sha256(ACQUISITION),
              "contract": sha256(CONTRACT), "runner": sha256(RUNNER),
              "source_helper": sha256(SOURCE_HELPER)}
    if manifest["pinned_hashes"] != pinned:
        raise AssertionError("a pinned input/code hash differs from the run manifest")
    for name, item in manifest["output_files"].items():
        path = OUT / name
        if not path.exists() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise AssertionError(f"output checksum mismatch: {name}")
    expected_names = set(manifest["output_files"]) | {"manifest.json"}
    actual_names = {p.name for p in OUT.iterdir() if p.is_file()}
    if actual_names != expected_names:
        raise AssertionError("canonical output inventory differs from the manifest")

    trials_by_session, expected, eligible_counts = expected_samples()
    inventory = read_csv(OUT / "session_inventory.csv")
    if len(inventory) != 16:
        raise AssertionError(f"expected 16 sessions, found {len(inventory)}")
    inv_map = {(r["group"], int(r["session_index"])): r for r in inventory}
    if set(inv_map) != set(trials_by_session):
        raise AssertionError("session inventory does not match the acquired group/session structure")
    for key, folds in trials_by_session.items():
        row = inv_map[key]
        if int(row["eligible_trials"]) != eligible_counts[key] or len(folds) != eligible_counts[key]:
            raise AssertionError(f"eligible trial count mismatch: {key}")

    sample_state: dict[tuple[str, int, int, int], dict[str, object]] = {}
    trial_acc: dict[tuple[str, int, int, str], list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    session_ap: dict[tuple[str, int, str], tuple[list[int], list[float]]] = {}
    n_prediction_rows = 0
    with (OUT / "heldout_predictions.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            n_prediction_rows += 1
            group, session = row["group"], int(row["session_index"])
            trial, fold = int(row["trial_index"]), int(row["fold"])
            arm, time_s = row["arm"], float(row["time_since_midpoint_s"])
            y, prob = int(row["observed_lick_onset"]), float(row["predicted_probability"])
            if arm not in ARMS or not (0.0 <= prob <= 1.0) or y not in (0, 1):
                raise AssertionError("invalid arm, probability, or binary target")
            expected_trial_fold = trials_by_session[(group, session)].get(trial)
            if expected_trial_fold is None or expected_trial_fold != fold:
                raise AssertionError(f"held-out trial/fold assignment mismatch: {group} {session} {trial}")
            time_key = int(round(time_s * 1_000_000))
            sample_key = (group, session, trial, time_key)
            state = sample_state.setdefault(sample_key, {"arms": set(), "y": y, "fold": fold, "frame": None})
            if arm in state["arms"]:
                raise AssertionError(f"duplicate arm prediction for sample {sample_key} {arm}")
            if state["y"] != y or state["fold"] != fold:
                raise AssertionError(f"arm targets/folds differ for sample {sample_key}")
            state["arms"].add(arm)
            key = (group, session, trial)
            # Frame index is resolved against the expected time list after read.
            if "probs" not in state:
                state["probs"] = {}
            state["probs"][arm] = prob
            accum = trial_acc[(group, session, trial, arm)]
            accum[0] += (prob - y) ** 2
            clipped = min(max(prob, 1e-8), 1 - 1e-8)
            accum[1] += -(y * np.log(clipped) + (1 - y) * np.log1p(-clipped))
            accum[2] += 1
            ap_key = (group, session, arm)
            ys, ps = session_ap.setdefault(ap_key, ([], []))
            ys.append(y)
            ps.append(prob)

    if set(sample_state) != set(expected):
        missing = len(set(expected) - set(sample_state))
        extra = len(set(sample_state) - set(expected))
        raise AssertionError(f"trial-time coverage mismatch: missing={missing}, extra={extra}")
    for key, state in sample_state.items():
        if state["arms"] != set(ARMS):
            raise AssertionError(f"incomplete arm coverage for {key}")
        if state["y"] != expected[key]:
            raise AssertionError(f"observed label differs from raw lick contacts for {key}")

    trial_rows = read_csv(OUT / "trial_scores.csv")
    trial_map = {(r["group"], int(r["session_index"]), int(r["trial_index"]), r["arm"]): r
                 for r in trial_rows}
    if len(trial_map) != len(trial_rows):
        raise AssertionError("duplicate trial score row")
    if set(trial_map) != set(trial_acc):
        raise AssertionError("trial-score coverage differs from trial-time predictions")
    for key, acc in trial_acc.items():
        row = trial_map[key]
        n = int(acc[2])
        actual = (float(row["brier_score"]), float(row["log_loss"]), n)
        expected_metrics = (acc[0] / n, acc[1] / n, int(float(row["n_time_samples"])))
        if not np.allclose(actual[:2], expected_metrics[:2], rtol=0, atol=1e-11) or n != expected_metrics[2]:
            raise AssertionError(f"trial score recomputation mismatch: {key}")

    session_rows = read_csv(OUT / "session_summary.csv")
    if len(session_rows) != 16 * len(ARMS):
        raise AssertionError("unexpected session summary row count")
    session_map = {(r["group"], int(r["session_index"]), r["arm"]): r for r in session_rows}
    trial_by_session_arm: dict[tuple[str, int, str], list[dict[str, str]]] = defaultdict(list)
    for r in trial_rows:
        trial_by_session_arm[(r["group"], int(r["session_index"]), r["arm"])].append(r)
    for key, rows in trial_by_session_arm.items():
        sr = session_map[key]
        brier = float(np.mean([float(x["brier_score"]) for x in rows]))
        logloss = float(np.mean([float(x["log_loss"]) for x in rows]))
        if not np.isclose(brier, float(sr["mean_trial_brier"]), rtol=0, atol=1e-11):
            raise AssertionError(f"session Brier mismatch: {key}")
        if not np.isclose(logloss, float(sr["mean_trial_log_loss"]), rtol=0, atol=1e-11):
            raise AssertionError(f"session log-loss mismatch: {key}")
        base_key = (key[0], key[1], "TIME_LICK_HISTORY")
        base = float(session_map[base_key]["mean_trial_brier"])
        if not np.isclose(base - brier, float(sr["brier_gain_vs_time_history"]), rtol=0, atol=1e-11):
            raise AssertionError(f"session primary contrast mismatch: {key}")
        ys, ps = session_ap[key]
        if np.unique(ys).size == 2:
            ap = average_precision_score(ys, ps)
            if not np.isclose(ap, float(sr["sample_level_average_precision"]), rtol=0, atol=1e-11):
                raise AssertionError(f"session average precision mismatch: {key}")

    fit_rows = read_csv(OUT / "fold_fit_manifest.csv")
    if len(fit_rows) != 16 * FOLDS * len(ARMS):
        raise AssertionError(f"unexpected fold-fit manifest size: {len(fit_rows)}")
    for row in fit_rows:
        key = (row["group"], int(row["session_index"]))
        n = eligible_counts[key]
        test_n = sum(v == int(row["fold"]) for v in trials_by_session[key].values())
        if int(row["n_train_trials"]) != n - test_n or int(row["n_test_trials"]) != test_n:
            raise AssertionError(f"fit manifest trial counts disagree with split: {key}, fold {row['fold']}")

    summary = json.loads((OUT / "summary.json").read_text())
    if summary["sessions"] != 16 or summary["eligible_trials"] != sum(eligible_counts.values()):
        raise AssertionError("summary counts differ from raw-data audit")
    if summary["heldout_trial_time_predictions"] != n_prediction_rows:
        raise AssertionError("summary prediction row count mismatch")
    print(json.dumps({"status": "PASS", "sessions": 16,
                      "eligible_trials": sum(eligible_counts.values()),
                      "unique_trial_time_samples": len(expected),
                      "prediction_rows": n_prediction_rows,
                      "fold_fit_rows": len(fit_rows),
                      "checks": ["pinned input/code/output hashes", "raw trial and sensor-QC inventory",
                                 "deterministic whole-trial fold assignment", "trial-time target reconstruction",
                                 "all-arm coverage", "trial/session metric recomputation"]}, indent=2))


if __name__ == "__main__":
    main()
