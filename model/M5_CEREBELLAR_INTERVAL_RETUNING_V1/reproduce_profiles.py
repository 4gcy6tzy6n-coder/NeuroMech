#!/usr/bin/env python3
"""Descriptive reanalysis of source-defined GrC timing profiles in Dryad v4."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4"
OUT = ROOT / "data/results/M5_CEREBELLAR_INTERVAL_RETUNING_V1/source_reproduction"
INPUT = RAW / "learning_1s_to_2s_GrC_CF.mat"
GROUP_LABELS = ("1-s expert", "2-s novice / 1-s expert", "2-s expert")


def ref_object(h5: h5py.File, ref: h5py.Reference):
    if not ref:
        raise ValueError("unexpected null MATLAB object reference")
    return h5[ref]


def read_vector(session: h5py.Group, name: str) -> np.ndarray:
    return np.asarray(session[name][()]).reshape(-1)


def session_refs(h5: h5py.File, group_index: int):
    group_cell = ref_object(h5, h5["groups"][0, group_index])
    return [group_cell[0, j] for j in range(group_cell.shape[1])]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    session_rows: list[dict[str, object]] = []
    profile_rows: list[dict[str, object]] = []
    cell_rows: list[dict[str, object]] = []

    with h5py.File(INPUT, "r") as h5:
        template_session = ref_object(h5, session_refs(h5, 2)[0])
        template_time = read_vector(template_session, "tmpxCb")
        for g, label in enumerate(GROUP_LABELS):
            session_profiles = []
            for d, ref in enumerate(session_refs(h5, g), start=1):
                s = ref_object(h5, ref)
                t = read_vector(s, "tmpxCb")
                dt = float(np.asarray(s["dtimCb"][()]).reshape(-1)[0])
                dtb = float(np.asarray(s["dtb"][()]).reshape(-1)[0])
                delay = (read_vector(s, "rewtimes") - read_vector(s, "midpt")) * dtb
                rewarded = read_vector(s, "rewarded").astype(bool)
                good = read_vector(s, "goodmvdir").astype(bool)
                threshold = 0.75 if g == 0 else 1.75
                trials = np.flatnonzero(rewarded & good & (delay > threshold))
                if len(trials) == 0:
                    raise ValueError(f"no source-filtered reward trials in group {g+1}, session {d}")

                # MATLAB dimensions are trials × cells × time; HDF5 reverses them.
                activity = np.asarray(s["midAlgn/sigFilt_GrC"][:, :, trials], dtype=np.float32)
                # HDF5 view is time × cells × trials.
                mean_activity = np.mean(activity, axis=2, dtype=np.float64).T
                baseline = (t >= -1.0) & (t <= 0.0)
                interval = (t >= 0.0) & (t <= 2.0)
                baseline_mean = np.mean(mean_activity[:, baseline], axis=1)
                interval_activity = mean_activity[:, interval]
                interval_time = t[interval]
                active = interval_activity > baseline_mean[:, None]
                durations = active.sum(axis=1) * dt
                centroids = np.full(mean_activity.shape[0], np.nan, dtype=np.float64)
                for c in range(mean_activity.shape[0]):
                    use = active[c]
                    vals = interval_activity[c, use]
                    denom = vals.sum()
                    if use.any() and np.isfinite(denom) and abs(denom) > 1e-12:
                        centroids[c] = np.sum(vals * interval_time[use]) / denom

                session_profile = np.interp(
                    template_time, t, np.mean(mean_activity, axis=0)
                )
                session_profiles.append(session_profile)
                session_rows.append({
                    "source_group": g + 1,
                    "source_group_label": label,
                    "within_group_session_index": d,
                    "eligible_reward_trials": int(len(trials)),
                    "grc_cells": int(mean_activity.shape[0]),
                    "imaging_dt_seconds": dt,
                    "mean_reward_delay_seconds": float(np.mean(delay[trials])),
                    "median_grc_active_duration_seconds": float(np.nanmedian(durations)),
                    "median_grc_activity_centroid_seconds": float(np.nanmedian(centroids)),
                })
                for c, (duration, centroid) in enumerate(zip(durations, centroids), start=1):
                    cell_rows.append({
                        "source_group": g + 1,
                        "source_group_label": label,
                        "within_group_session_index": d,
                        "cell_index_within_session": c,
                        "active_duration_seconds": float(duration),
                        "activity_centroid_seconds": float(centroid),
                    })

            # Equal session weighting avoids letting larger sessions dominate the profile.
            group_profile = np.mean(np.stack(session_profiles), axis=0)
            for time_s, activity_z in zip(template_time, group_profile):
                profile_rows.append({
                    "source_group": g + 1,
                    "source_group_label": label,
                    "time_from_movement_midpoint_seconds": float(time_s),
                    "mean_grc_activity_z": float(activity_z),
                })

    def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(OUT / "session_summary.csv", session_rows)
    write_csv(OUT / "group_time_profiles.csv", profile_rows)
    write_csv(OUT / "cell_metrics_descriptive.csv", cell_rows)
    digest = hashlib.sha256()
    with INPUT.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    input_hash = digest.hexdigest()
    summary = {
        "analysis": "full eligible-trial source-filtered descriptive reproduction",
        "contract": "summery/M5_CEREBELLAR_INTERVAL_RETUNING_V1/REPRODUCTION_CONTRACT.md",
        "input": str(INPUT.relative_to(ROOT)),
        "input_sha256": input_hash,
        "source_code_reference": "wagnerlabnih/garcia-garcia-neuron-2024:learning_1s_to_2s_GrC_CF.m",
        "source_code_commit": "124c83e1af83e9680e05f9827448579d02345fa3",
        "python_version": __import__("platform").python_version(),
        "numpy_version": np.__version__,
        "h5py_version": h5py.__version__,
        "analysis_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "groups": list(GROUP_LABELS),
        "trial_sampling": "all rewarded & goodmvdir trials past source delay threshold; no first/random-50 subsampling",
        "inference": "descriptive only; cells are nested and are not treated as independent biological replicates",
        "n_sessions_in_source_groups": [
            sum(row["source_group"] == i for row in session_rows) for i in (1, 2, 3)
        ],
        "session_summary_file": "session_summary.csv",
        "group_profiles_file": "group_time_profiles.csv",
        "cell_metrics_file": "cell_metrics_descriptive.csv",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
