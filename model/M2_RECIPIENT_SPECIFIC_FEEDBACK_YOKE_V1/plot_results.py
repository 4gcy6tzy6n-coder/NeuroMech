#!/usr/bin/env python3
"""Plot the frozen recipient-specific feedback contrast and its task grid."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize

from figure_alignment import require_matplotlib_panel_alignment

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/results/M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1/canonical"
OUT = ROOT / "data/results/M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1/figures"
WIDTH_MM = 180
HEIGHT_MM = 86
SEEDS = tuple(range(420000, 420032))
EPISODES = tuple(range(256))
HAZARDS = (1 / 240, 1 / 120, 1 / 40)
MISSING = (0.25, 0.50, 0.75)

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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = read_csv(DATA / "episode_results.csv")
    summary = json.loads((DATA / "summary.json").read_text())
    values = {}
    for row in rows:
        key = (int(row["training_seed"]), float(row["hazard"]), float(row["missing_rate"]),
               int(row["episode_id"]), row["arm"])
        values[key] = float(row["tracking_mse"])

    primary = np.array([
        [values[(seed, 1 / 120, 0.50, episode, "SENSORY_CROSS_AGENT_YOKE")] -
         values[(seed, 1 / 120, 0.50, episode, "SENSORY_SELF")]
         for episode in EPISODES]
        for seed in SEEDS
    ])
    per_seed = primary.mean(axis=1)
    overall = summary["primary"]
    mean, low, high = float(overall["mean"]), *map(float, overall["ci95"])

    heat = np.empty((len(HAZARDS), len(MISSING)), dtype=float)
    for i, hazard in enumerate(HAZARDS):
        for j, missing in enumerate(MISSING):
            pairs = [values[(seed, hazard, missing, episode, "SENSORY_CROSS_AGENT_YOKE")] -
                     values[(seed, hazard, missing, episode, "SENSORY_SELF")]
                     for seed in SEEDS for episode in EPISODES]
            heat[i, j] = float(np.mean(pairs))

    fig, (ax_primary, ax_grid) = plt.subplots(
        1, 2, figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), constrained_layout=False
    )
    fig.subplots_adjust(left=0.085, right=0.91, top=0.82, bottom=0.27, wspace=0.34)

    ax_primary.axvline(0, color="#606060", linewidth=0.8, linestyle=(0, (2, 2)), zorder=1)
    jitter = 0.12 * np.sin(np.arange(len(per_seed), dtype=float) * 2.399963229728653)
    ax_primary.scatter(per_seed, jitter, s=13, color="#7884B4", alpha=0.72,
                       edgecolors="white", linewidths=0.35, zorder=2)
    ax_primary.errorbar(mean, 0.31, xerr=[[mean - low], [high - mean]], fmt="D",
                        color="#2E9E44", markeredgecolor="white", markeredgewidth=0.5,
                        markersize=4.2, linewidth=1.4, capsize=3, zorder=4)
    ax_primary.text(0.18, 0.93, f"Crossed mean {mean:+.4f}  [{low:+.4f}, {high:+.4f}]",
                    transform=ax_primary.transAxes, fontsize=5.5, va="top", color="#343434")
    ax_primary.set_xlim(-0.008, 0.052)
    ax_primary.set_ylim(-0.22, 0.50)
    ax_primary.set_yticks([])
    ax_primary.set_xlabel("MSE(yoke) − MSE(self-feedback)")
    ax_primary.set_title("Primary condition  |  h = 1/120, 50% missing", loc="left", x=0.075,
                         pad=7, fontweight="bold")
    ax_primary.text(0.0, 1.045, "a", transform=ax_primary.transAxes, fontsize=8,
                    fontweight="bold", va="bottom")
    ax_primary.text(0.18, 0.06, "Positive values favor recipient-specific feedback.",
                    transform=ax_primary.transAxes, fontsize=5.5, va="bottom", color="#404040")

    cmap = LinearSegmentedColormap.from_list("m2_specificity", ["#F3F3F3", "#B4D6C8", "#2E9E44"])
    image = ax_grid.imshow(heat, cmap=cmap, norm=Normalize(vmin=0, vmax=0.11), aspect="auto")
    for i in range(len(HAZARDS)):
        for j in range(len(MISSING)):
            ax_grid.text(j, i, f"{heat[i, j]:+.3f}", ha="center", va="center",
                         fontsize=6, color="#1f382a" if heat[i, j] < 0.075 else "white",
                         fontweight="bold")
    ax_grid.set_xticks(range(3), ["25%", "50%", "75%"])
    ax_grid.set_yticks(range(3), ["1/240", "1/120", "1/40"])
    ax_grid.set_xlabel("Sensory observations missing")
    ax_grid.set_ylabel("Target-switch hazard")
    ax_grid.set_title("Self-specificity across task conditions", loc="left", x=0.075,
                      pad=7, fontweight="bold")
    ax_grid.text(0.0, 1.045, "b", transform=ax_grid.transAxes, fontsize=8,
                 fontweight="bold", va="bottom")
    cax = fig.add_axes([0.925, 0.35, 0.014, 0.42])
    colorbar = fig.colorbar(image, cax=cax)
    colorbar.set_label("Mean yoke − self MSE", fontsize=6)
    colorbar.ax.tick_params(labelsize=5.5, width=0.6, length=2)

    legend_handles = [
        plt.Line2D([], [], marker="o", linestyle="none", color="#7884B4", markersize=4,
                   label="Training-seed mean (n = 32)"),
        plt.Line2D([], [], marker="D", linestyle="-", color="#2E9E44", markersize=4,
                   label="Grand mean and crossed 95% interval"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, 0.105),
               ncol=2, frameon=False, handletextpad=0.5, columnspacing=1.5)
    fig.text(0.5, 0.025,
             "Panel a: 32 seed means, each over 256 paired episodes; interval resamples seed and episode IDs. "
             "Panel b: descriptive grid means; cells are not separate confirmatory tests.",
             ha="center", va="bottom", fontsize=5.2, color="#404040")

    stem = OUT / "M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1"
    alignment = require_matplotlib_panel_alignment(
        fig,
        json_out=stem.with_suffix(".alignment.json"),
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
        panel_ids={ax_primary: "a", ax_grid: "b"},
    )
    stem.with_suffix(".layout.json").write_text(json.dumps(alignment["layout"], indent=2) + "\n")
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".svg"))
    fig.savefig(stem.with_suffix(".png"), dpi=600)
    fig.savefig(stem.with_suffix(".tiff"), dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    main()
