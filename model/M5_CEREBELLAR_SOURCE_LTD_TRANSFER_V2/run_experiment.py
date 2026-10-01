#!/usr/bin/env python3
"""Transfer the source-defined CF-timed LTD rule to a paired artificial interval task."""
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
EXP = "M5_CEREBELLAR_SOURCE_LTD_TRANSFER_V2"
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
ACQUISITION = RAW.parent / "ACQUISITION_MANIFEST.json"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
DEFAULT_OUT = ROOT / "data/results" / EXP
GRID = np.linspace(0.0, 2.4, 81, dtype=np.float64)
DT = float(GRID[1] - GRID[0])
GROUPS = (("1-s expert", 0, 0.75), ("2-s expert", 2, 1.75))
N_PER_GROUP = 32
SEEDS = tuple(range(6100, 6112))
NTRAIN = 1800
NTEST = 500
BOOTSTRAPS = 20_000
BOOT_SEED = 20261014
SPLIT_WIN = (-0.15, -0.025)
RIDGE_ALPHA = 1.0
ARMS = ("BIO_CF_LTD", "BIO_NO_TRACE", "BIO_CF_TIME_SHUFFLED", "BIO_CELL_SHUFFLED",
        "GENERIC_RBF_CF_LTD", "SHUFFLED_BIO_CF_LTD", "UNIFORM_POOL", "EMPIRICAL_TIMER")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
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


def vec(s: h5py.Group, name: str) -> np.ndarray:
    return np.asarray(s[name][()]).reshape(-1)


def source_profiles() -> tuple[np.ndarray, list[dict[str, object]]]:
    profiles: list[np.ndarray] = []
    metadata: list[dict[str, object]] = []
    with h5py.File(RAW, "r") as h5:
        for group_label, group_index, delay_threshold in GROUPS:
            for session_index, ref in enumerate(session_refs(h5, group_index), start=1):
                s = h5_ref(h5, ref)
                axis = vec(s, "tmpxCb").astype(np.float64)
                dtb = float(np.asarray(s["dtb"][()]).reshape(-1)[0])
                delay = (vec(s, "rewtimes") - vec(s, "midpt")) * dtb
                keep = (vec(s, "rewarded").astype(bool) & vec(s, "goodmvdir").astype(bool)
                        & (delay > delay_threshold))
                trials = np.flatnonzero(keep)
                if not trials.size:
                    continue
                # MATLAB v7.3 arrays are time × cell × trial.
                x = np.asarray(s["midAlgn/sigFilt_GrC"][:, :, trials], dtype=np.float32)
                mean_x = x.mean(axis=2, dtype=np.float64).T
                baseline = (axis >= -1.0) & (axis <= 0.0)
                window = (axis >= 0.0) & (axis <= 2.0)
                positive = np.maximum(mean_x[:, window] - mean_x[:, baseline].mean(axis=1, keepdims=True), 0.0)
                peaks = positive.max(axis=1, keepdims=True)
                valid = peaks[:, 0] > 1e-12
                normalized = positive[valid] / peaks[valid]
                cell_indices = np.flatnonzero(valid)
                for cell_index, row in zip(cell_indices, normalized):
                    profiles.append(np.interp(GRID, axis[window], row, left=0.0, right=0.0).astype(np.float32))
                    metadata.append({"source_group": group_label, "source_group_index": group_index,
                                     "session_index": session_index, "cell_index": int(cell_index + 1),
                                     "eligible_reward_trials": int(trials.size)})
    return np.asarray(profiles, dtype=np.float32), metadata


def choose_bio_basis() -> tuple[np.ndarray, list[dict[str, object]]]:
    profiles, meta = source_profiles()
    chosen: list[int] = []
    for group_label, _, _ in GROUPS:
        ix = np.flatnonzero([m["source_group"] == group_label for m in meta])
        if len(ix) < N_PER_GROUP:
            raise ValueError(f"only {len(ix)} usable profiles for {group_label}; need {N_PER_GROUP}")
        positions = np.linspace(0, len(ix) - 1, N_PER_GROUP).round().astype(int)
        chosen.extend(ix[positions].tolist())
    selected = np.asarray(chosen, dtype=int)
    return profiles[selected].T, [meta[i] for i in selected]


def generic_rbf() -> np.ndarray:
    centers = np.linspace(0.0, 2.0, 64)
    width = 0.11
    return np.exp(-0.5 * ((GRID[:, None] - centers[None, :]) / width) ** 2).astype(np.float32)


