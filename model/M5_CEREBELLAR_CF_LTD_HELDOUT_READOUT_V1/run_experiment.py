#!/usr/bin/env python3
"""Evaluate author-code CF-timed GrC LTD weights on held-out source trials."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = "M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1"
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
ACQUISITION = RAW.parent / "ACQUISITION_MANIFEST.json"
CONTRACT = ROOT / "summery" / EXPERIMENT / "CONTRACT.md"
DEFAULT_OUT = ROOT / "data/results" / EXPERIMENT
GROUPS = (
    ("1-s expert", 0),
    ("2-s novice / 1-s expert", 1),
    ("2-s expert", 2),
)
N_SPLITS = 5
SPLIT_SEED = 20261001
REWARD_WINDOW = (0.0, 0.25)
BASELINE_WINDOW = (-0.3, -0.025)
ELIGIBILITY_WINDOW = (-0.15, -0.025)
SOURCE_TWIN = (-3.0, 2.0)
EVAL_MAX_S = 2.0
RIDGE_ALPHA = 1.0
METHODS = ("CF_LTD", "UNIFORM", "CELL_SHUFFLED", "CF_TIME_SHUFFLED", "RIDGE_REFERENCE")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matlab_round(values: np.ndarray | float) -> np.ndarray:
    """MATLAB round: ties away from zero (unlike NumPy's bankers' rounding)."""
    x = np.asarray(values, dtype=np.float64)
    return np.where(x >= 0, np.floor(x + 0.5), np.ceil(x - 0.5)).astype(int)


def h5_ref(h5: h5py.File, ref: h5py.Reference):
    if not ref:
        raise ValueError("unexpected null MATLAB object reference")
    return h5[ref]


def group_sessions(h5: h5py.File, group_index: int) -> list[h5py.Reference]:
    cell = h5_ref(h5, h5["groups"][0, group_index])
    return [cell[0, i] for i in range(cell.shape[1])]


def scalar(session: h5py.Group, field: str) -> float:
    return float(np.asarray(session[field][()]).reshape(-1)[0])


def vector(session: h5py.Group, field: str) -> np.ndarray:
    return np.asarray(session[field][()]).reshape(-1)


def preflight(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    record: dict[str, object] = {
        "experiment_id": EXPERIMENT,
        "raw_path_relative": str(path.relative_to(ROOT)),
        "raw_bytes": path.stat().st_size,
        "raw_sha256": sha256(path),
        "groups": [],
    }
    with h5py.File(path, "r") as h5:
        if "groups" not in h5 or h5["groups"].shape != (1, 3):
            raise ValueError("unexpected MATLAB groups schema")
        for label, gi in GROUPS:
            sessions = group_sessions(h5, gi)
            shapes = []
            for si, ref in enumerate(sessions, start=1):
                session = h5_ref(h5, ref)
                required = (
                    "dtb", "dtimCb", "tmpxCb", "rewarded", "goodmvdir", "mvlen",
                    "rewtimes", "midpt", "rewAlgn", "midAlgn",
                )
                absent = [field for field in required if field not in session]
                if absent:
                    raise ValueError(f"{label} session {si} missing fields: {absent}")
                for align in ("rewAlgn", "midAlgn"):
                    for field in ("sp_CF", "sigFilt_GrC"):
                        if field not in session[align]:
                            raise ValueError(f"{label} session {si} missing {align}/{field}")
                n_trials = len(vector(session, "rewarded"))
                shape = tuple(int(v) for v in session["rewAlgn/sigFilt_GrC"].shape)
                if shape[0] != len(vector(session, "tmpxCb")) or shape[2] != n_trials:
                    raise ValueError(f"{label} session {si}: unexpected time/trial dimensions {shape}")
                shapes.append({
                    "session_index": si,
                    "timepoints": shape[0],
                    "grc_cells": shape[1],
                    "cf_cells": int(session["rewAlgn/sp_CF"].shape[1]),
                    "trials": n_trials,
                    "dtimCb_seconds": scalar(session, "dtimCb"),
                })
            record["groups"].append({"label": label, "session_count": len(sessions), "sessions": shapes})
    return record


def read_aligned(session: h5py.Group, align: str, field: str, trial_indices: np.ndarray) -> np.ndarray:
    # MATLAB v7.3 arrays are exposed as time × cell × trial.
    data = np.asarray(session[f"{align}/{field}"][:, :, trial_indices], dtype=np.float32)
    return np.transpose(data, (2, 0, 1))


def corr_r2(values: np.ndarray, times: np.ndarray) -> tuple[float, float]:
    if values.size < 3 or not np.isfinite(values).all() or np.ptp(values) <= 1e-12:
        return float("nan"), float("nan")
    r = float(np.corrcoef(values, times)[0, 1])
    if not math.isfinite(r):
        return float("nan"), float("nan")
    return r, r * r


def source_ltd_weights(
    grc: np.ndarray,
    cf_spikes: np.ndarray,
    time_axis: np.ndarray,
    dt: float,
    rng: np.random.Generator,
    shuffle_grc_time: bool = False,
) -> tuple[np.ndarray, int, dict[str, object]]:
    """Mirror author LTD transform/centering, fitting from training trials only."""
    twin_ix = np.flatnonzero((time_axis >= SOURCE_TWIN[0]) & (time_axis <= SOURCE_TWIN[1]))
    twin_t = time_axis[twin_ix]
    reward_ix = np.flatnonzero((twin_t >= REWARD_WINDOW[0]) & (twin_t <= REWARD_WINDOW[1]))
    baseline_ix = np.flatnonzero((twin_t >= BASELINE_WINDOW[0]) & (twin_t <= BASELINE_WINDOW[1]))
    if not reward_ix.size or not baseline_ix.size:
        raise ValueError("reward or baseline CF window has no imaging samples")

    # Training arrays are trials × time × cells. Author code chooses CFs from the
    # mean reward response minus mean pre-reward baseline response.
    cf_twin = cf_spikes[:, twin_ix, :]
    cf_response = cf_twin[:, reward_ix, :].mean(axis=(0, 1))
    cf_baseline = cf_twin[:, baseline_ix, :].mean(axis=(0, 1))
    selected = np.flatnonzero((cf_response - cf_baseline) > 0.0)
    if selected.size == 0:
        return np.empty(grc.shape[2], dtype=np.float64), 0, {"selected_cf_indices": []}
    cf_twin = cf_twin[:, :, selected]

    grc_twin = grc[:, twin_ix, :].astype(np.float64, copy=True)
    if shuffle_grc_time:
        for trial in range(grc_twin.shape[0]):
            for cell in range(grc_twin.shape[2]):
                grc_twin[trial, :, cell] = grc_twin[trial, rng.permutation(grc_twin.shape[1]), cell]

    scale = np.percentile(grc_twin.reshape(-1, grc_twin.shape[-1]), 95, axis=0)
    if np.any(~np.isfinite(scale)) or np.any(scale <= 0):
        raise ValueError("author logistic scale has a non-positive or non-finite GrC p95")

    offsets = matlab_round(np.asarray(ELIGIBILITY_WINDOW) / dt)
    # The source uses winfnz, an inclusive integer range in frame offsets.
    offsets = np.arange(int(offsets[0]), int(offsets[1]) + 1, dtype=int)
    full_to_twin = {int(full): local for local, full in enumerate(twin_ix)}
    weights_by_cf = []
    for local_cf, original_cf in enumerate(selected):
        eligibility = np.zeros((grc.shape[0], len(twin_ix)), dtype=bool)
        for trial in range(grc.shape[0]):
            event_full = np.flatnonzero(
                (cf_spikes[trial, :, original_cf] > 0)
                & (time_axis >= REWARD_WINDOW[0])
                & (time_axis <= REWARD_WINDOW[1])
            )
            for event in event_full:
                for offset in offsets:
                    local = full_to_twin.get(int(event + offset))
                    if local is not None:
                        eligibility[trial, local] = True

        # Noneligible entries are sigmoid(0) = 0.5 in the source code.
        positive = np.maximum(grc_twin, 0.0)
        z = np.clip(positive / scale[None, None, :], -30.0, 30.0)
        transformed = 1.0 / (1.0 + np.exp(-z))
        cf_elig = eligibility[:, :, None]
        transformed = np.where(cf_elig, transformed, 0.5)
        mean_by_cell = transformed.mean(axis=(0, 1))
        denominator = float(mean_by_cell.sum())
        if not math.isfinite(denominator) or denominator <= 0:
            raise ValueError("source per-CF weight normalization is degenerate")
        weights_by_cf.append((mean_by_cell - mean_by_cell.mean()) / denominator)

    source_weight = -np.mean(np.stack(weights_by_cf, axis=0), axis=0)
    return source_weight, int(selected.size), {
        "selected_cf_indices": [int(i) for i in selected],
        "eligibility_offsets_frames": [int(v) for v in offsets],
        "grc_p95_min": float(scale.min()),
        "grc_p95_max": float(scale.max()),
    }


def ridge_reference_weights(x: np.ndarray, y: np.ndarray, alpha: float = RIDGE_ALPHA) -> tuple[np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-8] = 1.0
    z = (x - mean) / scale
    y_mean = float(y.mean())
    yc = y - y_mean
    # Use explicit contractions instead of the platform BLAS matmul path. On
    # this host the first run emitted overflow/divide warnings for finite, small
    # matrix operands; the explicit path is warning-free and reproducible.
    gram = np.einsum("ni,nj->ij", z, z, optimize=False)
    rhs = np.einsum("ni,n->i", z, yc, optimize=False)
    beta = np.linalg.solve(gram + alpha * np.eye(gram.shape[0]), rhs)
    raw_weights = beta / scale
    return raw_weights, np.asarray([y_mean - float(np.sum(mean * raw_weights))])


def evaluate_session(
    h5: h5py.File,
    group_label: str,
    group_index: int,
    session_index: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    session = h5_ref(h5, group_sessions(h5, group_index)[session_index])
    time_axis = vector(session, "tmpxCb").astype(np.float64)
    dt = scalar(session, "dtimCb")
    dtb = scalar(session, "dtb")
    rewarded = vector(session, "rewarded").astype(bool)
    good = vector(session, "goodmvdir").astype(bool)
    mvlen = vector(session, "mvlen")
    delay = (vector(session, "rewtimes") - vector(session, "midpt")) * dtb
    eligible_trials = np.flatnonzero(rewarded & good & (mvlen > 7))
    if eligible_trials.size < 6:
        return [], [], [], [{"group": group_label, "session_index": session_index + 1,
                             "status": "SKIPPED_TOO_FEW_ELIGIBLE_TRIALS", "n_eligible_trials": int(eligible_trials.size)}]

    # Read only the required aligned traces, then keep the trial split identical
    # across all interventions and readout controls.
    rew_grc_all = read_aligned(session, "rewAlgn", "sigFilt_GrC", eligible_trials)
    rew_cf_all = read_aligned(session, "rewAlgn", "sp_CF", eligible_trials)
    mid_grc_all = read_aligned(session, "midAlgn", "sigFilt_GrC", eligible_trials)
    trial_rows: list[dict[str, object]] = []
    weight_rows: list[dict[str, object]] = []
    split_rows: list[dict[str, object]] = []
    n_cells = rew_grc_all.shape[-1]
    for split in range(N_SPLITS):
        seed = SPLIT_SEED + group_index * 100_000 + session_index * 1_000 + split
        rng = np.random.default_rng(seed)
        order = rng.permutation(len(eligible_trials))
        n_train = len(order) // 2
        train_ix, test_ix = order[:n_train], order[n_train:]
        source_weights, n_cfs, weight_meta = source_ltd_weights(
            rew_grc_all[train_ix], rew_cf_all[train_ix], time_axis, dt, rng, shuffle_grc_time=False
        )
        if n_cfs == 0:
            split_rows.append({"group": group_label, "session_index": session_index + 1,
                               "split": split + 1, "seed": seed,
                               "status": "NO_TRAINING_CF_CANDIDATES", "n_train": len(train_ix),
                               "n_test": len(test_ix), "n_selected_cf": 0})
            continue
        time_shuf_weights, time_shuf_cfs, time_meta = source_ltd_weights(
            rew_grc_all[train_ix], rew_cf_all[train_ix], time_axis,
            dt, np.random.default_rng(seed + 11_000_000), shuffle_grc_time=True,
        )
        if time_shuf_cfs == 0:
            raise RuntimeError("CF-time shuffle changed CF selection; selection must be common across arms")
        perm = np.random.default_rng(seed + 21_000_000).permutation(n_cells)
        shuffled_weights = source_weights[perm]
        uniform_weights = np.full(n_cells, 1.0 / n_cells, dtype=np.float64)

        train_samples, train_targets = [], []
        for ix in train_ix:
            actual_delay = float(delay[eligible_trials[ix]])
            keep = (time_axis >= 0) & (time_axis <= min(actual_delay, EVAL_MAX_S))
            if np.count_nonzero(keep) >= 3:
                train_samples.append(mid_grc_all[ix, keep, :].astype(np.float64))
                train_targets.append(time_axis[keep])
        ridge_weights = None
        ridge_intercept = None
        if train_samples:
            ridge_weights, ridge_intercept = ridge_reference_weights(
                np.concatenate(train_samples), np.concatenate(train_targets)
            )

        for cell, w in enumerate(source_weights):
            weight_rows.append({"group": group_label, "session_index": session_index + 1,
                                "split": split + 1, "training_seed": seed,
                                "cell_index": cell + 1, "source_ltd_weight": float(w),
                                "cell_shuffled_weight": float(shuffled_weights[cell]),
                                "cf_time_shuffled_weight": float(time_shuf_weights[cell])})
        for test_pos in test_ix:
            original_trial = int(eligible_trials[test_pos])
            actual_delay = float(delay[original_trial])
            keep = (time_axis >= 0) & (time_axis <= min(actual_delay, EVAL_MAX_S))
            t = time_axis[keep]
            x = mid_grc_all[test_pos, keep, :].astype(np.float64)
            if t.size < 3:
                continue
            readouts = {
                "CF_LTD": np.einsum("ij,j->i", x, source_weights, optimize=False),
                "UNIFORM": np.einsum("ij,j->i", x, uniform_weights, optimize=False),
                "CELL_SHUFFLED": np.einsum("ij,j->i", x, shuffled_weights, optimize=False),
                "CF_TIME_SHUFFLED": np.einsum("ij,j->i", x, time_shuf_weights, optimize=False),
            }
            if ridge_weights is not None and ridge_intercept is not None:
                readouts["RIDGE_REFERENCE"] = np.einsum("ij,j->i", x, ridge_weights, optimize=False) + float(ridge_intercept[0])
            else:
                readouts["RIDGE_REFERENCE"] = np.full(len(t), np.nan)
            for method in METHODS:
                r, r2 = corr_r2(readouts[method], t)
                trial_rows.append({
                    "group": group_label, "session_index": session_index + 1,
                    "split": split + 1, "split_seed": seed,
                    "source_trial_index": original_trial + 1,
                    "method": method, "reward_delay_s": actual_delay,
                    "n_eval_frames": int(t.size), "pearson_r": r, "r_squared": r2,
                })
        for method in METHODS:
            vals = [r["r_squared"] for r in trial_rows
                    if r["group"] == group_label and r["session_index"] == session_index + 1
                    and r["split"] == split + 1 and r["method"] == method
                    and isinstance(r["r_squared"], float) and math.isfinite(r["r_squared"])]
            split_rows.append({
                "group": group_label, "session_index": session_index + 1,
                "split": split + 1, "seed": seed, "method": method,
                "status": "OK", "n_train": len(train_ix), "n_test": len(test_ix),
                "n_selected_cf": n_cfs,
                "mean_test_trial_r2": float(np.mean(vals)) if vals else float("nan"),
                "median_test_trial_r2": float(np.median(vals)) if vals else float("nan"),
            })
    return trial_rows, split_rows, weight_rows, []


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize(split_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    session_rows: list[dict[str, object]] = []
    grouped: dict[tuple[str, int, str], list[float]] = {}
    for row in split_rows:
        value = row.get("mean_test_trial_r2")
        if row.get("status") != "OK" or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            continue
        key = (str(row["group"]), int(row["session_index"]), str(row["method"]))
        grouped.setdefault(key, []).append(float(value))
    group_means: dict[tuple[str, str], list[float]] = {}
    for (group, session, method), values in sorted(grouped.items()):
        session_mean = float(np.mean(values))
        session_rows.append({"group": group, "session_index": session, "method": method,
                             "n_valid_splits": len(values), "mean_split_trial_r2": session_mean})
        group_means.setdefault((group, method), []).append(session_mean)
    summary_groups = []
    for (group, method), values in sorted(group_means.items()):
        summary_groups.append({"group": group, "method": method,
                               "n_sessions": len(values), "mean_session_r2": float(np.mean(values)),
                               "median_session_r2": float(np.median(values)),
                               "min_session_r2": float(np.min(values)),
                               "max_session_r2": float(np.max(values))})
    summary = {
        "classification": "post-result exploratory, descriptive source-data reanalysis",
        "primary_metric": "held-out per-trial Pearson correlation squared, averaged within split then session",
        "inference": "descriptive only; no session-as-animal assumption, p-values, or animal-level intervals",
        "groups": summary_groups,
        "split_status_counts": {},
    }
    for status in sorted({str(row.get("status")) for row in split_rows}):
        summary["split_status_counts"][status] = sum(row.get("status") == status for row in split_rows)
    return session_rows, summary


def run(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output}")
    output.mkdir(parents=True)
    started = time.time()
    source = preflight(RAW)
    contract_hash = sha256(CONTRACT)
    raw_hash = sha256(RAW)
    rows_trial: list[dict[str, object]] = []
    rows_split: list[dict[str, object]] = []
    rows_weight: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    with h5py.File(RAW, "r") as h5:
        for group_label, group_index in GROUPS:
            for session_index, _ in enumerate(group_sessions(h5, group_index)):
                trials, splits, weights, session_skips = evaluate_session(h5, group_label, group_index, session_index)
                rows_trial.extend(trials)
                rows_split.extend(splits)
                rows_weight.extend(weights)
                skipped.extend(session_skips)
                skipped.extend(row for row in splits if row.get("status") != "OK")
                print(f"{group_label}: session {session_index + 1}, splits={len(splits)}, trial rows={len(trials)}", flush=True)
    session_rows, summary = summarize(rows_split)
    summary["skipped_sessions"] = skipped
    summary["preflight_group_sessions"] = [
        {"group": g["label"], "n_sessions": g["session_count"]} for g in source["groups"]
    ]
    summary["trial_rows"] = len(rows_trial)
    summary["split_rows"] = len(rows_split)
    write_csv(output / "heldout_trial_results.csv", rows_trial)
    write_csv(output / "session_split_results.csv", rows_split)
    write_csv(output / "session_summary.csv", session_rows)
    write_csv(output / "ltd_weights.csv", rows_weight)
    (output / "preflight_schema.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if sha256(RAW) != raw_hash or sha256(CONTRACT) != contract_hash:
        raise RuntimeError("pinned raw input or contract changed during the run")
    files = {}
    for path in sorted(output.iterdir()):
        if path.is_file():
            files[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    manifest = {
        "experiment_id": EXPERIMENT,
        "classification": "post-result exploratory, descriptive source-data reanalysis",
        "started_unix": started,
        "finished_unix": time.time(),
        "duration_seconds": time.time() - started,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "h5py": h5py.__version__,
        "runner_sha256": sha256(Path(__file__)),
        "contract_sha256": contract_hash,
        "author_source_repository": "https://github.com/wagnerlabnih/garcia-garcia-neuron-2024",
        "author_source_commit": "124c83e1af83e9680e05f9827448579d02345fa3",
        "acquisition_manifest_sha256": sha256(ACQUISITION),
        "raw_sha256": raw_hash,
        "raw_sha256_matches_dryad": raw_hash == json.loads(ACQUISITION.read_text())["files"][0]["dryad_sha256"],
        "randomization": {"n_splits_per_session": N_SPLITS, "seed_formula": "20261001 + group_index*100000 + session_index*1000 + split_index"},
        "outputs": files,
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": summary}, indent=2, allow_nan=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--preflight", action="store_true", help="check fields, shapes, hashes; do not calculate outcomes")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(RAW), indent=2))
        return
    run(args.output_dir)


if __name__ == "__main__":
    main()
