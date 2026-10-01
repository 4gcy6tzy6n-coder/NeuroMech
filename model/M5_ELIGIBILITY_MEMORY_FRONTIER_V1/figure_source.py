#!/usr/bin/env python3
"""Plot the accuracy/active-state frontier for delayed credit assignment."""
from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.transforms import ScaledTranslation

from audit_panel_alignment import require_matplotlib_panel_alignment

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "results" / "M5_ELIGIBILITY_MEMORY_FRONTIER_V1" / "canonical" / "task_metrics.csv"
OUT = ROOT / "data" / "results" / "M5_ELIGIBILITY_MEMORY_FRONTIER_V1" / "figures"
FAMILIES = (
    ("IID_GAUSSIAN", "IID Gaussian"),
    ("AR1_GAUSSIAN", "AR(1) Gaussian"),
    ("SPARSE_SIGN", "Sparse sign"),
)
DELAYS = (1, 4, 16, 64)
COLORS = {1: "#484878", 4: "#2B8C9B", 16: "#D28E2D", 64: "#9B5F8F"}
FIFO_ARMS = {"EXACT_FIFO_64", "EXACT_FIFO_256", "EXACT_FIFO_1024", "EXACT_FIFO_4096"}
FIG_WIDTH_IN, FIG_HEIGHT_IN = 7.2047, 3.2283  # 183 mm × 82 mm final size

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 6.6,
    "axes.labelsize": 7,
    "axes.titlesize": 7.2,
    "xtick.labelsize": 6.2,
    "ytick.labelsize": 6.2,
    "legend.fontsize": 6.1,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.7,
    "legend.frameon": False,
    "lines.linewidth": 1.35,
    "pdf.use14corefonts": False,
})


def percentile_ci(values: np.ndarray, seed: int):
    rng = np.random.default_rng(seed)
    ids = rng.integers(0, len(values), size=(20_000, len(values)))
    draws = values[ids].mean(axis=1)
    return np.quantile(draws, [0.025, 0.975])


def load_rows():
    with DATA.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    grouped = {}
    for row in rows:
        key = (row["generator"], int(row["seed"]), int(row["delay"]), row["arm"])
        grouped[key] = float(row["test_accuracy"])
    return grouped


def aggregate(grouped, family, delay, arms):
    by_seed = {}
    for arm in arms:
        for seed in range(100, 130):
            by_seed.setdefault(arm, []).append(grouped[(family, seed, delay, arm)])
    result = {}
    for arm, values in by_seed.items():
        values = np.asarray(values)
        lo, hi = percentile_ci(values, 20261002 + DELAYS.index(delay) * 100 + len(arm))
        result[arm] = (float(values.mean()), float(lo), float(hi))
    return result


def add_panel_label(ax, label):
    offset = ScaledTranslation(-3 / 72, 2 / 72, ax.figure.dpi_scale_trans)
    ax.text(0, 1, label, transform=ax.transAxes + offset, ha="left", va="bottom",
            fontsize=8, fontweight="bold", clip_on=False)