def episode(rng: np.random.Generator, cue: int, interval: float, basis: np.ndarray):
    target = float(np.clip(interval + rng.uniform(-0.15, 0.15), 0.3, 2.25))
    noise = rng.normal(0.0, 0.025, basis.shape).astype(np.float32)
    return basis + noise, target, noise


def source_ltd_fit(
    features: np.ndarray,
    targets: np.ndarray,
    rng: np.random.Generator,
    event_mode: str,
) -> tuple[np.ndarray, dict[str, object]]:
    """Apply the source logistic, event-triggered eligibility, centering and LTD sign."""
    if features.ndim != 3 or features.shape[1] != len(GRID):
        raise ValueError(f"expected trials × {len(GRID)} × cells, got {features.shape}")
    events = targets.copy()
    if event_mode == "permuted":
        events = rng.permutation(events)
    event_bins = np.argmin(np.abs(GRID[None, :] - events[:, None]), axis=1)
    scale = np.percentile(features.reshape(-1, features.shape[-1]), 95, axis=0)
    if np.any(~np.isfinite(scale)) or np.any(scale <= 0):
        raise ValueError("nonpositive or nonfinite training p95 scale")
    eligible = np.zeros(features.shape[:2], dtype=bool)
    if event_mode == "instant":
        offsets = np.array([0], dtype=int)
    else:
        limits = matlab_round(np.asarray(SPLIT_WIN) / DT)
        offsets = np.arange(int(limits[0]), int(limits[1]) + 1, dtype=int)
    for trial, event_bin in enumerate(event_bins):
        bins = event_bin + offsets
        bins = bins[(bins >= 0) & (bins < len(GRID))]
        eligible[trial, bins] = True
    positive = np.maximum(features.astype(np.float64), 0.0)
    z = np.clip(positive / scale[None, None, :], -30.0, 30.0)
    transformed = 1.0 / (1.0 + np.exp(-z))
    transformed = np.where(eligible[:, :, None], transformed, 0.5)
    mean_by_cell = transformed.mean(axis=(0, 1))
    denominator = float(mean_by_cell.sum())
    if not math.isfinite(denominator) or denominator <= 0:
        raise ValueError("degenerate LTD weight normalization")
    weights = -(mean_by_cell - mean_by_cell.mean()) / denominator
    if not np.isfinite(weights).all():
        raise FloatingPointError("nonfinite LTD weights")
    return weights, {"event_mode": event_mode, "eligibility_offsets_frames": [int(x) for x in offsets],
                     "p95_min": float(scale.min()), "p95_max": float(scale.max())}


def predict_by_minimum(features: np.ndarray, weights: np.ndarray) -> np.ndarray:
    values = np.einsum("ntd,d->nt", features.astype(np.float64), weights, optimize=False)
    return GRID[np.argmin(values, axis=1)]


def bootstrap_interval(values: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))
    draws = values[indices].mean(axis=1)
    return tuple(float(v) for v in np.quantile(draws, [0.025, 0.975]))


