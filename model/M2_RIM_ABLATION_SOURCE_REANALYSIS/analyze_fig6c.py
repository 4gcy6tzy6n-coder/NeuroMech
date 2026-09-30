#!/usr/bin/env python3
"""Descriptive reanalysis of published C. elegans Figure 6C source events."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/elife-68848-fig6-data1-v3.xlsx"
OUT = ROOT / "data/results/M2_RIM_ABLATION_SOURCE_REANALYSIS"
SHEET = "Fig 6C"
DIRECTION_BINS = 12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def collect_group(rows, angle_col: int, duration_col: int):
    pairs = []
    partial_rows = 0
    for row in rows:
        angle, duration = row[angle_col], row[duration_col]
        if angle is None and duration is None:
            continue
        if angle is None or duration is None:
            partial_rows += 1
            continue
        pairs.append((float(angle), float(duration)))
    return np.asarray(pairs, dtype=float), partial_rows


def group_summary(values: np.ndarray) -> dict:
    direction, duration = values[:, 0], values[:, 1]
    return {
        "events": int(len(duration)),
        "direction_min_rad": float(direction.min()),
        "direction_max_rad": float(direction.max()),
        "duration_min_s": float(duration.min()),
        "duration_max_s": float(duration.max()),
        "duration_mean_s": float(duration.mean()),
        "duration_median_s": float(np.median(duration)),
        "duration_q25_s": float(np.quantile(duration, 0.25)),
        "duration_q75_s": float(np.quantile(duration, 0.75)),
        "fraction_duration_ge_30s": float(np.mean(duration >= 30.0)),
        "fraction_duration_ge_60s": float(np.mean(duration >= 60.0)),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(SOURCE, read_only=True, data_only=True)
    if SHEET not in workbook.sheetnames:
        raise ValueError(f"Expected sheet {SHEET!r}; found {workbook.sheetnames}")
    sheet = workbook[SHEET]
    header_rows = list(sheet.iter_rows(min_row=1, max_row=2, values_only=True))
    expected_headers = {
        "group_labels": ("WT", "RIM ablated"),
        "wt_fields": ("Run direction (radian)", "Run duration (s)"),
        "rim_fields": ("Run direction (radian)", "Run duration (s)"),
    }
    observed_headers = {
        "group_labels": (header_rows[0][0], header_rows[0][3]),
        "wt_fields": (header_rows[1][0], header_rows[1][1]),
        "rim_fields": (header_rows[1][3], header_rows[1][4]),
    }
    if observed_headers != expected_headers:
        raise ValueError(f"Unexpected Figure 6C schema: {observed_headers}")
    rows = list(sheet.iter_rows(min_row=3, values_only=True))
    wt, wt_partial = collect_group(rows, 0, 1)
    rim, rim_partial = collect_group(rows, 3, 4)
    if len(wt) == 0 or len(rim) == 0:
        raise ValueError("No paired run direction/duration observations found")
    if not np.isfinite(wt).all() or not np.isfinite(rim).all():
        raise ValueError("Non-finite source values found")
    if np.any(wt[:, 1] <= 0) or np.any(rim[:, 1] <= 0):
        raise ValueError("Forward-run durations must be positive")

    edges = np.linspace(-np.pi, np.pi, DIRECTION_BINS + 1)
    records = []
    for group, values in (("WT", wt), ("RIM_ABLATED", rim)):
        indices = np.digitize(values[:, 0], edges[1:-1], right=False)
        for i in range(DIRECTION_BINS):
            durations = values[indices == i, 1]
            records.append({
                "group": group,
                "direction_bin": i,
                "direction_left_rad": float(edges[i]),
                "direction_right_rad": float(edges[i + 1]),
                "event_count": int(len(durations)),
                "duration_mean_s": float(durations.mean()) if len(durations) else None,
                "duration_median_s": float(np.median(durations)) if len(durations) else None,
                "duration_q25_s": float(np.quantile(durations, 0.25)) if len(durations) else None,
                "duration_q75_s": float(np.quantile(durations, 0.75)) if len(durations) else None,
                "fraction_duration_ge_30s": float(np.mean(durations >= 30)) if len(durations) else None,
            })
    table = OUT / "direction_bin_descriptives.csv"
    headers = list(records[0])
    import csv
    with table.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)

    wt_summary, rim_summary = group_summary(wt), group_summary(rim)
    six_bins = []
    coarse_edges = np.linspace(-np.pi, np.pi, 7)
    for i in range(6):
        wt_d = wt[(wt[:, 0] >= coarse_edges[i]) & (wt[:, 0] < coarse_edges[i + 1]), 1]
        rim_d = rim[(rim[:, 0] >= coarse_edges[i]) & (rim[:, 0] < coarse_edges[i + 1]), 1]
        six_bins.append({
            "direction_left_rad": float(coarse_edges[i]),
            "direction_right_rad": float(coarse_edges[i + 1]),
            "wt_events": int(len(wt_d)),
            "rim_ablated_events": int(len(rim_d)),
            "wt_duration_median_s": float(np.median(wt_d)),
            "rim_ablated_duration_median_s": float(np.median(rim_d)),
            "rim_ablated_minus_wt_median_s": float(np.median(rim_d) - np.median(wt_d)),
        })

    summary = {
        "status": "EXPLORATORY_EVENT_LEVEL_SOURCE_DATA_REANALYSIS",
        "source": {
            "paper": "Ji et al., eLife 2021, 10:e68848",
            "doi": "10.7554/eLife.68848",
            "source_data_file": str(SOURCE.relative_to(ROOT)),
            "source_data_sha256": sha256(SOURCE),
            "sheet": SHEET,
            "columns": {
                "WT": ["Run direction (radian)", "Run duration (s)"],
                "RIM_ABLATED": ["Run direction (radian)", "Run duration (s)"],
            },
        },
        "independent_unit": "Not available in this source sheet; event-level summaries are descriptive and are not used for animal-level inference.",
        "row_quality": {
            "data_rows_examined": len(rows),
            "expected_schema_verified": True,
            "wt_partial_direction_duration_rows": wt_partial,
            "rim_ablated_partial_direction_duration_rows": rim_partial,
            "all_durations_positive": True,
            "all_values_finite": True,
        },
        "wt_event_weighted": wt_summary,
        "rim_ablated_event_weighted": rim_summary,
        "event_weighted_contrast": {
            "rim_ablated_minus_wt_mean_s": rim_summary["duration_mean_s"] - wt_summary["duration_mean_s"],
            "rim_ablated_minus_wt_median_s": rim_summary["duration_median_s"] - wt_summary["duration_median_s"],
            "rim_ablated_minus_wt_fraction_ge_30s": rim_summary["fraction_duration_ge_30s"] - wt_summary["fraction_duration_ge_30s"],
            "fraction_ge_30s_relative_reduction": 1 - rim_summary["fraction_duration_ge_30s"] / wt_summary["fraction_duration_ge_30s"],
        },
        "six_equal_angle_bins_descriptive": six_bins,
        "inference_boundary": "No p-values, confidence intervals, or worm-level effects are computed because event-to-worm keys are absent. Events are repeated observations; pooling weights animals by how many runs they contribute.",
        "analysis_parameters": {"direction_bins_for_plot": DIRECTION_BINS, "long_run_threshold_s": 30.0},
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    centers = (edges[:-1] + edges[1:]) / 2
    for group, color, values in (("WT", "#246a73", wt), ("RIM ablated", "#cf6a3b", rim)):
        medians = [r["duration_median_s"] for r in records if r["group"] == group.replace(" ", "_").upper()]
        counts = [r["event_count"] for r in records if r["group"] == group.replace(" ", "_").upper()]
        axes[0].plot(centers, medians, marker="o", linewidth=2, color=color, label=group)
        axes[1].plot(centers, counts, marker="o", linewidth=2, color=color, label=group)
    axes[0].set_title("Forward-run duration by heading bin")
    axes[0].set_xlabel("Run direction (radians; source convention)")
    axes[0].set_ylabel("Median run duration (s)")
    axes[1].set_title("Source events per heading bin")
    axes[1].set_xlabel("Run direction (radians; source convention)")
    axes[1].set_ylabel("Number of run events")
    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
        ax.legend(frameon=False)
    fig.suptitle("Ji et al. Figure 6C source-data reanalysis\nEvent-level descriptive summaries; no worm IDs available", fontsize=12)
    figure_path = OUT / "figure6c_event_level_descriptive.png"
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    import importlib.metadata as metadata
    manifest = {
        "experiment": "M2_RIM_ABLATION_SOURCE_REANALYSIS",
        "python": platform.python_version(),
        "packages": {name: metadata.version(name) for name in ("numpy", "openpyxl", "matplotlib")},
        "artifacts_sha256": {
            "model/M2_RIM_ABLATION_SOURCE_REANALYSIS/analyze_fig6c.py": sha256(Path(__file__).resolve()),
            "data/results/M2_RIM_ABLATION_SOURCE_REANALYSIS/summary.json": sha256(summary_path),
            "data/results/M2_RIM_ABLATION_SOURCE_REANALYSIS/direction_bin_descriptives.csv": sha256(table),
            "data/results/M2_RIM_ABLATION_SOURCE_REANALYSIS/figure6c_event_level_descriptive.png": sha256(figure_path),
        },
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "wt_events": wt_summary["events"],
        "rim_ablated_events": rim_summary["events"],
        "wt_median_duration_s": wt_summary["duration_median_s"],
        "rim_ablated_median_duration_s": rim_summary["duration_median_s"],
        "median_difference_s": summary["event_weighted_contrast"]["rim_ablated_minus_wt_median_s"],
        "fraction_ge_30s": {
            "wt": wt_summary["fraction_duration_ge_30s"],
            "rim_ablated": rim_summary["fraction_duration_ge_30s"],
        },
        "all_six_coarse_bin_median_differences_s": [x["rim_ablated_minus_wt_median_s"] for x in six_bins],
        "inference": "descriptive only; no worm IDs",
    }, indent=2))


if __name__ == "__main__":
    main()