def main():
    grouped = load_rows()
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN), sharey=True)
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.32, top=0.82, wspace=0.14)
    fig.suptitle("Eligibility traces trade delayed-credit accuracy for compact state", x=0.5,
                 y=0.965, fontsize=9, fontweight="bold")

    fifo_names = ["EXACT_FIFO_64", "EXACT_FIFO_256", "EXACT_FIFO_1024", "EXACT_FIFO_4096"]
    for panel_i, (family, title) in enumerate(FAMILIES):
        ax = axes[panel_i]
        add_panel_label(ax, "abc"[panel_i])
        ax.set_title(title, pad=6)
        for delay in DELAYS:
            color = COLORS[delay]
            estimates = aggregate(grouped, family, delay, fifo_names + ["ELIGIBILITY_TRACE_64"])
            # Collapse arms with identical actual state size; FIFO arms with capacity >= delay
            # encode the same exact replay and have identical task-level results.
            by_state = {}
            for arm in fifo_names:
                cap = int(arm.rsplit("_", 1)[1]) // 64
                state_values = min(cap, delay) * 64
                by_state[state_values] = estimates[arm]
            xs = sorted(by_state)
            if not xs or min(xs) <= 0:
                raise ValueError("active memory budgets must be positive before logarithmic display")
            means = np.asarray([by_state[x][0] for x in xs])
            lows = np.asarray([by_state[x][1] for x in xs])
            highs = np.asarray([by_state[x][2] for x in xs])
            ax.plot(xs, means, color=color, marker="o", markersize=3.1,
                    markeredgecolor="white", markeredgewidth=0.55, linewidth=1.2, zorder=3)
            ax.errorbar(xs, means, yerr=np.vstack([means - lows, highs - means]),
                        fmt="none", ecolor=color, capsize=1.8, elinewidth=0.75, zorder=3)

            trace = estimates["ELIGIBILITY_TRACE_64"]
            ax.errorbar([64], [trace[0]], yerr=[[trace[0] - trace[1]], [trace[2] - trace[0]]],
                        color=color, marker="*", markersize=6.2, markeredgecolor="white",
                        markeredgewidth=0.45, capsize=1.8, elinewidth=0.75, zorder=5)

        current_by_seed = np.asarray([
            np.mean([grouped[(family, seed, delay, "CURRENT_FEATURE_64")] for delay in DELAYS])
            for seed in range(100, 130)
        ])
        current_lo, current_hi = percentile_ci(current_by_seed, 20261333 + panel_i)
        current_mean = float(current_by_seed.mean())
        ax.errorbar([64], [current_mean],
                    yerr=[[current_mean - current_lo], [current_hi - current_mean]],
                    color="#555555", marker="x", markersize=4.1, markeredgewidth=1.0,
                    capsize=1.8, elinewidth=0.8, zorder=6)

        ax.set_xscale("log", base=2)
        ax.set_xlim(42, 6200)
        ax.set_xticks([64, 256, 1024, 4096], labels=["64", "256", "1,024", "4,096"])
        ax.set_ylim(0.20, 0.84)
        ax.set_yticks(np.arange(0.25, 0.81, 0.15))
        ax.axhline(0.25, color="#8A8A8A", linestyle=(0, (2, 2)), linewidth=0.65, zorder=0)
        ax.grid(axis="y", color="#E5E5E5", linewidth=0.55)
        ax.set_xlabel("Peak active feature-state values")
    axes[0].set_ylabel("Held-out accuracy")

    delay_handles = [Line2D([0], [0], color=COLORS[d], marker="o", markersize=3.2,
                            linewidth=1.3, label=f"Exact replay, delay {d}") for d in DELAYS]
    method_handles = [
        Line2D([0], [0], color="#333333", marker="*", linestyle="none", markersize=6,
               label="Eligibility trace (64 values)"),
        Line2D([0], [0], color="#333333", marker="x", linestyle="none", markersize=4,
               label="Current-feature update (64 values; delay-averaged)"),
    ]
    fig.legend(handles=delay_handles + method_handles, ncol=3, loc="lower center",
               bbox_to_anchor=(0.5, 0.085), columnspacing=1.5, handletextpad=0.45,
               borderaxespad=0, labelspacing=0.65)
    fig.text(0.5, 0.025,
             "Mean ± task-seed bootstrap 95% CI (n=30 per generator); dashed line = chance (0.25).",
             ha="center", va="bottom", fontsize=6.1, color="#444444")

    fig.canvas.draw()
    prefix = OUT / "M5_ELIGIBILITY_MEMORY_FRONTIER_V1"
    alignment = require_matplotlib_panel_alignment(
        fig,
        json_out=str(prefix) + ".alignment.json",
        overlay_svg=str(prefix) + ".alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        require_panel_labels=True,
        strict=True,
    )
    fig.savefig(str(prefix) + ".pdf", metadata={"Title": "M5 eligibility trace memory-accuracy frontier"})
    fig.savefig(str(prefix) + ".svg")
    fig.savefig(str(prefix) + ".png", dpi=600)
    fig.savefig(str(prefix) + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    for svg_path in OUT.glob("*.svg"):
        svg_text = svg_path.read_text(encoding="utf-8")
        svg_path.write_text(re.sub(r"[ \t]+(?=\n|$)", "", svg_text), encoding="utf-8")
    print({"figure": str(prefix), "alignment_verdict": alignment.get("verdict")})


if __name__ == "__main__":
    main()