def make_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing results: {output}")
    output.mkdir(parents=True)
    start = time.time()
    raw_hash = sha256(RAW)
    contract_hash = sha256(CONTRACT)
    bio, provenance = choose_bio_basis()
    rbf = generic_rbf()
    shuffled = bio.copy()
    profile_rng = np.random.default_rng(909)
    for col in range(shuffled.shape[1]):
        shuffled[:, col] = shuffled[profile_rng.permutation(len(GRID)), col]

    with (output / "selected_cell_provenance.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(provenance[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(provenance)
    basis_rows = []
    for t, sec in enumerate(GRID):
        row = {"time_seconds": float(sec)}
        for j in range(bio.shape[1]):
            row[f"bio_{j:02d}"] = float(bio[t, j])
            row[f"shuffled_bio_{j:02d}"] = float(shuffled[t, j])
            row[f"rbf_{j:02d}"] = float(rbf[t, j])
        basis_rows.append(row)
    make_csv(output / "temporal_bases.csv", basis_rows)

    all_episode_rows: list[dict[str, object]] = []
    all_seed_rows: list[dict[str, object]] = []
    fit_rows: list[dict[str, object]] = []
    mappings = {"ALIGNED": (0.9, 1.8), "REVERSED": (1.8, 0.9)}
    for seed in SEEDS:
        for mapping_index, (mapping, intervals) in enumerate(mappings.items()):
            tr_rng = np.random.default_rng(seed * 1009 + mapping_index)
            train = []
            for _ in range(NTRAIN):
                cue = int(tr_rng.integers(0, 2))
                x, target, noise = episode(tr_rng, cue, intervals[cue], bio)
                train.append((cue, x, target, noise))
            te_rng = np.random.default_rng(seed * 1009 + 555)
            test = []
            for _ in range(NTEST):
                cue = int(te_rng.integers(0, 2))
                x, target, noise = episode(te_rng, cue, intervals[cue], bio)
                test.append((cue, x, target, noise))

            arm_weights: dict[str, dict[int, np.ndarray]] = {arm: {} for arm in ARMS}
            timer: dict[int, float] = {}
            for cue in (0, 1):
                cue_train = [row for row in train if row[0] == cue]
                targets = np.asarray([row[2] for row in cue_train], dtype=np.float64)
                bio_features = np.stack([row[1] for row in cue_train])
                # Re-use each episode's exact noise realization for every representation.
                noise = np.stack([row[3] for row in cue_train])
                rbf_features = rbf[None, :, :] + noise
                shuffled_features = shuffled[None, :, :] + noise
                w_bio, meta = source_ltd_fit(bio_features, targets, np.random.default_rng(seed + cue), "source")
                w_no_trace, _ = source_ltd_fit(bio_features, targets, np.random.default_rng(seed + cue + 100), "instant")
                w_time_shuf, _ = source_ltd_fit(bio_features, targets, np.random.default_rng(seed + cue + 200), "permuted")
                w_rbf, _ = source_ltd_fit(rbf_features, targets, np.random.default_rng(seed + cue + 300), "source")
                w_shuffled, _ = source_ltd_fit(shuffled_features, targets, np.random.default_rng(seed + cue + 400), "source")
                w_cell_shuffle = w_bio[np.random.default_rng(seed + cue + 500).permutation(len(w_bio))]
                arm_weights["BIO_CF_LTD"][cue] = w_bio
                arm_weights["BIO_NO_TRACE"][cue] = w_no_trace
                arm_weights["BIO_CF_TIME_SHUFFLED"][cue] = w_time_shuf
                arm_weights["BIO_CELL_SHUFFLED"][cue] = w_cell_shuffle
                arm_weights["GENERIC_RBF_CF_LTD"][cue] = w_rbf
                arm_weights["SHUFFLED_BIO_CF_LTD"][cue] = w_shuffled
                arm_weights["UNIFORM_POOL"][cue] = -np.full(bio.shape[1], 1.0 / bio.shape[1])
                timer[cue] = float(targets.mean())
                fit_rows.append({"task_seed": seed, "mapping": mapping, "cue": cue,
                                 "n_training_episodes": len(cue_train), "n_test_episodes": sum(r[0] == cue for r in test),
                                 "n_training_CF_events": len(cue_train),
                                 "source_window_frames": ",".join(map(str, meta["eligibility_offsets_frames"])),
                                 "weight_l1": float(np.abs(w_bio).sum()), "weight_l2": float(np.linalg.norm(w_bio))})

            by_arm: dict[str, list[float]] = {arm: [] for arm in ARMS}
            for episode_index, (cue, x_bio, target, noise) in enumerate(test):
                arm_features = {
                    "BIO_CF_LTD": x_bio,
                    "BIO_NO_TRACE": x_bio,
                    "BIO_CF_TIME_SHUFFLED": x_bio,
                    "BIO_CELL_SHUFFLED": x_bio,
                    "GENERIC_RBF_CF_LTD": rbf + noise,
                    "SHUFFLED_BIO_CF_LTD": shuffled + noise,
                    "UNIFORM_POOL": x_bio,
                }
                for arm in ARMS:
                    if arm == "EMPIRICAL_TIMER":
                        estimate = timer[cue]
                    else:
                        estimate = float(predict_by_minimum(arm_features[arm][None, :, :], arm_weights[arm][cue])[0])
                    error = abs(estimate - target)
                    by_arm[arm].append(error)
                    all_episode_rows.append({"task_seed": seed, "mapping": mapping, "episode_index": episode_index,
                                             "cue": cue, "true_reward_time_s": target,
                                             "estimated_reward_time_s": estimate,
                                             "absolute_error_s": error, "arm": arm})
            for arm, errors in by_arm.items():
                all_seed_rows.append({"task_seed": seed, "mapping": mapping, "arm": arm,
                                      "test_episodes": len(errors), "mean_absolute_error_s": float(np.mean(errors)),
                                      "median_absolute_error_s": float(np.median(errors))})
        print(f"completed paired task seed {seed}", flush=True)

    seed_means = {(r["mapping"], r["task_seed"], r["arm"]): r["mean_absolute_error_s"] for r in all_seed_rows}
    summary_rows = []
    contrast_rows = []
    for mapping in mappings:
        for arm in ARMS:
            values = np.asarray([seed_means[(mapping, seed, arm)] for seed in SEEDS])
            lo, hi = bootstrap_interval(values, BOOT_SEED + (0 if mapping == "ALIGNED" else 10_000))
            summary_rows.append({"mapping": mapping, "arm": arm, "n_task_seeds": len(SEEDS),
                                 "mean_seed_mae_s": float(values.mean()), "bootstrap95_low_s": lo,
                                 "bootstrap95_high_s": hi, "min_seed_mae_s": float(values.min()),
                                 "max_seed_mae_s": float(values.max())})
        for control in ("BIO_NO_TRACE", "BIO_CF_TIME_SHUFFLED", "BIO_CELL_SHUFFLED",
                        "GENERIC_RBF_CF_LTD", "SHUFFLED_BIO_CF_LTD", "UNIFORM_POOL", "EMPIRICAL_TIMER"):
            diffs = np.asarray([seed_means[(mapping, seed, control)] - seed_means[(mapping, seed, "BIO_CF_LTD")]
                                for seed in SEEDS])
            lo, hi = bootstrap_interval(diffs, BOOT_SEED + (0 if mapping == "ALIGNED" else 10_000) + len(contrast_rows) + 1)
            contrast_rows.append({"mapping": mapping, "contrast": f"{control} minus BIO_CF_LTD",
                                  "mean_mae_improvement_s": float(diffs.mean()),
                                  "bootstrap95_low_s": lo, "bootstrap95_high_s": hi,
                                  "task_seeds_favoring_BIO_CF_LTD": int(np.count_nonzero(diffs > 0))})

    make_csv(output / "episode_results.csv", all_episode_rows)
    make_csv(output / "task_seed_results.csv", all_seed_rows)
    make_csv(output / "arm_summary.csv", summary_rows)
    make_csv(output / "paired_contrasts.csv", contrast_rows)
    make_csv(output / "fit_manifest.csv", fit_rows)
    summary = {"experiment_id": EXP, "classification": "post-result exploratory artificial transfer",
               "task_seeds": list(SEEDS), "training_episodes_per_mapping": NTRAIN,
               "test_episodes_per_mapping": NTEST, "episodes_per_mapping_total": NTRAIN + NTEST,
               "primary_mapping": "ALIGNED", "primary_outcome": "task-seed mean absolute reward-time error in seconds",
               "source_window_seconds": list(SPLIT_WIN), "source_frame_offsets": matlab_round(np.asarray(SPLIT_WIN) / DT).tolist(),
               "summary_rows": summary_rows, "paired_contrasts": contrast_rows,
               "interpretation": "Any result is limited to this synthetic task and extracted mean temporal profiles; no biological causality or general AI claim follows."}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if sha256(RAW) != raw_hash or sha256(CONTRACT) != contract_hash:
        raise RuntimeError("raw input or contract changed during execution")
    output_hashes = {}
    for path in sorted(output.iterdir()):
        if path.is_file():
            output_hashes[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    manifest = {"experiment_id": EXP, "classification": summary["classification"],
                "started_unix": start, "finished_unix": time.time(), "duration_seconds": time.time() - start,
                "python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "h5py": h5py.__version__,
                "raw_sha256": raw_hash, "raw_sha256_matches_dryad": raw_hash == json.loads(ACQUISITION.read_text())["files"][0]["dryad_sha256"],
                "acquisition_manifest_sha256": sha256(ACQUISITION), "contract_sha256": contract_hash,
                "runner_sha256": sha256(Path(__file__)), "seed_count": len(SEEDS), "outputs": output_hashes}
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "primary_summary": [r for r in summary_rows if r["mapping"] == "ALIGNED"],
                      "primary_contrasts": [r for r in contrast_rows if r["mapping"] == "ALIGNED"]}, indent=2))


def preflight() -> dict[str, object]:
    basis, meta = choose_bio_basis()
    return {"experiment_id": EXP, "raw_sha256": sha256(RAW), "raw_bytes": RAW.stat().st_size,
            "profile_basis_shape": list(basis.shape), "selected_source_cells": len(meta),
            "source_groups": sorted({str(m["source_group"]) for m in meta}),
            "grid_bins": len(GRID), "arms": list(ARMS), "seeds": list(SEEDS)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--preflight", action="store_true", help="inspect source basis and task settings without generating outcomes")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), indent=2))
    else:
        run(args.output_dir)


if __name__ == "__main__":
    main()
