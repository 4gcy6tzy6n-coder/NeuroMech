#!/usr/bin/env python3
"""Render the M2 optimizer-budget frontier with seed-block bootstrap intervals."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_BURSTY_COMPUTE_FRONTIER_V1"
SUMMARY = ROOT / "data" / "results" / EXP / "summary.json"
OUT = ROOT / "data" / "results" / EXP / "figures"
ARMS = ("SENSORY_SITE", "OUTPUT_SITE", "NO_FEEDBACK", "GENERIC_RNN", "GRU_8")
LABELS = {
    "SENSORY_SITE": "Sensory-site feedback (4 params)",
    "OUTPUT_SITE": "Output-site feedback (4)",
    "NO_FEEDBACK": "No feedback (4)",
    "GENERIC_RNN": "Scalar RNN (4)",
    "GRU_8": "GRU-8 (321)",
}
COLORS = {"SENSORY_SITE": "#0072B2", "OUTPUT_SITE": "#D55E00", "NO_FEEDBACK": "#009E73",
          "GENERIC_RNN": "#CC79A7", "GRU_8": "#333333"}
UPDATES = (60, 120, 240)


def main():
    data = json.loads(SUMMARY.read_text())
    rows = data["arm_metric_summaries"]
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.8), sharey=True)
    for ax, q in zip(axes, (0.125, 0.50)):
        for arm in ARMS:
            selected = [next(r for r in rows if r["checkpoint_updates"] == updates
                             and r["visibility_q"] == q and r["arm"] == arm
                             and r["metric"] == "tracking_mse") for updates in UPDATES]
            mean = np.asarray([r["mean_seed_block"] for r in selected])
            lo = np.asarray([r["bootstrap_95ci_low"] for r in selected])
            hi = np.asarray([r["bootstrap_95ci_high"] for r in selected])
            ax.plot(UPDATES, mean, marker="o", linewidth=1.7, markersize=4,
                    color=COLORS[arm], label=LABELS[arm])
            ax.fill_between(UPDATES, lo, hi, color=COLORS[arm], alpha=0.12, linewidth=0)
        ax.set_title(f"Evaluation visibility q = {q:g}", fontsize=9)
        ax.set_xlabel("Optimizer updates")
        ax.set_xticks(UPDATES)
        ax.grid(axis="y", color="#dddddd", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Tracking MSE (lower is better)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 0.105), fontsize=7.2, columnspacing=1.5,
               handlelength=1.8, labelspacing=0.6)
    fig.suptitle("Feedback placement and recurrent capacity across training budgets", y=1.02, fontsize=10)
    fig.text(0.5, 0.025, "Mean across 32 training-seed blocks; bands are percentile 95% bootstrap intervals.",
             ha="center", fontsize=7)
    fig.tight_layout(rect=(0, 0.27, 1, 0.96), w_pad=1.1)
    for suffix, kwargs in (("png", {"dpi": 300}), ("svg", {}), ("pdf", {})):
        fig.savefig(OUT / f"{EXP}.{suffix}", bbox_inches="tight", **kwargs)
    svg_path = OUT / f"{EXP}.svg"
    svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n")
    plt.close(fig)
    print(f"wrote figures to {OUT}")


if __name__ == "__main__":
    main()
