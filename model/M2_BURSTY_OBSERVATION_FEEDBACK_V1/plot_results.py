#!/usr/bin/env python3
"""Publication-style plot for M2_BURSTY_OBSERVATION_FEEDBACK_V1."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from audit_panel_alignment import require_matplotlib_panel_alignment

ARMS = ("SENSORY_SITE", "OUTPUT_SITE", "NO_FEEDBACK", "GENERIC_RNN", "GRU_8")
LABELS = {
    "SENSORY_SITE": "Sensory-site feedback",
    "OUTPUT_SITE": "Output-site persistence",
    "NO_FEEDBACK": "No feedback",
    "GENERIC_RNN": "Generic scalar RNN",
    "GRU_8": "GRU-8",
}
COLORS = {
    "SENSORY_SITE": "#2F6B8A",
    "OUTPUT_SITE": "#B86B52",
    "NO_FEEDBACK": "#9B9B9B",
    "GENERIC_RNN": "#739D85",
    "GRU_8": "#8C7AAE",
}


def read_rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def seed_mean_ci(rows, arm, q, seed_ids, rng, draws=10_000):
    by_seed = []
    for seed in seed_ids:
        vals = [float(r["tracking_mse"]) for r in rows
                if r["arm"] == arm and float(r["visibility_q"]) == q and int(r["training_seed"]) == seed]
        by_seed.append(float(np.mean(vals)))
    x = np.asarray(by_seed)
    sample = x[rng.integers(0, len(x), size=(draws, len(x)))].mean(axis=1)
    return float(x.mean()), np.quantile(sample, [.025, .975])


def paired_crossed_ci(rows, baseline, seeds, episodes=128, draws=10_000, rng=None):
    q = .125
    lookup = {(int(r["training_seed"]), int(r["episode_id"]), r["arm"]): float(r["tracking_mse"])
              for r in rows if float(r["visibility_q"]) == q and r["arm"] in (baseline, "SENSORY_SITE")}
    diff = np.asarray([[lookup[(s, e, baseline)] - lookup[(s, e, "SENSORY_SITE")]
                        for e in range(episodes)] for s in seeds])
    sample_means = np.empty(draws)
    for i in range(draws):
        si = rng.integers(0, len(seeds), size=len(seeds))
        ei = rng.integers(0, episodes, size=(len(seeds), episodes))
        sample_means[i] = diff[si[:, None], ei].mean()
    return float(diff.mean()), np.quantile(sample_means, [.025, .975])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_dir", type=Path)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    rows = read_rows(args.result_dir / "episode_results.csv")
    seeds = sorted({int(r["training_seed"]) for r in rows})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7,
        "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": .75,
        "legend.frameon": False, "xtick.major.width": .7, "ytick.major.width": .7,
        "xtick.major.size": 3, "ytick.major.size": 3,
    })
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.0, 3.72), constrained_layout=False)
    q_grid = (.50, .25, .125)
    gaps = np.asarray([2, 4, 8], dtype=float)
    rng = np.random.default_rng(20261002)
    for arm in ARMS:
        means, low, high = [], [], []
        for q in q_grid:
            m, ci = seed_mean_ci(rows, arm, q, seeds, rng)
            means.append(m); low.append(m - ci[0]); high.append(ci[1] - m)
        ax0.errorbar(gaps, means, yerr=np.asarray([low, high]), color=COLORS[arm],
                     marker="o", markersize=3.5, linewidth=1.45, capsize=2,
                     elinewidth=.8, label=LABELS[arm])
    ax0.set(xlabel="Expected missing-run length (steps)", ylabel="Tracking MSE",
            xticks=gaps, xlim=(1.55, 8.45), ylim=(.49, .79))
    ax0.grid(axis="y", color="#D9D9D9", linewidth=.5, alpha=.75)
    ax0.set_axisbelow(True)
    ax0.text(-.17, 1.045, "a", transform=ax0.transAxes, fontsize=8, fontweight="bold", va="bottom")

    arms_b = ("OUTPUT_SITE", "GENERIC_RNN", "GRU_8")
    labels_b = [LABELS[a] for a in arms_b]
    y = np.arange(len(arms_b))[::-1]
    rng = np.random.default_rng(20261001)
    effect_values = []
    for yi, arm in zip(y, arms_b):
        mean, ci = paired_crossed_ci(rows, arm, seeds, rng=rng)
        effect_values.append({"arm": arm, "mean_difference": mean, "ci95": [float(ci[0]), float(ci[1])]})
        ax1.errorbar(mean, yi, xerr=[[mean - ci[0]], [ci[1] - mean]], fmt="o",
                     color=COLORS[arm], markersize=4, capsize=2, elinewidth=.9,
                     markeredgecolor="white", markeredgewidth=.5)
    ax1.axvline(0, color="#333333", linewidth=.8, linestyle=(0, (2, 2)))
    ax1.set_yticks(y, labels_b)
    ax1.set_xlabel("Baseline MSE − sensory-site MSE\n(long-burst condition; positive favors sensory site)")
    ax1.set_xlim(-.012, .085)
    ax1.grid(axis="x", color="#E2E2E2", linewidth=.5, alpha=.7)
    ax1.set_axisbelow(True)
    ax1.text(-.17, 1.045, "b", transform=ax1.transAxes, fontsize=8, fontweight="bold", va="bottom")

    fig.legend(*ax0.get_legend_handles_labels(), loc="lower center", ncol=3,
               bbox_to_anchor=(.5, -.01), fontsize=6.5, columnspacing=1.4,
               handlelength=2.0, handletextpad=.5)
    fig.subplots_adjust(left=.10, right=.99, top=.91, bottom=.25, wspace=.42)
    align_json = args.output_dir / "M2_BURSTY_OBSERVATION_FEEDBACK_V1.alignment.json"
    align_svg = args.output_dir / "M2_BURSTY_OBSERVATION_FEEDBACK_V1.alignment.svg"
    require_matplotlib_panel_alignment(fig, json_out=str(align_json), overlay_svg=str(align_svg),
                                       tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    stem = args.output_dir / "M2_BURSTY_OBSERVATION_FEEDBACK_V1"
    fig.savefig(Path(str(stem) + ".svg"), bbox_inches="tight")
    fig.savefig(Path(str(stem) + ".pdf"), bbox_inches="tight")
    fig.savefig(Path(str(stem) + ".tiff"), dpi=600, bbox_inches="tight")
    (args.output_dir / "FIGURE_DATA.json").write_text(json.dumps({
        "panel_a_uncertainty": "95% percentile bootstrap CI over 24 training-seed mean MSEs; episodes nested within seed",
        "panel_b_uncertainty": "Frozen 95% crossed bootstrap resampling training seeds and paired held-out episode IDs",
        "independent_training_seeds": len(seeds), "heldout_episodes_per_seed_condition": 128,
        "long_burst_primary_contrasts": effect_values,
        "plot_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "matplotlib_version": mpl.__version__, "numpy_version": np.__version__,
        "source_data": "data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical/episode_results.csv"
    }, indent=2) + "\n")
    plt.close(fig)
    print(f"Wrote SVG, PDF and 600-dpi TIFF to {args.output_dir}")


if __name__ == "__main__":
    main()
