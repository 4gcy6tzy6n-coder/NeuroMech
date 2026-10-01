#!/usr/bin/env python3
"""Decode held-out anticipatory lick events from same-session GrC activity."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import time
from pathlib import Path

import h5py
import numpy as np
import scipy
from scipy.signal import lfilter
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, log_loss
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
NAME = "M5_CF_LTD_LICK_DECODING_V1"
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
ACQUISITION = RAW.parent / "ACQUISITION_MANIFEST.json"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
SOURCE_HELPER = ROOT / "model/M5_REAL_TRIAL_INTERVAL_DECODING_V1/run_experiment.py"
DEFAULT_OUT = ROOT / "data/results" / NAME / "canonical"
AUTHOR_COMMIT = "124c83e1af83e9680e05f9827448579d02345fa3"
AUTHOR_GRCCF_SHA256 = "a4a916f16052d2a0aa2f0bce969a2efd70646c1af244755a003452ce5b849628"
AUTHOR_LICK_SHA256 = "3bd4f5c2a19613f55de517825d9edf5ccd6f2dba83cd6e1961bafeab1f3eb337"
GROUPS = (("1-s expert", 0, 1.0, 0.75),
          ("2-s novice / 1-s expert", 1, 2.0, 1.75),
          ("2-s expert", 2, 2.0, 1.75))
FOLDS = 5
SEED = 20261001
N_TIME_BASIS = 8
LABEL_START = 0.05
LABEL_END = 0.20
CENSOR_GAP = 0.05
HISTORY_WINDOWS = (0.25, 1.0)
LOGISTIC_C = 1.0
MAX_ITER = 1000
TOL = 1e-8
ARMS = ("TIME_LICK_HISTORY", "CF_LTD", "CF_NO_TRACE", "CF_EVENT_YOKED",
        "CF_TIME_SHUFFLED", "CF_CELL_SHUFFLED", "RAW_GRC_PC1", "RAW_GRC_PC16")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_source_helpers():
    spec = importlib.util.spec_from_file_location("m5_interval_source_rule", SOURCE_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load source-rule implementation at {SOURCE_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


source = load_source_helpers()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def scalar(session: h5py.Group, name: str) -> float:
    return float(np.asarray(session[name][()]).reshape(-1)[0])


def read_behavior_trials(session: h5py.Group, align: str, field: str, trial_ids: np.ndarray) -> np.ndarray:
    # MATLAB trial × time arrays are exposed by HDF5 as time × trial.
    return np.asarray(session[f"{align}/{field}"][:, trial_ids]).T


def read_lick_trials(session: h5py.Group, align: str, trial_ids: np.ndarray) -> np.ndarray:
    return read_behavior_trials(session, align, "lick", trial_ids).astype(np.uint8)


def lick_sensor_valid(session: h5py.Group, tmpxx: np.ndarray, trial_ids: np.ndarray) -> np.ndarray:
    reward_lick = read_lick_trials(session, "rewAlgn", trial_ids).T.astype(np.float64)
    # Match the author's filter(ones(300,1)/300, 1, lick')' implementation.
    smoothed = lfilter(np.ones(300, dtype=np.float64) / 300.0, [1.0], reward_lick, axis=0)
    window = (tmpxx >= -1.75) & (tmpxx <= 1.75)
    return np.max(smoothed[window], axis=0) < 0.99


def time_basis(times: np.ndarray, expected_delay: float) -> np.ndarray:
    centers = np.linspace(0.0, 1.0, N_TIME_BASIS)
    scale = 0.18
    u = np.clip(times / expected_delay, 0.0, 1.0)
    return np.exp(-0.5 * ((u[:, None] - centers[None, :]) / scale) ** 2)


def event_counts(event_times: np.ndarray, low: np.ndarray, high: np.ndarray,
                 low_side: str = "left", high_side: str = "left") -> np.ndarray:
    return (np.searchsorted(event_times, high, side=high_side)
            - np.searchsorted(event_times, low, side=low_side)).astype(np.float64)


def build_session_samples(session: h5py.Group, trial_global: np.ndarray,
                          expected_delay: float) -> dict[str, np.ndarray]:
    axis = source.vec(session, "tmpxCb").astype(np.float64)
    behavior_axis = source.vec(session, "tmpxx").astype(np.float64)
    dtb = scalar(session, "dtb")
    target_delay = (source.vec(session, "rewtimes") - source.vec(session, "midpt")) * dtb
    reward_flags = source.vec(session, "rewarded").astype(bool)
    raw_mid = read_lick_trials(session, "midAlgn", trial_global)
    output: dict[str, list[np.ndarray]] = {"frame": [], "trial": [], "label": [], "base": []}
    onsets_by_trial: list[np.ndarray] = []
    for local, raw in enumerate(raw_mid):
        onset_indices = np.flatnonzero(np.diff(raw.astype(np.int16)) > 0) + 1
        onsets_by_trial.append(behavior_axis[onset_indices])

    candidate_frames = np.flatnonzero((axis >= 0.0) & (axis <= expected_delay - 0.25))
    candidate_times = axis[candidate_frames]
    for local, global_trial in enumerate(trial_global):
        onset_times = onsets_by_trial[local]
        times = candidate_times
        # Reward time is only an outcome-window censor; it is not included as a model feature.
        keep = times + LABEL_END < target_delay[global_trial] - CENSOR_GAP
        frames = candidate_frames[keep]
        times = axis[frames]
        if len(times) == 0:
            continue
        lower = times + LABEL_START
        upper = times + LABEL_END
        positive = event_counts(onset_times, lower, upper, "right", "right") > 0
        history = []
        for width in HISTORY_WINDOWS:
            history.append(event_counts(onset_times, times - width, times, "left", "left"))
        features = np.column_stack((time_basis(times, expected_delay), *history))
        output["frame"].append(frames.astype(np.int32))
        output["trial"].append(np.full(len(times), local, dtype=np.int32))
        output["label"].append(positive.astype(np.uint8))
        output["base"].append(features.astype(np.float64))
    if not output["frame"]:
        raise ValueError("no eligible anticipatory trial-time samples")
    return {key: np.concatenate(parts, axis=0) for key, parts in output.items()}


def fit_logistic_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray
                         ) -> tuple[np.ndarray, str]:
    if len(np.unique(y_train)) < 2:
        return np.full(len(x_test), float(y_train.mean()), dtype=np.float64), "NO_CLASS_VARIATION_CONSTANT"
    scaler = StandardScaler()
    x_train_z = scaler.fit_transform(x_train)
    x_test_z = scaler.transform(x_test)
    model = LogisticRegression(C=LOGISTIC_C, solver="lbfgs", max_iter=MAX_ITER,
                               tol=TOL, random_state=0)
    model.fit(x_train_z, y_train)
    return model.predict_proba(x_test_z)[:, 1], "FIT_OK"


def probabilities_metrics(y: np.ndarray, probability: np.ndarray) -> tuple[float, float]:
    p = np.clip(probability, 1e-8, 1.0 - 1e-8)
    brier = float(np.mean((p - y) ** 2))
    loss = float(-np.mean(y * np.log(p) + (1 - y) * np.log1p(-p)))
    return brier, loss


def preflight() -> dict[str, object]:
    sessions = []
    with h5py.File(RAW, "r") as h5:
        if "groups" not in h5 or h5["groups"].shape != (1, 3):
            raise ValueError("unexpected MATLAB root/group schema")
        for group, gi, expected_delay, min_delay in GROUPS:
            for si, ref in enumerate(source.session_refs(h5, gi), start=1):
                s = source.h5_ref(h5, ref)
                required = ("rewarded", "goodmvdir", "mvlen", "rewtimes", "midpt", "dtb", "dtimCb",
                            "tmpxx", "tmpxCb", "midAlgn", "rewAlgn")
                missing = [name for name in required if name not in s]
                for align, fields in (("midAlgn", ("lick", "sigFilt_GrC")),
                                      ("rewAlgn", ("lick", "sp_CF"))):
                    if align not in s:
                        missing.append(align)
                    else:
                        missing.extend(f"{align}/{field}" for field in fields if field not in s[align])
                if missing:
                    raise ValueError(f"{group} session {si}: missing {missing}")
                n_trials = int(s["rewarded"].size)
                all_trial_ids = np.arange(n_trials)
                valid_lick = lick_sensor_valid(s, source.vec(s, "tmpxx").astype(np.float64), all_trial_ids)
                reward = source.vec(s, "rewarded").astype(bool)
                good = source.vec(s, "goodmvdir").astype(bool)
                length = source.vec(s, "mvlen")
                delay = (source.vec(s, "rewtimes") - source.vec(s, "midpt")) * scalar(s, "dtb")
                min_keep = (delay > min_delay)
                keep = (((reward & good & min_keep)
                         | (~reward & good & (length > 6) & min_keep)) & valid_lick)
                if "laser" in s["rewAlgn"]:
                    laser = read_behavior_trials(s, "rewAlgn", "laser", all_trial_ids).T.astype(bool)
                    reward_axis = source.vec(s, "tmpxx").astype(np.float64)
                    laser_window = (reward_axis >= -2.0) & (reward_axis <= 2.0)
                    keep &= ~np.any(laser[laser_window], axis=0)
                indices = np.flatnonzero(keep)
                sample_design = build_session_samples(s, indices, expected_delay)
                sessions.append({"group": group, "session_index": si, "all_trials": n_trials,
                                 "eligible_trials": int(len(indices)), "candidate_time_samples": int(len(sample_design["label"])),
                                 "rewarded_trials": int(np.count_nonzero(reward[indices])),
                                 "omission_trials": int(np.count_nonzero(~reward[indices])),
                                 "grc_cells": int(s["midAlgn/sigFilt_GrC"].shape[1]),
                                 "cf_cells": int(s["rewAlgn/sp_CF"].shape[1]),
                                 "lick_samples": int(s["midAlgn/lick"].shape[0]),
                                 "grc_samples": int(s["midAlgn/sigFilt_GrC"].shape[0]),
                                 "imaging_dt_s": scalar(s, "dtimCb"), "behavior_dt_s": scalar(s, "dtb"),
                                 "midlick_and_grc_share_trial_axis": s["midAlgn/lick"].shape[1] == s["midAlgn/sigFilt_GrC"].shape[2]})
    return {"experiment": NAME, "classification": "retrospective exploratory within-session source-data analysis",
            "raw_sha256": sha256(RAW), "raw_bytes": RAW.stat().st_size,
            "acquisition_manifest_sha256": sha256(ACQUISITION), "contract_sha256": sha256(CONTRACT),
            "runner_sha256": sha256(Path(__file__)), "source_helper_sha256": sha256(SOURCE_HELPER),
            "author_source": {"repository_commit": AUTHOR_COMMIT,
                              "grc_cf_script_sha256": AUTHOR_GRCCF_SHA256,
                              "lick_script_sha256": AUTHOR_LICK_SHA256},
            "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "h5py": h5py.__version__, "sklearn": __import__("sklearn").__version__,
            "folds": FOLDS, "seed": SEED, "arms": list(ARMS), "sessions": sessions,
            "scoring_unit": "trial-level mean Brier, aggregated within session; session summaries descriptive",
            "caveat": "preprocessed neural time series are offline; no causal deployment claim"}


def _metric_rows(predictions: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    per_trial: dict[tuple[str, int, int, str], list[dict[str, object]]] = {}
    for row in predictions:
        key = (str(row["group"]), int(row["session_index"]), int(row["trial_index"]), str(row["arm"]))
        per_trial.setdefault(key, []).append(row)
    trial_rows = []
    for (group, session, trial, arm), rows in sorted(per_trial.items()):
        y = np.asarray([int(r["observed_lick_onset"] ) for r in rows], dtype=np.int8)
        p = np.asarray([float(r["predicted_probability"]) for r in rows], dtype=np.float64)
        brier, loss = probabilities_metrics(y, p)
        trial_rows.append({"group": group, "session_index": session, "trial_index": trial, "arm": arm,
                           "n_time_samples": len(rows), "observed_event_fraction": float(y.mean()),
                           "brier_score": brier, "log_loss": loss})
    return trial_rows, []


def aggregate(trial_rows: list[dict[str, object]], predictions: list[dict[str, object]]
              ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[tuple[str, int, str], list[dict[str, object]]] = {}
    for row in trial_rows:
        grouped.setdefault((str(row["group"]), int(row["session_index"]), str(row["arm"])), []).append(row)
    session = []
    baseline: dict[tuple[str, int], dict[str, float]] = {}
    for (group, session_ix, arm), rows in sorted(grouped.items()):
        brier = float(np.mean([float(r["brier_score"]) for r in rows]))
        loss = float(np.mean([float(r["log_loss"]) for r in rows]))
        event_frac = float(np.mean([float(r["observed_event_fraction"]) for r in rows]))
        session.append({"group": group, "session_index": session_ix, "arm": arm,
                        "n_trials": len(rows), "mean_trial_brier": brier,
                        "mean_trial_log_loss": loss, "mean_trial_event_fraction": event_frac})
        if arm == "TIME_LICK_HISTORY":
            baseline[(group, session_ix)] = {"brier": brier, "log_loss": loss}
    for row in session:
        base = baseline[(str(row["group"]), int(row["session_index"]))]
        row["brier_gain_vs_time_history"] = base["brier"] - float(row["mean_trial_brier"])
        row["log_loss_gain_vs_time_history"] = base["log_loss"] - float(row["mean_trial_log_loss"])
    pred_groups: dict[tuple[str, int, str], list[dict[str, object]]] = {}
    for row in predictions:
        pred_groups.setdefault((str(row["group"]), int(row["session_index"]), str(row["arm"])), []).append(row)
    for row in session:
        key = (str(row["group"]), int(row["session_index"]), str(row["arm"]))
        pred = pred_groups[key]
        y = np.asarray([int(r["observed_lick_onset"]) for r in pred], dtype=np.int8)
        p = np.asarray([float(r["predicted_probability"]) for r in pred], dtype=np.float64)
        row["sample_level_average_precision"] = (float(average_precision_score(y, p))
                                                  if np.unique(y).size == 2 else None)
    by_group: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in session:
        by_group.setdefault((str(row["group"]), str(row["arm"])), []).append(row)
    group_rows = []
    for (group, arm), rows in sorted(by_group.items()):
        gains = np.asarray([float(r["brier_gain_vs_time_history"]) for r in rows])
        ap_values = [float(r["sample_level_average_precision"]) for r in rows
                     if r["sample_level_average_precision"] is not None]
        group_rows.append({"group": group, "arm": arm, "n_sessions": len(rows),
                           "mean_session_brier": float(np.mean([float(r["mean_trial_brier"]) for r in rows])),
                           "mean_session_brier_gain_vs_time_history": float(gains.mean()),
                           "mean_session_average_precision": float(np.mean(ap_values)) if ap_values else None,
                           "sessions_with_positive_brier_gain": int(np.count_nonzero(gains > 0)),
                           "inference_scope": "descriptive sessions; animal ID unavailable"})
    return session, group_rows


def run(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {out}")
    out.mkdir(parents=True)
    started = time.time()
    pinned = {"raw": sha256(RAW), "manifest": sha256(ACQUISITION), "contract": sha256(CONTRACT),
              "runner": sha256(Path(__file__)), "source_helper": sha256(SOURCE_HELPER)}
    preflight_record = preflight()
    (out.parent / "PREFLIGHT.json").write_text(json.dumps(preflight_record, indent=2) + "\n")
    predictions: list[dict[str, object]] = []
    fit_rows: list[dict[str, object]] = []
    inventory: list[dict[str, object]] = []
    with h5py.File(RAW, "r") as h5:
        for group, gi, expected_delay, min_delay in GROUPS:
            for si, ref in enumerate(source.session_refs(h5, gi), start=1):
                s = source.h5_ref(h5, ref)
                all_n = int(s["rewarded"].size)
                all_trials = np.arange(all_n)
                valid_lick = lick_sensor_valid(s, source.vec(s, "tmpxx").astype(np.float64), all_trials)
                reward_all = source.vec(s, "rewarded").astype(bool)
                good = source.vec(s, "goodmvdir").astype(bool)
                mvlen = source.vec(s, "mvlen")
                delay = (source.vec(s, "rewtimes") - source.vec(s, "midpt")) * scalar(s, "dtb")
                min_keep = delay > min_delay
                keep = (((reward_all & good & min_keep)
                         | (~reward_all & good & (mvlen > 6) & min_keep)) & valid_lick)
                if "laser" in s["rewAlgn"]:
                    laser = read_behavior_trials(s, "rewAlgn", "laser", all_trials).T.astype(bool)
                    reward_axis = source.vec(s, "tmpxx").astype(np.float64)
                    laser_window = (reward_axis >= -2.0) & (reward_axis <= 2.0)
                    keep &= ~np.any(laser[laser_window], axis=0)
                trial_global = np.flatnonzero(keep)
                if len(trial_global) < FOLDS:
                    raise ValueError(f"too few eligible trials in {group} session {si}")
                samples = build_session_samples(s, trial_global, expected_delay)
                x_all = source.read_trials(s, "midAlgn", "sigFilt_GrC", trial_global)
                y_trial_reward = reward_all[trial_global]
                y_samples = samples["label"].astype(np.uint8)
                sample_trial = samples["trial"]
                sample_frames = samples["frame"]
                base_features = samples["base"]
                fold_assign = np.full(len(trial_global), -1, dtype=np.int16)
                random_state = SEED + gi * 100_000 + si
                class_counts = np.bincount(y_trial_reward.astype(np.int8), minlength=2)
                if np.count_nonzero(class_counts) == 2 and np.all(class_counts >= FOLDS):
                    splitter = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=random_state)
                    fold_iter = splitter.split(np.zeros(len(trial_global)), y_trial_reward)
                    split_method = "STRATIFIED_REWARD_STATUS"
                else:
                    splitter = KFold(n_splits=FOLDS, shuffle=True, random_state=random_state)
                    fold_iter = splitter.split(np.zeros(len(trial_global)))
                    split_method = "SHUFFLED_KFOLD_SMALL_CLASS"
                for fold, (_, test_local) in enumerate(fold_iter):
                    fold_assign[test_local] = fold
                inventory.append({"group": group, "session_index": si, "all_trials": all_n,
                                  "eligible_trials": int(len(trial_global)),
                                  "rewarded_trials": int(np.count_nonzero(y_trial_reward)),
                                  "omission_trials": int(np.count_nonzero(~y_trial_reward)),
                                  "candidate_time_samples": int(len(y_samples)),
                                  "grc_cells": int(x_all.shape[-1]),
                                  "animal_id_available": False, "fold_split_method": split_method})
                axis = source.vec(s, "tmpxCb").astype(np.float64)
                for fold in range(FOLDS):
                    train_local = np.flatnonzero(fold_assign != fold)
                    test_local = np.flatnonzero(fold_assign == fold)
                    train_sample = np.isin(sample_trial, train_local)
                    test_sample = np.isin(sample_trial, test_local)
                    base_train, base_test = base_features[train_sample], base_features[test_sample]
                    y_train, y_test = y_samples[train_sample], y_samples[test_sample]
                    train_trials = trial_global[train_local]
                    reward_train = train_local[y_trial_reward[train_local]]
                    reward_global = trial_global[reward_train]
                    if len(reward_global) < 3:
                        raise ValueError(f"too few training rewarded trials: {group} session {si} fold {fold}")
                    fold_probabilities: dict[str, np.ndarray] = {}
                    base_pred, base_status = fit_logistic_predict(base_train, y_train, base_test)
                    fold_probabilities["TIME_LICK_HISTORY"] = base_pred
                    fit_rows.append({"group": group, "session_index": si, "fold": fold,
                                     "arm": "TIME_LICK_HISTORY", "n_train_trials": len(train_local),
                                     "n_test_trials": len(test_local), "n_train_samples": len(y_train),
                                     "n_test_samples": len(y_test), "n_features": int(base_train.shape[1]),
                                     "fit_status": base_status, "training_event_fraction": float(y_train.mean())})

                    grc_reward = source.read_trials(s, "rewAlgn", "sigFilt_GrC", reward_global)
                    cf_reward = source.read_trials(s, "rewAlgn", "sp_CF", reward_global)
                    source_arms = (("CF_LTD", "source"), ("CF_NO_TRACE", "instant"),
                                   ("CF_EVENT_YOKED", "event_yoked"), ("CF_TIME_SHUFFLED", "time_shuffled"),
                                   ("CF_CELL_SHUFFLED", "source"))
                    neural_cache: dict[str, tuple[np.ndarray, dict[str, object]]] = {}
                    for arm_ix, (arm, mode) in enumerate(source_arms):
                        weights, meta = source.source_weights(grc_reward, cf_reward, axis, mode,
                                                              SEED + gi * 1_000_000 + si * 10_000 + fold * 100 + arm_ix)
                        if arm == "CF_CELL_SHUFFLED":
                            rng = np.random.default_rng(SEED + gi * 9_000_000 + si * 1000 + fold)
                            weights = weights[rng.permutation(len(weights))]
                        all_projection = np.einsum("ntc,c->nt", x_all.astype(np.float64), weights, optimize=False)
                        neural_cache[arm] = (all_projection[sample_trial, sample_frames, None], meta)

                    train_raw_rows = x_all[sample_trial[train_sample], sample_frames[train_sample], :].astype(np.float64)
                    test_raw_rows = x_all[sample_trial[test_sample], sample_frames[test_sample], :].astype(np.float64)
                    for arm in ("CF_LTD", "CF_NO_TRACE", "CF_EVENT_YOKED", "CF_TIME_SHUFFLED", "CF_CELL_SHUFFLED"):
                        neural_all, meta = neural_cache[arm]
                        x_train = np.column_stack((base_train, neural_all[train_sample]))
                        x_test = np.column_stack((base_test, neural_all[test_sample]))
                        pred, status = fit_logistic_predict(x_train, y_train, x_test)
                        fold_probabilities[arm] = pred
                        fit_rows.append({"group": group, "session_index": si, "fold": fold, "arm": arm,
                                         "n_train_trials": len(train_local), "n_test_trials": len(test_local),
                                         "n_train_samples": len(y_train), "n_test_samples": len(y_test),
                                         "n_features": int(x_train.shape[1]), "fit_status": status,
                                         "training_event_fraction": float(y_train.mean()), **meta})

                    pca = PCA(n_components=min(16, x_all.shape[-1], max(1, len(train_raw_rows) - 1)),
                              svd_solver="randomized", random_state=SEED, n_oversamples=10,
                              iterated_power=3)
                    pca.fit(train_raw_rows)
                    train_pc = pca.transform(train_raw_rows)
                    test_pc = pca.transform(test_raw_rows)
                    n_pc = int(train_pc.shape[1])
                    for arm, n_use in (("RAW_GRC_PC1", 1), ("RAW_GRC_PC16", n_pc)):
                        x_train = np.column_stack((base_train, train_pc[:, :n_use]))
                        x_test = np.column_stack((base_test, test_pc[:, :n_use]))
                        pred, status = fit_logistic_predict(x_train, y_train, x_test)
                        fold_probabilities[arm] = pred
                        fit_rows.append({"group": group, "session_index": si, "fold": fold, "arm": arm,
                                         "n_train_trials": len(train_local), "n_test_trials": len(test_local),
                                         "n_train_samples": len(y_train), "n_test_samples": len(y_test),
                                         "n_features": int(x_train.shape[1]), "pca_components": n_use,
                                         "fit_status": status, "training_event_fraction": float(y_train.mean())})

                    test_trial_ids = sample_trial[test_sample]
                    test_frames = sample_frames[test_sample]
                    test_times = axis[test_frames]
                    fold_keys = np.flatnonzero(test_sample)
                    for arm in ARMS:
                        probs = fold_probabilities[arm]
                        for j, sample_row in enumerate(fold_keys):
                            predictions.append({"group": group, "session_index": si, "fold": fold,
                                                "trial_index": int(trial_global[test_trial_ids[j]] + 1),
                                                "rewarded": int(y_trial_reward[test_trial_ids[j]]),
                                                "time_since_midpoint_s": float(test_times[j]),
                                                "observed_lick_onset": int(y_test[j]),
                                                "predicted_probability": float(probs[j]), "arm": arm})
                    print(f"{group}: session {si}, fold {fold}, trials={len(test_local)}, samples={len(y_test)}", flush=True)

    trial_rows, _ = _metric_rows(predictions)
    session_rows, group_rows = aggregate(trial_rows, predictions)
    write_csv(out / "heldout_predictions.csv", predictions)
    write_csv(out / "trial_scores.csv", trial_rows)
    write_csv(out / "fold_fit_manifest.csv", fit_rows)
    write_csv(out / "session_inventory.csv", inventory)
    write_csv(out / "session_summary.csv", session_rows)
    write_csv(out / "group_summary.csv", group_rows)
    summary = {"experiment": NAME, "classification": "retrospective exploratory within-session source-data analysis",
               "sessions": len(inventory), "eligible_trials": int(sum(r["eligible_trials"] for r in inventory)),
               "heldout_trial_time_predictions": len(predictions), "primary_metric": "mean trial-averaged held-out Brier score",
               "primary_contrast": "Brier(TIME_LICK_HISTORY) - Brier(CF_LTD), positive favors incremental CF-LTD association",
               "mean_session_brier_gain": {str(r["arm"]): float(r["mean_session_brier_gain_vs_time_history"])
                                           for r in group_rows if r["group"] == GROUPS[0][0]},
               "inference_scope": "session-descriptive; animal IDs unavailable; no session-level p-values or CIs",
               "interpretation": "predictive association only; not causal, measured synaptic weights, prospective closed-loop forecast, or AI benefit",
               "group_summary": group_rows}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if pinned != {"raw": sha256(RAW), "manifest": sha256(ACQUISITION), "contract": sha256(CONTRACT),
                  "runner": sha256(Path(__file__)), "source_helper": sha256(SOURCE_HELPER)}:
        raise RuntimeError("an input or code artifact changed during the run")
    output_meta = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
                   for p in sorted(out.iterdir()) if p.is_file()}
    manifest = {"experiment": NAME, "classification": summary["classification"],
                "started_unix": started, "finished_unix": time.time(),
                "duration_seconds": time.time() - started, "pinned_hashes": pinned,
                "author_source": preflight_record["author_source"], "python": platform.python_version(),
                "numpy": np.__version__, "scipy": scipy.__version__, "h5py": h5py.__version__,
                "sklearn": __import__("sklearn").__version__, "folds": FOLDS, "seed": SEED,
                "arms": list(ARMS), "label_window_s": [LABEL_START, LABEL_END],
                "censor_gap_s": CENSOR_GAP, "logistic_C": LOGISTIC_C, "max_iter": MAX_ITER,
                "output_files": output_meta}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": "COMPLETE", "output": str(out),
                      "sessions": len(inventory), "eligible_trials": summary["eligible_trials"],
                      "group_summary": group_rows}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), indent=2))
    else:
        run(args.output_dir)


if __name__ == "__main__":
    main()
