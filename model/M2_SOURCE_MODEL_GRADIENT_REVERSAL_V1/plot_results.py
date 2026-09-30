#!/usr/bin/env python3
"""Render the gradient-reversal result and control-failure figure."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/canonical"
FIGURE_BASE = RESULTS / "Figure_M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1"
METRICS_PATH = RESULTS / "seed_block_metrics.csv"

# Use the project's selected figure backend and its rendered axes-alignment gate.
SKILL_SCRIPTS = Path.home() / ".codex/skills/nature-figure/scripts"
if SKILL_SCRIPTS.exists():
    sys.path.insert(0, str(SKILL_SCRIPTS))
try:
    from audit_panel_alignment import require_matplotlib_panel_alignment
except ImportError as exc:  # pragma: no cover - depends on the local figure-audit runtime
    raise RuntimeError("Install the Nature Figure skill audit scripts or add them to PYTHONPATH") from exc

SCHEDULES = (0.0, 40.0, 20.0, 10.0, 5.0)
ARMS = ("SENSORY_SITE_FB", "OUTPUT_SITE_FB", "NO_FEEDBACK")
LABELS = {
    "SENSORY_SITE_FB": "Sensory-site feedback",
    "OUTPUT_SITE_FB": "Output-site feedback",
    "NO_FEEDBACK": "No feedback",
}
COLORS = {
    "SENSORY_SITE_FB": "#267B78",
    "OUTPUT_SITE_FB": "#BC6F72",
    "NO_FEEDBACK": "#64748B",
}
N_BOOT = 20_000
BOOT_SEED = 20261013


def bootstrap_ci(values: np.ndarray, rng: np.random.RandomState) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    draws = rng.randint(0, values.size, size=(N_BOOT, values.size))
    means = values[draws].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> None:
    with METRICS_PATH.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    seeds = sorted({int(row["seed_block"]) for row in rows})
    if len(seeds) != 100:
        raise ValueError(f"expected 100 seed blocks, found {len(seeds)}")
    lookup = {
        (int(row["seed_block"]), float(row["reversal_interval_s"]), row["arm"]): row
        for row in rows
    }
    rng = np.random.RandomState(BOOT_SEED)
    plot_rows: list[dict[str, object]] = []
    contrast_series = {
        "Sensory − no feedback": [],
        "Sensory − output site†": [],
    }
    contrast_ci = {key: [] for key in contrast_series}
    occupancy_means = {arm: [] for arm in ARMS}
    occupancy_ci = {arm: [] for arm in ARMS}

    for interval in SCHEDULES:
        for contrast_name, arm_b in (
            ("Sensory − no feedback", "NO_FEEDBACK"),
            ("Sensory − output site†", "OUTPUT_SITE_FB"),
        ):
            paired = np.asarray([
                float(lookup[(seed, interval, "SENSORY_SITE_FB")]["aligned_progress_rate"])
                - float(lookup[(seed, interval, arm_b)]["aligned_progress_rate"])
                for seed in seeds
            ])
            ci = bootstrap_ci(paired, rng)
            mean = float(paired.mean())
            contrast_series[contrast_name].append(mean)
            contrast_ci[contrast_name].append(ci)
            plot_rows.append({
                "reversal_interval_s": interval,
                "panel": "a_paired_progress_contrast",
                "series": contrast_name,
                "mean": mean,
                "ci95_low": ci[0],
                "ci95_high": ci[1],
                "n_seed_blocks": len(seeds),
                "positive_seed_blocks": int((paired > 0).sum()),
                "uncertainty": "paired percentile bootstrap over seed blocks; 20000 resamples",
            })
        for arm in ARMS:
            values = np.asarray([
                float(lookup[(seed, interval, arm)]["forward_occupancy"])
                for seed in seeds
            ])
            ci = bootstrap_ci(values, rng)
            occupancy_means[arm].append(float(values.mean()))
            occupancy_ci[arm].append(ci)
            plot_rows.append({
                "reversal_interval_s": interval,
                "panel": "b_forward_occupancy",
                "series": LABELS[arm],
                "mean": float(values.mean()),
                "ci95_low": ci[0],
                "ci95_high": ci[1],
                "n_seed_blocks": len(seeds),
                "positive_seed_blocks": "",
                "uncertainty": "percentile bootstrap over seed blocks; 20000 resamples",
            })

    with (RESULTS / "figure_source_data.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(plot_rows[0]))
        writer.writeheader()
        writer.writerows(plot_rows)

    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.labelsize": 7,
        "axes.titlesize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 6.5,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.7,
        "lines.linewidth": 1.5,
        "lines.markersize": 4,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    })
    fig, axes = plt.subplots(1, 2, figsize=(7.0866, 3.5433), sharex=True)
    ax, ax_occ = axes
    x = np.arange(len(SCHEDULES))
    contrast_styles = {
        "Sensory − no feedback": ("#267B78", "-", "o"),
        "Sensory − output site†": ("#BC6F72", "--", "s"),
    }
    for name, values in contrast_series.items():
        color, linestyle, marker = contrast_styles[name]
        cis = np.asarray(contrast_ci[name])
        vals = np.asarray(values)
        yerr = np.vstack((vals - cis[:, 0], cis[:, 1] - vals))
        ax.errorbar(x, vals, yerr=yerr, color=color, linestyle=linestyle,
                    marker=marker, capsize=2.3, elinewidth=0.8, label=name)
    ax.axhline(0, color="#444444", linewidth=0.7, zorder=0)
    ax.set_ylabel("Change in aligned progress (units per s)")
    ax.set_title("Paired progress contrasts (n = 100 blocks)", loc="left", pad=6)
    ax.text(0.63, 0.95, "Sensory − no feedback", transform=ax.transAxes,
            color="#267B78", fontsize=6.5, va="top")
    ax.text(0.63, 0.89, "Sensory − output site†", transform=ax.transAxes,
            color="#BC6F72", fontsize=6.5, va="top")

    xlabels = ["Static", "40 s", "20 s", "10 s", "5 s"]
    for arm in ARMS:
        vals = np.asarray(occupancy_means[arm])
        cis = np.asarray(occupancy_ci[arm])
        yerr = np.vstack((vals - cis[:, 0], cis[:, 1] - vals))
        ax_occ.errorbar(x, vals, yerr=yerr, color=COLORS[arm],
                        linestyle="--" if arm == "OUTPUT_SITE_FB" else "-",
                        marker={"SENSORY_SITE_FB": "o", "OUTPUT_SITE_FB": "s", "NO_FEEDBACK": "^"}[arm],
                        capsize=2.3, elinewidth=0.8, label=LABELS[arm])
    ax_occ.set_ylim(-0.04, 1.12)
    ax_occ.set_ylabel("Forward-state occupancy")
    ax_occ.set_title("Forward-state occupancy (n = 100 blocks)", loc="left", pad=6)
    ax_occ.text(0.62, 0.80, LABELS["OUTPUT_SITE_FB"], transform=ax_occ.transAxes,
                color=COLORS["OUTPUT_SITE_FB"], fontsize=6.5, va="top")
    ax_occ.text(0.62, 0.31, LABELS["SENSORY_SITE_FB"], transform=ax_occ.transAxes,
                color=COLORS["SENSORY_SITE_FB"], fontsize=6.5, va="top")
    ax_occ.text(0.62, 0.12, LABELS["NO_FEEDBACK"], transform=ax_occ.transAxes,
                color=COLORS["NO_FEEDBACK"], fontsize=6.5, va="top")

    for axis in axes:
        axis.set_xticks(x, xlabels)
        axis.set_xlabel("Gradient reversal interval")
        axis.grid(False)
        axis.set_axisbelow(True)
        axis.spines["left"].set_color("#64748B")
        axis.spines["bottom"].set_color("#64748B")
        axis.tick_params(width=0.6, length=2.5, color="#64748B")
    ax.text(-0.16, 1.04, "a", transform=ax.transAxes, fontweight="bold", fontsize=9)
    ax_occ.text(-0.16, 1.04, "b", transform=ax_occ.transAxes, fontweight="bold", fontsize=9)
    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.20, top=0.88, wspace=0.34)

    require_matplotlib_panel_alignment(
        fig,
        json_out=f"{FIGURE_BASE}.alignment.json",
        overlay_svg=f"{FIGURE_BASE}.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
    )
    fig.savefig(FIGURE_BASE.with_suffix(".pdf"), format="pdf")
    fig.savefig(FIGURE_BASE.with_suffix(".svg"), format="svg")
    fig.savefig(FIGURE_BASE.with_suffix(".tiff"), format="tiff", dpi=600)
    fig.savefig(FIGURE_BASE.with_suffix(".png"), format="png", dpi=300)
    plt.close(fig)
    print(json.dumps({"figure_base": FIGURE_BASE.name, "seed_blocks": len(seeds), "panels": 2}, indent=2))


if __name__ == "__main__":
    main()
