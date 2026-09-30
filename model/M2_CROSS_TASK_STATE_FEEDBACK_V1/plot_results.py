"""Create the primary contrast figure from the frozen experiment summary."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "data/results/M2_CROSS_TASK_STATE_FEEDBACK_V1/summary.json"
OUT = ROOT / "data/results/M2_CROSS_TASK_STATE_FEEDBACK_V1/figures/m2_cross_task_primary_contrast"


def main():
    summary = json.loads(SUMMARY.read_text())
    names = ["ALIGNED (primary)", "INDEPENDENT (secondary)", "REVERSED (secondary)"]
    keys = ["ALIGNED", "INDEPENDENT", "REVERSED"]
    contrasts = [summary["by_condition"][key]["primary_family_contrast"] for key in keys]
    estimates = [item["generic_minus_mode_gain_mse"] for item in contrasts]
    lows = [item["crossed_95_percent_bootstrap_interval"][0] for item in contrasts]
    highs = [item["crossed_95_percent_bootstrap_interval"][1] for item in contrasts]
    colors = ["#2878A5", "#7A8791", "#C46B50"]

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 8,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
    })
    fig, ax = plt.subplots(figsize=(7.2, 2.65))
    ys = [2, 1, 0]
    for y, estimate, low, high, color in zip(ys, estimates, lows, highs, colors):
        ax.errorbar(estimate, y, xerr=[[estimate - low], [high - estimate]],
                    fmt="o", color=color, ecolor=color, markersize=5,
                    capsize=3, linewidth=1.4, zorder=3)
    ax.axvline(0, color="#333333", linewidth=1, linestyle=(0, (3, 2)), zorder=1)
    ax.set_yticks(ys, names)
    ax.set_xlim(-0.065, 0.13)
    ax.set_ylim(-0.65, 2.65)
    ax.set_xlabel("MSE(RNN) − MSE(mode-gain filter)  (positive favors mode-gain)")
    ax.set_title("The mode-gain advantage reverses under a reversed mapping", loc="left", weight="bold", fontsize=9)
    ax.grid(axis="x", color="#D8DDE1", linewidth=0.6, zorder=0)
    ax.tick_params(axis="both", length=0)
    fig.tight_layout(pad=1.1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUT.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(OUT.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(OUT.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
