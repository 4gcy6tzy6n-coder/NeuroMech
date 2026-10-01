#!/usr/bin/env python3
"""Plot task-native outcomes across reversal hazards."""
import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_LTC_THERMOTAXIS_REVERSAL_V1"
SUMMARY = ROOT / "data/results" / EXP / "summary.json"
OUT = ROOT / "data/results" / EXP / "figures"
ARMS = ["LTC_SENSORY_SITE", "LTC_OUTPUT_SITE", "LTC_NO_FEEDBACK", "LTC_DENSE_FEEDBACK",
        "LTC_SENSORY_YOKED", "GRU_4", "GRU_8"]
LABELS = ["LTC sensory-site", "LTC output-site", "LTC no feedback", "LTC dense feedback",
          "LTC yoked", "GRU-4", "GRU-8"]
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#56B4E9", "#E69F00", "#333333", "#999999"]
HAZARDS = [1/80, 1/40, 1/20]

def main():
    data = json.loads(SUMMARY.read_text())
    rows = data["arm_metric_summaries"]
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9.3, 4.0))
    for ax, (metric, ylabel, title) in zip(axes, [
        ("position_mse", "Position MSE (lower is better)", "Thermal setpoint tracking"),
        ("action_energy", "Mean squared action", "Control effort")]):
        for arm, label, color in zip(ARMS, LABELS, COLORS):
            rs = [next(r for r in rows if r["arm"] == arm and r["metric"] == metric
                       and r["reversal_hazard"] == h) for h in HAZARDS]
            y = [r["mean_seed_block"] for r in rs]
            lo = [r["bootstrap_95ci"][0] for r in rs]
            hi = [r["bootstrap_95ci"][1] for r in rs]
            x = range(3)
            ax.plot(x, y, marker="o", linewidth=1.6, markersize=4, color=color, label=label)
            ax.fill_between(x, lo, hi, color=color, alpha=0.10, linewidth=0)
        ax.set_xticks(range(3), ["1/80", "1/40", "1/20"])
        ax.set_xlabel("Gradient reversal hazard")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(axis="y", color="#dddddd", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, -0.02), fontsize=7.5, columnspacing=1.4)
    fig.suptitle("M2 motor-state feedback in LTC thermotaxis-like control", y=1.02, fontsize=11)
    fig.text(0.5, -0.07, "32 seed blocks; ribbons are percentile 95% seed-block bootstrap intervals. Privileged oracle omitted.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.11, 1, 0.97), w_pad=1.6)
    for suffix, kwargs in (("png", {"dpi": 300}), ("svg", {}), ("pdf", {})):
        fig.savefig(OUT / f"{EXP}.{suffix}", bbox_inches="tight", **kwargs)
    p = OUT / f"{EXP}.svg"
    p.write_text("\n".join(line.rstrip() for line in p.read_text().splitlines()) + "\n")
    plt.close(fig)

if __name__ == "__main__": main()
