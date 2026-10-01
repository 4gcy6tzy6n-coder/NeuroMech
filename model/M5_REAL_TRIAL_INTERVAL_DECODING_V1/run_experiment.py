#!/usr/bin/env python3
"""Cross-validated prediction of measured single-trial reward delays from GrC traces."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M5_REAL_TRIAL_INTERVAL_DECODING_V1"
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
ACQUISITION = RAW.parent / "ACQUISITION_MANIFEST.json"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
DEFAULT_OUT = ROOT / "data/results" / NAME / "canonical"
GROUPS = (("1-s expert", 0), ("2-s novice / 1-s expert", 1), ("2-s expert", 2))
FOLDS = 5
SPLIT_SEED = 20261021
REWARD_WINDOW = (0.0, 0.25)
BASELINE_WINDOW = (-0.3, -0.025)
SOURCE_TWIN = (-3.0, 2.0)
ELIGIBILITY_WINDOW = (-0.15, -0.025)
INSTANT_WINDOW = "instant"
INPUT_WINDOW = (0.0, 0.80)
RIDGE_ALPHA = 10.0
N_PCS = 16
SOURCE_ARMS = ("BIO_CF_LTD", "BIO_NO_TRACE", "CF_EVENT_YOKED", "GRC_TIME_SHUFFLED", "CELL_SHUFFLED")
ARMS = SOURCE_ARMS + ("RAW_GRC_PCA16_RIDGE", "TRAINING_MEAN")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def matlab_round(x: np.ndarray | float) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64)
    return np.where(a >= 0, np.floor(a + 0.5), np.ceil(a - 0.5)).astype(int)


def h5_ref(h5: h5py.File, ref: h5py.Reference):
    if not ref:
        raise ValueError("unexpected null MATLAB object reference")
    return h5[ref]


def session_refs(h5: h5py.File, group_index: int) -> list[h5py.Reference]:
    cell = h5_ref(h5, h5["groups"][0, group_index])
    return [cell[0, i] for i in range(cell.shape[1])]


def vec(session: h5py.Group, name: str) -> np.ndarray:
    return np.asarray(session[name][()]).reshape(-1)


def scalar(session: h5py.Group, name: str) -> float:
    return float(np.asarray(session[name][()]).reshape(-1)[0])


def read_trials(session: h5py.Group, align: str, field: str, trial_indices: np.ndarray) -> np.ndarray:
    # The MATLAB v7.3 arrays are exposed time × cell × trial.
    return np.transpose(np.asarray(session[f"{align}/{field}"][:, :, trial_indices], dtype=np.float32), (2, 0, 1))


def preflight() -> dict[str, object]:
    groups = []
    with h5py.File(RAW, "r") as h5:
        if "groups" not in h5 or h5["groups"].shape != (1, 3):
            raise ValueError("unexpected Dryad MATLAB group schema")
        for label, gi in GROUPS:
            sessions = []
            for si, ref in enumerate(session_refs(h5, gi), start=1):
                s = h5_ref(h5, ref)
                required = ("dtb", "dtimCb", "tmpxCb", "rewarded", "goodmvdir", "mvlen", "rewtimes", "midpt", "rewAlgn", "midAlgn")
                absent = [key for key in required if key not in s]
                if absent:
                    raise ValueError(f"{label} session {si}: missing {absent}")
                for align in ("rewAlgn", "midAlgn"):
                    for field in ("sp_CF", "sigFilt_GrC"):
                        if field not in s[align]:
                            raise ValueError(f"{label} session {si}: missing {align}/{field}")
                delay = (vec(s, "rewtimes") - vec(s, "midpt")) * scalar(s, "dtb")
                keep = vec(s, "rewarded").astype(bool) & vec(s, "goodmvdir").astype(bool) & (vec(s, "mvlen") > 7)
                d = delay[keep]
                axis = vec(s, "tmpxCb").astype(np.float64)
                n_cells = int(s["midAlgn/sigFilt_GrC"].shape[1])
                if np.min(d) <= INPUT_WINDOW[1]:
                    raise ValueError(f"{label} session {si}: pre-reward input window overlaps reward onset")
                sessions.append({"session_index": si, "eligible_trials": int(len(d)), "grc_cells": n_cells,
                                 "cf_cells": int(s["rewAlgn/sp_CF"].shape[1]), "minimum_delay_s": float(d.min()),
                                 "maximum_delay_s": float(d.max()), "time_bins": int(len(axis)),
                                 "time_step_s": float(np.median(np.diff(axis)))})
            groups.append({"label": label, "session_count": len(sessions), "sessions": sessions})
    return {"experiment": NAME, "raw_sha256": sha256(RAW), "raw_bytes": RAW.stat().st_size,
            "acquisition_manifest_sha256": sha256(ACQUISITION), "groups": groups,
            "input_window_s": list(INPUT_WINDOW), "all_eligible_trials_end_after_input_window": True,
            "python": platform.python_version(), "numpy": np.__version__, "h5py": h5py.__version__}


def source_weights(grc: np.ndarray, cf: np.ndarray, axis: np.ndarray, mode: str,
                   seed: int) -> tuple[np.ndarray, dict[str, object]]:
    """Author-rule CF selection and GrC LTD weight fit using training-fold data only."""
    dt = float(np.median(np.diff(axis)))
    cf_for_fit = cf
    if mode == "event_yoked":
        cf_for_fit = cf[np.random.default_rng(seed).permutation(len(cf))]
    twin = np.flatnonzero((axis >= SOURCE_TWIN[0]) & (axis <= SOURCE_TWIN[1]))
    t_twin = axis[twin]
    reward_ix = np.flatnonzero((t_twin >= REWARD_WINDOW[0]) & (t_twin <= REWARD_WINDOW[1]))
    baseline_ix = np.flatnonzero((t_twin >= BASELINE_WINDOW[0]) & (t_twin <= BASELINE_WINDOW[1]))
    cf_twin = cf_for_fit[:, twin, :]
    selected = np.flatnonzero(cf_twin[:, reward_ix, :].mean(axis=(0, 1)) - cf_twin[:, baseline_ix, :].mean(axis=(0, 1)) > 0)
    if selected.size == 0:
        raise ValueError("no CF candidates in training fold")
    grc_twin = grc[:, twin, :].astype(np.float64, copy=True)
    if mode == "time_shuffled":
        for ti in range(grc_twin.shape[0]):
            for ci in range(grc_twin.shape[2]):
                grc_twin[ti, :, ci] = grc_twin[ti, rng.permutation(len(twin)), ci]
    scale = np.percentile(grc_twin.reshape(-1, grc_twin.shape[-1]), 95, axis=0)
    if np.any(~np.isfinite(scale)) or np.any(scale <= 0):
        raise ValueError("invalid training-fold GrC p95")
    if mode == "instant":
        offsets = np.asarray([0], dtype=int)
    else:
        lim = matlab_round(np.asarray(ELIGIBILITY_WINDOW) / dt)
        offsets = np.arange(int(lim[0]), int(lim[1]) + 1, dtype=int)
    full_to_local = {int(full): local for local, full in enumerate(twin)}
    cell_weights = []
    for cf_index in selected:
        eligible = np.zeros((len(grc), len(twin)), dtype=bool)
        for trial in range(len(grc)):
            events = np.flatnonzero((cf_for_fit[trial, :, cf_index] > 0) & (axis >= REWARD_WINDOW[0]) & (axis <= REWARD_WINDOW[1]))
            for event in events:
                for offset in offsets:
                    local = full_to_local.get(int(event + offset))
                    if local is not None:
                        eligible[trial, local] = True
        positive = np.maximum(grc_twin, 0.0)
        transformed = 1.0 / (1.0 + np.exp(-np.clip(positive / scale[None, None, :], -30.0, 30.0)))
        transformed = np.where(eligible[:, :, None], transformed, 0.5)
        mean_cell = transformed.mean(axis=(0, 1))
        denom = float(mean_cell.sum())
        if not math.isfinite(denom) or denom <= 0:
            raise ValueError("invalid source-rule weight normalizer")
        cell_weights.append((mean_cell - mean_cell.mean()) / denom)
    weights = -np.mean(np.stack(cell_weights), axis=0)
    return weights, {"n_cf_candidates": int(len(selected)), "offsets_frames": [int(v) for v in offsets],
                     "p95_min": float(scale.min()), "p95_max": float(scale.max())}


def ridge_fit_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, alpha: float = RIDGE_ALPHA) -> np.ndarray:
    mean = x_train.mean(axis=0)
    scale = x_train.std(axis=0)
    scale[scale < 1e-8] = 1.0
    z_train = (x_train - mean) / scale
    z_test = (x_test - mean) / scale
    y_mean = float(y_train.mean())
    gram = np.einsum("ni,nj->ij", z_train, z_train, optimize=False)
    rhs = np.einsum("ni,n->i", z_train, y_train - y_mean, optimize=False)
    beta = np.linalg.solve(gram + alpha * np.eye(gram.shape[0]), rhs)
    return y_mean + np.einsum("ni,i->n", z_test, beta, optimize=False)


def raw_pca_ridge(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, int]:
    flat_train = x_train.reshape(len(x_train), -1).astype(np.float64)
    flat_test = x_test.reshape(len(x_test), -1).astype(np.float64)
    mean = flat_train.mean(axis=0)
    scale = flat_train.std(axis=0)
    scale[scale < 1e-8] = 1.0
    z_train = (flat_train - mean) / scale
    z_test = (flat_test - mean) / scale
    _, _, vt = np.linalg.svd(z_train, full_matrices=False)
    n_components = min(N_PCS, max(1, len(x_train) - 1), vt.shape[0])
    basis = vt[:n_components]
    return ridge_fit_predict(z_train @ basis.T, y_train, z_test @ basis.T), n_components


def summarize_predictions(pred_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    session_rows: list[dict[str, object]] = []
    for (group, session, arm), rows in sorted(_group_by(pred_rows, ("group", "session_index", "arm")).items()):
        errors = np.asarray([float(r["absolute_error_s"]) for r in rows])
        base = np.asarray([float(r["baseline_absolute_error_s"]) for r in rows])
        session_rows.append({"group": group, "session_index": int(session), "arm": arm, "n_heldout_trials": len(rows),
                             "mean_absolute_error_s": float(errors.mean()), "median_absolute_error_s": float(np.median(errors)),
                             "training_mean_baseline_mae_s": float(base.mean()),
                             "mae_improvement_vs_training_mean_s": float(base.mean() - errors.mean()),
                             "fraction_baseline_mae_reduced": float((base.mean() - errors.mean()) / max(base.mean(), 1e-12))})
    group_rows = []
    for (group, arm), rows in sorted(_group_by(session_rows, ("group", "arm")).items()):
        vals = [float(r["mean_absolute_error_s"]) for r in rows]
        improvements = [float(r["mae_improvement_vs_training_mean_s"]) for r in rows]
        group_rows.append({"group": group, "arm": arm, "n_sessions": len(rows),
                           "mean_session_mae_s": float(np.mean(vals)), "median_session_mae_s": float(np.median(vals)),
                           "mean_session_improvement_vs_training_mean_s": float(np.mean(improvements)),
                           "sessions_improved_vs_training_mean": int(np.count_nonzero(np.asarray(improvements) > 0)),
                           "inference_scope": "descriptive sessions; animal IDs unavailable"})
    return session_rows, group_rows


def _group_by(rows: list[dict[str, object]], fields: tuple[str, ...]) -> dict[tuple[object, ...], list[dict[str, object]]]:
    out: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for row in rows:
        key = tuple(row[f] for f in fields)
        out.setdefault(key, []).append(row)
    return out


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    started = time.time()
    raw_hash, contract_hash = sha256(RAW), sha256(CONTRACT)
    predictions: list[dict[str, object]] = []
    fits: list[dict[str, object]] = []
    session_inventory: list[dict[str, object]] = []
    with h5py.File(RAW, "r") as h5:
        for group, gi in GROUPS:
            for si, ref in enumerate(session_refs(h5, gi), start=1):
                s = h5_ref(h5, ref)
                axis = vec(s, "tmpxCb").astype(np.float64)
                dtb = scalar(s, "dtb")
                target_all = (vec(s, "rewtimes") - vec(s, "midpt")) * dtb
                keep = vec(s, "rewarded").astype(bool) & vec(s, "goodmvdir").astype(bool) & (vec(s, "mvlen") > 7)
                trials = np.flatnonzero(keep)
                y = target_all[trials].astype(np.float64)
                input_mask = (axis >= INPUT_WINDOW[0]) & (axis <= INPUT_WINDOW[1])
                if not input_mask.any() or float(y.min()) <= INPUT_WINDOW[1]:
                    raise ValueError(f"pre-reward input window not valid in {group} session {si}")
                mid_all = read_trials(s, "midAlgn", "sigFilt_GrC", trials)[:, input_mask, :]
                rew_all = read_trials(s, "rewAlgn", "sigFilt_GrC", trials)
                cf_all = read_trials(s, "rewAlgn", "sp_CF", trials)
                if len(trials) < FOLDS * 3:
                    raise ValueError(f"too few eligible trials in {group} session {si}")
                split_rng = np.random.default_rng(SPLIT_SEED + gi * 100_000 + si)
                order = split_rng.permutation(len(trials))
                folds = np.empty(len(trials), dtype=int)
                for fold_ix, indices in enumerate(np.array_split(order, FOLDS)):
                    folds[indices] = fold_ix
                session_inventory.append({"group": group, "session_index": si, "eligible_trials": int(len(trials)),
                                          "target_mean_s": float(y.mean()), "target_sd_s": float(y.std(ddof=1)),
                                          "target_min_s": float(y.min()), "target_max_s": float(y.max()),
                                          "input_window_s": list(INPUT_WINDOW), "grc_cells": int(mid_all.shape[-1])})
                for fold in range(FOLDS):
                    train_ix, test_ix = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
                    x_train, x_test = mid_all[train_ix], mid_all[test_ix]
                    y_train, y_test = y[train_ix], y[test_ix]
                    source_fits: dict[str, tuple[np.ndarray, dict[str, object]]] = {}
                    for ai, arm in enumerate(SOURCE_ARMS):
                        mode = {"BIO_CF_LTD": "source", "BIO_NO_TRACE": "instant", "CF_EVENT_YOKED": "event_yoked",
                                "GRC_TIME_SHUFFLED": "time_shuffled", "CELL_SHUFFLED": "source"}[arm]
                        w, meta = source_weights(rew_all[train_ix], cf_all[train_ix], axis, mode,
                                                 SPLIT_SEED + gi * 1_000_000 + si * 10_000 + fold * 100 + ai)
                        if arm == "CELL_SHUFFLED":
                            w = w[np.random.default_rng(SPLIT_SEED + gi * 9_000_000 + si * 1000 + fold).permutation(len(w))]
                        source_fits[arm] = (w, meta)
                        signal_train = np.einsum("ntc,c->nt", x_train.astype(np.float64), w, optimize=False)
                        signal_test = np.einsum("ntc,c->nt", x_test.astype(np.float64), w, optimize=False)
                        pred = ridge_fit_predict(signal_train, y_train, signal_test)
                        fits.append({"group": group, "session_index": si, "fold": fold, "arm": arm,
                                     "n_train": len(train_ix), "n_test": len(test_ix), **meta})
                        for ix, yt, yp in zip(test_ix, y_test, pred):
                            predictions.append(_prediction_row(group, si, fold, int(trials[ix]), arm, float(yt), float(yp), float(y_train.mean())))
                    raw_pred, n_pc = raw_pca_ridge(x_train, y_train, x_test)
                    fits.append({"group": group, "session_index": si, "fold": fold, "arm": "RAW_GRC_PCA16_RIDGE",
                                 "n_train": len(train_ix), "n_test": len(test_ix), "n_components": n_pc})
                    mean_pred = np.full(len(test_ix), float(y_train.mean()))
                    for ix, yt, yp in zip(test_ix, y_test, raw_pred):
                        predictions.append(_prediction_row(group, si, fold, int(trials[ix]), "RAW_GRC_PCA16_RIDGE", float(yt), float(yp), float(y_train.mean())))
                    for ix, yt, yp in zip(test_ix, y_test, mean_pred):
                        predictions.append(_prediction_row(group, si, fold, int(trials[ix]), "TRAINING_MEAN", float(yt), float(yp), float(y_train.mean())))
                print(f"{group}: session {si}, n={len(trials)} trials", flush=True)

    session_rows, group_rows = summarize_predictions(predictions)
    write_csv(out / "heldout_predictions.csv", predictions)
    write_csv(out / "fold_fit_manifest.csv", fits)
    write_csv(out / "session_inventory.csv", session_inventory)
    write_csv(out / "session_summary.csv", session_rows)
    write_csv(out / "group_summary.csv", group_rows)
    summary = {"experiment": NAME, "classification": "retrospective exploratory source-data reanalysis",
               "n_predictions": len(predictions), "n_session_folds": len(fits), "n_sessions": len(session_inventory),
               "independent_unit_limit": "animal IDs unavailable; report sessions descriptively",
               "primary_metric": "out-of-fold mean absolute error in measured reward delay, seconds",
               "group_summary": group_rows,
               "interpretation": "No biological causality, animal-level generalization, or AI transfer claim."}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if sha256(RAW) != raw_hash or sha256(CONTRACT) != contract_hash:
        raise RuntimeError("pinned input or contract changed during run")
    outputs = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(out.iterdir()) if p.is_file()}
    manifest = {"experiment": NAME, "classification": summary["classification"], "started_unix": started,
                "finished_unix": time.time(), "duration_seconds": time.time() - started,
                "raw_sha256": raw_hash, "acquisition_manifest_sha256": sha256(ACQUISITION),
                "contract_sha256": contract_hash, "runner_sha256": sha256(Path(__file__)),
                "python": platform.python_version(), "numpy": np.__version__, "h5py": h5py.__version__,
                "folds": FOLDS, "seed": SPLIT_SEED, "input_window_s": list(INPUT_WINDOW), "outputs": outputs}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": "COMPLETE", "output": str(out), "n_predictions": len(predictions),
                      "n_sessions": len(session_inventory), "group_summary": group_rows}, indent=2))


def _prediction_row(group: str, session: int, fold: int, source_trial: int, arm: str,
                    target: float, prediction: float, train_mean: float) -> dict[str, object]:
    return {"group": group, "session_index": session, "fold": fold, "source_trial_index": source_trial + 1,
            "arm": arm, "target_delay_s": target, "predicted_delay_s": prediction,
            "absolute_error_s": abs(prediction - target), "baseline_absolute_error_s": abs(train_mean - target)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.preflight:
        record = preflight()
        record.update({"contract_sha256": sha256(CONTRACT), "runner_sha256": sha256(Path(__file__)),
                       "output_dir": str(DEFAULT_OUT.relative_to(ROOT))})
        print(json.dumps(record, indent=2))
    else:
        run(args.output_dir)


if __name__ == "__main__":
    main()
