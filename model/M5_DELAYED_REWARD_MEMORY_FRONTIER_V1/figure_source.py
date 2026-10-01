#!/usr/bin/env python3
"""Plot the delayed-reward accuracy/active-state frontier by reward delay."""
from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from audit_panel_alignment import require_matplotlib_panel_alignment

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/results/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/canonical"
OUT = DATA.parent / "figures"
DELAYS = (1, 4, 16, 64)
SEEDS = tuple(range(30, 60))
ARMS = ("ELIGIBILITY_TRACE_32", "EXACT_FIFO_32", "EXACT_FIFO_128", "EXACT_FIFO_512",
        "EXACT_FIFO_2048", "NO_TRACE_CURRENT_32", "EXACT_REPLAY")
FIFO_CAPACITY = {"EXACT_FIFO_32": 1, "EXACT_FIFO_128": 4,
                 "EXACT_FIFO_512": 16, "EXACT_FIFO_2048": 64}
COLORS = {"trace": "#C14A36", "fifo": "#4B7185", "no_trace": "#A4A8AB", "replay": "#242A30"}
WIDTH_IN, HEIGHT_IN = 183 / 25.4, 112 / 25.4

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 6.5,
    "axes.labelsize": 6.7,
    "axes.titlesize": 7.2,
    "xtick.labelsize": 5.8,
    "ytick.labelsize": 6.0,
    "legend.fontsize": 6.2,
    "axes.linewidth": 0.65,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "savefig.facecolor": "white",
})


