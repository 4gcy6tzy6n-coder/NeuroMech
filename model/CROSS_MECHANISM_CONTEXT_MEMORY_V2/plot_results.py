#!/usr/bin/env python3
"""Render the two task-native V2 contrasts without pooling their outcomes."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from figure_alignment import require_matplotlib_panel_alignment

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/canonical_corrected"
OUT = ROOT / "data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/figures"
PALETTE = {
    "context": "#7884B4",
    "no_context": "#B4C0E4",
    "latest": "#7884B4",
    "fifo": "#A8A8A8",
    "trace": "#2E9E44",
    "zero": "#606060",
    "point": "#484878",
}
fig_width_mm = 180
fig_height_mm = 85

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 7,
    "axes.labelsize": 7,
    "axes.titlesize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "legend.fontsize": 6,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def draw_group(ax, x: float, values: np.ndarray, color: str, summary: dict, offset: float = 0.0) -> None:
    jitter = 0.075 * np.sin(np.arange(len(values), dtype=float) * 2.399963229728653)
    xs = x + offset + jitter
    ax.scatter(xs, values, s=8, color=color, alpha=0.32, edgecolors="none", zorder=2)
    mean = float(summary["mean"])
    low, high = map(float, summary["ci95"])
    assert np.isclose(mean, values.mean(), atol=1e-12, rtol=0)
    ax.errorbar(x + offset, mean, yerr=[[mean - low], [high - mean]], color=color,
                marker="o", markersize=3.2, markeredgecolor="white", markeredgewidth=0.5,
                linewidth=1.2, capsize=2.2, zorder=4)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    m2 = read_rows(DATA / "m2_seed_results.csv")
    m5 = read_rows(DATA / "m5_seed_results.csv")
    summary = json.loads((DATA / "summary.json").read_text())
    fig, (ax_m2, ax_m5) = plt.subplots(
        1, 2, figsize=(fig_width_mm / 25.4, fig_height_mm / 25.4), constrained_layout=False
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.82, bottom=0.25, wspace=0.32)

    ax_m2.axhline(0, color=PALETTE["zero"], linewidth=0.8, linestyle=(0, (2, 2)), zorder=1)
    mappings = [(1.0, "Aligned\nκ = +1"), (0.0, "Independent\nκ = 0"), (-1.0, "Reversed\nκ = −1")]
    for idx, (kappa, _) in enumerate(mappings):
        rows = [r for r in m2 if float(r["kappa"]) == kappa]
        ctx = np.array([float(r["gru_context_minus_gain"]) for r in rows])
        noctx = np.array([float(r["gru_no_context_minus_gain"]) for r in rows])
        group_summary = summary["m2_by_mapping"][str(kappa)]
        draw_group(ax_m2, idx, ctx, PALETTE["context"], group_summary["gru_context_minus_gain"], offset=-0.10)
        draw_group(ax_m2, idx, noctx, PALETTE["no_context"], group_summary["gru_no_context_minus_gain"], offset=0.10)
    ax_m2.set_xticks(range(3), [label for _, label in mappings])
    ax_m2.set_ylabel("GRU − context-gain filter (MSE)")
    ax_m2.set_title("M2  |  State estimation", loc="left", x=0.075, pad=7, fontweight="bold")
    ax_m2.text(0.0, 1.045, "a", transform=ax_m2.transAxes, fontsize=8, fontweight="bold", va="bottom")
    ax_m2.text(0.02, 0.02, "Negative favors GRU; context GRU 297 params,\nobservation-only GRU 273, filter 3.",
               transform=ax_m2.transAxes, fontsize=5.2, va="bottom", color="#404040")
    ax_m2.set_xlim(-0.48, 2.48)

    ax_m5.axhline(0, color=PALETTE["zero"], linewidth=0.8, linestyle=(0, (2, 2)), zorder=1)
    delays = [1, 4, 16, 64]
    for idx, delay in enumerate(delays):
        rows = [r for r in m5 if int(r["delay"]) == delay]
        trace_vs_latest = np.array([float(r["eligibility_minus_latest_input"]) for r in rows])
        trace_vs_fifo = np.array([float(r["eligibility_minus_exact_fifo"]) for r in rows])
        group_summary = summary["m5_by_delay"][str(delay)]
        draw_group(ax_m5, idx, trace_vs_latest, PALETTE["trace"], group_summary["eligibility_minus_latest_input"], offset=-0.10)
        draw_group(ax_m5, idx, trace_vs_fifo, PALETTE["fifo"], group_summary["eligibility_minus_exact_fifo"], offset=0.10)
    ax_m5.set_xticks(range(4), [str(delay) for delay in delays])
    ax_m5.set_xlabel("Teaching-signal delay (steps)")
    ax_m5.set_ylabel("Eligibility − comparator (accuracy)")
    ax_m5.set_title("M5  |  Delayed credit", loc="left", x=0.075, pad=7, fontweight="bold")
    ax_m5.text(0.0, 1.045, "b", transform=ax_m5.transAxes, fontsize=8, fontweight="bold", va="bottom")
    ax_m5.text(0.02, 0.02, "Positive favors eligibility; latest-input and eligibility\nuse 16 state dimensions; FIFO uses 16 × delay.",
               transform=ax_m5.transAxes, fontsize=5.2, va="bottom", color="#404040")
    ax_m5.set_xlim(-0.48, 3.48)

    handles = [
        plt.Line2D([], [], marker="o", linestyle="none", color=PALETTE["context"], label="Context-aware GRU"),
        plt.Line2D([], [], marker="o", linestyle="none", color=PALETTE["no_context"], label="Observation-only GRU"),
        plt.Line2D([], [], marker="o", linestyle="none", color=PALETTE["trace"], label="Trace − latest input"),
        plt.Line2D([], [], marker="o", linestyle="none", color=PALETTE["fifo"], label="Trace − exact FIFO"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.08), ncol=4,
               frameon=False, handletextpad=0.45, columnspacing=1.3)
    fig.text(0.5, 0.025, "Each dot is one task-seed block (n = 32); markers and bars show mean and 95% seed-bootstrap interval.",
             ha="center", va="bottom", fontsize=5.5, color="#404040")

    alignment_path = OUT / "CROSS_MECHANISM_CONTEXT_MEMORY_V2.alignment.json"
    alignment_report = require_matplotlib_panel_alignment(
        fig,
        json_out=alignment_path,
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
        panel_ids={ax_m2: "a", ax_m5: "b"},
    )
    (OUT / "CROSS_MECHANISM_CONTEXT_MEMORY_V2.layout.json").write_text(
        json.dumps(alignment_report["layout"], indent=2) + "\n"
    )
    stem = OUT / "CROSS_MECHANISM_CONTEXT_MEMORY_V2"
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".svg"))
    fig.savefig(stem.with_suffix(".png"), dpi=600)
    fig.savefig(stem.with_suffix(".tiff"), dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    main()
