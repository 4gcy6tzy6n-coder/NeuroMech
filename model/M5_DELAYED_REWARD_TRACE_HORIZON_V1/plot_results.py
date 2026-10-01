#!/usr/bin/env python3
"""Render the fixed, publication-style summary figure from canonical outcomes."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/results/M5_DELAYED_REWARD_TRACE_HORIZON_V1/canonical"
OUT = ROOT / "data/results/M5_DELAYED_REWARD_TRACE_HORIZON_V1/trace_horizon_figure.svg"
DELAYS = (1, 4, 16, 64)
GAMMAS = ("0.50", "0.75", "0.90", "0.98")
COLORS = {"0.50": "#0072B2", "0.75": "#E69F00", "0.90": "#009E73", "0.98": "#CC79A7"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    metrics = read_rows(DATA / "seed_metrics.csv")
    contrasts = read_rows(DATA / "paired_contrasts.csv")
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.8, 5.0))
    for arm, label, color, marker in [
        ("NO_TRACE_CURRENT_32", "Current-score update", "#4D4D4D", "o"),
        ("EXACT_REPLAY", "Exact replay", "#000000", "s"),
    ]:
        means = [np.mean([float(r["heldout_expected_reward"]) for r in metrics
                          if r["arm"] == arm and int(r["delay"]) == d]) for d in DELAYS]
        left.plot(DELAYS, means, marker=marker, linewidth=2.0, color=color, label=label)
    for gamma in GAMMAS:
        arm = f"TRACE_GAMMA_{gamma}"
        means = [np.mean([float(r["heldout_expected_reward"]) for r in metrics
                          if r["arm"] == arm and int(r["delay"]) == d]) for d in DELAYS]
        left.plot(DELAYS, means, marker="o", linewidth=1.8, color=COLORS[gamma], label=rf"Trace $\gamma={gamma}$")
        cells = [next(r for r in contrasts if int(r["delay"]) == d and r["trace_arm"] == arm
                      and r["control"] == "NO_TRACE_CURRENT_32") for d in DELAYS]
        y = np.array([float(r["mean_difference"]) for r in cells])
        lo = np.array([float(r["ci95_low"]) for r in cells])
        hi = np.array([float(r["ci95_high"]) for r in cells])
        right.errorbar(DELAYS, y, yerr=np.vstack([y - lo, hi - y]), marker="o", linewidth=1.8,
                       capsize=3, color=COLORS[gamma], label=rf"$\gamma={gamma}$")

    for ax in (left, right):
        ax.set_xscale("log", base=2)
        ax.set_xticks(DELAYS, labels=[str(d) for d in DELAYS])
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.7)
        ax.spines[["top", "right"]].set_visible(False)
    left.set_title("A  Held-out expected reward", loc="left", fontweight="bold")
    left.set_xlabel("Reward delay (decisions)")
    left.set_ylabel("Expected reward")
    right.axhline(0, color="#555555", linewidth=1, linestyle="--")
    right.set_title("B  Trace − current-score update", loc="left", fontweight="bold")
    right.set_xlabel("Reward delay (decisions)")
    right.set_ylabel("Expected-reward difference")
    handles, labels = left.get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 0.01))
    fig.subplots_adjust(left=0.08, right=0.985, top=0.84, bottom=0.25, wspace=0.24)
    fig.suptitle("Eligibility decay trades compact state against exact delayed credit (30 task seeds)", fontsize=13, fontweight="bold", y=0.97)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, format="svg", facecolor="white")
    svg = OUT.read_text(encoding="utf-8")
    OUT.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n", encoding="utf-8")
    fig.savefig(OUT.with_suffix(".png"), dpi=300, facecolor="white")
    plt.close(fig)
    print(OUT)


if __name__ == "__main__":
    main()