def load_metrics():
    with (DATA / "task_metrics.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = {(int(r["seed"]), int(r["delay"]), r["arm"]): r for r in rows}
    assert len(out) == len(SEEDS) * len(DELAYS) * len(ARMS)
    return out


def load_coverage():
    with (DATA / "update_coverage.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {(int(r["seed"]), int(r["delay"]), r["arm"]): float(r["update_coverage"]) for r in rows}


def estimate(lookup, delay: int, arm: str):
    values = np.asarray([float(lookup[(seed, delay, arm)]["heldout_expected_reward"]) for seed in SEEDS])
    rng = np.random.default_rng(20261003 + delay * 17 + sum(map(ord, arm)))
    ids = rng.integers(0, len(values), size=(20_000, len(values)))
    lo, hi = np.quantile(values[ids].mean(axis=1), [0.025, 0.975])
    return float(values.mean()), float(lo), float(hi)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lookup, coverage = load_metrics(), load_coverage()
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH_IN, HEIGHT_IN), sharex=True, sharey=True)
    axes = axes.ravel()
    derived = []
    for panel_i, (ax, delay) in enumerate(zip(axes, DELAYS)):
        fifo_points = []
        for arm, capacity in FIFO_CAPACITY.items():
            state = min(capacity, delay) * 32
            # When capacity exceeds the frozen delay, outcomes and update paths
            # are exactly equal; plot that state once and label full replay.
            if any(state == old[0] for old in fifo_points):
                continue
            mean, lo, hi = estimate(lookup, delay, arm)
            cov = float(np.mean([coverage[(seed, delay, arm)] for seed in SEEDS]))
            fifo_points.append((state, mean, lo, hi, cov, arm))
            derived.append({"delay": delay, "arm": arm, "active_credit_state_values": state,
                            "mean_expected_reward": mean, "ci95_low": lo, "ci95_high": hi,
                            "mean_update_coverage": cov})
        fifo_points.sort(key=lambda v: v[0])
        ax.plot([p[0] for p in fifo_points], [p[1] for p in fifo_points], color=COLORS["fifo"],
                lw=1.15, zorder=2)
        for state, mean, lo, hi, cov, arm in fifo_points:
            ax.errorbar(state, mean, yerr=[[mean - lo], [hi - mean]], fmt="D", ms=3.6,
                        mfc=COLORS["fifo"], mec="white", mew=0.55, ecolor=COLORS["fifo"],
                        elinewidth=0.75, capsize=1.8, zorder=3)

        trace = estimate(lookup, delay, "ELIGIBILITY_TRACE_32")
        no_trace = estimate(lookup, delay, "NO_TRACE_CURRENT_32")
        ax.errorbar(32, trace[0], yerr=[[trace[0] - trace[1]], [trace[2] - trace[0]]],
                    fmt="*", ms=8.0, mfc=COLORS["trace"], mec="white", mew=0.45,
                    ecolor=COLORS["trace"], elinewidth=0.8, capsize=1.8, zorder=5)
        ax.errorbar(32, no_trace[0], yerr=[[no_trace[0] - no_trace[1]], [no_trace[2] - no_trace[0]]],
                    fmt="o", ms=3.3, mfc="white", mec=COLORS["no_trace"], mew=0.9,
                    ecolor=COLORS["no_trace"], elinewidth=0.7, capsize=1.6, zorder=4)
        replay = estimate(lookup, delay, "EXACT_REPLAY")
        replay_state = delay * 32
        ax.plot(replay_state, replay[0], marker="x", ms=5, mew=0.9, color=COLORS["replay"],
                linestyle="none", zorder=6)
        for arm, values in (("ELIGIBILITY_TRACE_32", trace), ("NO_TRACE_CURRENT_32", no_trace),
                            ("EXACT_REPLAY", replay)):
            state = 32 if arm != "EXACT_REPLAY" else replay_state
            cov = float(np.mean([coverage[(seed, delay, arm)] for seed in SEEDS]))
            derived.append({"delay": delay, "arm": arm, "active_credit_state_values": state,
                            "mean_expected_reward": values[0], "ci95_low": values[1],
                            "ci95_high": values[2], "mean_update_coverage": cov})

        fifo1_cov = float(np.mean([coverage[(seed, delay, "EXACT_FIFO_32")] for seed in SEEDS]))
        ax.set_title(f"Reward delay D = {delay}", loc="left", pad=3.5, fontweight="semibold")
        ax.text(0.98, 0.94, f"1-vector FIFO updates: {100 * fifo1_cov:.3g}%", transform=ax.transAxes,
                ha="right", va="top", fontsize=5.5, color="#51565A")
        ax.set_xscale("log", base=2)
        ax.set_xlim(24, 2700)
        ax.set_ylim(0.488, 0.566)
        ax.set_xticks([32, 128, 512, 2048], labels=["32", "128", "512", "2,048"])
        ax.set_yticks([0.49, 0.51, 0.53, 0.55])
        ax.grid(axis="y", color="#DDE2E5", lw=0.55, zorder=0)
        ax.tick_params(length=2.4, width=0.55, pad=2)
        ax.text(-0.13, 1.05, "abcd"[panel_i], transform=ax.transAxes, fontsize=8,
                fontweight="bold", va="bottom", ha="left")

    handles = [
        plt.Line2D([], [], marker="*", color=COLORS["trace"], markeredgecolor="white",
                   linestyle="none", markersize=8, label="Eligibility trace (32 values)"),
        plt.Line2D([], [], marker="D", color=COLORS["fifo"], markeredgecolor="white",
                   linestyle="-", markersize=3.7, label="Exact FIFO; capacity increases"),
        plt.Line2D([], [], marker="o", color=COLORS["no_trace"], markerfacecolor="white",
                   linestyle="none", markersize=3.3, label="Current-score update"),
        plt.Line2D([], [], marker="x", color=COLORS["replay"], linestyle="none",
                   markersize=5, label="Exact replay (overlaid when FIFO covers D)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.047),
               columnspacing=1.5, handletextpad=0.45)
    fig.supxlabel("Active score-state values (log2 scale)", y=0.12, fontsize=6.8)
    fig.supylabel("Held-out expected reward", x=0.012, fontsize=6.8)
    fig.text(0.5, 0.012,
             "Points are task-seed means; bars are 95% bootstrap CIs (n = 30 seeds). FIFO coverage drops when capacity < delay.",
             ha="center", va="bottom", fontsize=5.6, color="#4D5358")
    fig.subplots_adjust(left=0.085, right=0.995, bottom=0.22, top=0.93, wspace=0.19, hspace=0.31)
    fig.canvas.draw()

    prefix = OUT / "M5_DELAYED_REWARD_MEMORY_FRONTIER_V1"
    alignment = require_matplotlib_panel_alignment(
        fig, json_out=str(prefix) + ".alignment.json",
        overlay_svg=str(prefix) + ".alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True,
    )
    fig.savefig(str(prefix) + ".pdf", metadata={"Title": "Delayed-reward bandit accuracy–memory frontier"})
    fig.savefig(str(prefix) + ".svg")
    fig.savefig(str(prefix) + ".png", dpi=600)
    fig.savefig(str(prefix) + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    with (OUT / "figure_source_data.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(derived[0]))
        writer.writeheader()
        writer.writerows(derived)
    for svg_path in OUT.glob("*.svg"):
        svg_text = svg_path.read_text(encoding="utf-8")
        svg_path.write_text(re.sub(r"[ \t]+(?=\n|$)", "", svg_text), encoding="utf-8")
    print({"figure": str(prefix), "alignment_verdict": alignment.get("verdict"),
           "derived_points": len(derived)})


if __name__ == "__main__":
    main()
