"""Render the prespecified two-panel figure from canonical seed summaries."""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_ACTUATION_UNCERTAINTY_STATE_FEEDBACK_V1"
DATA = ROOT / "data/results" / NAME / "canonical/seed_summary.csv"
OUT = ROOT / "data/results" / NAME / "figures"
LEVELS = [0.0, 0.1, 0.25, 0.4]
COLORS = {
    "SELF_STATE": "#007C91",
    "ACTION_STATE": "#D17A00",
    "ZERO_STATE": "#68737D",
    "YOKED_STATE": "#9A6FB0",
    "REACTIVE": "#222222",
}


def interval(values, seed):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    draws = values[rng.integers(0, len(values), size=(20_000, len(values)))].mean(axis=1)
    return np.quantile(draws, [0.025, 0.975])


def main():
    df = pd.read_csv(DATA)
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9,
        "svg.fonttype": "none", "pdf.fonttype": 42,
        "ps.fonttype": 42, "axes.spines.top": False,
        "axes.spines.right": False,
    })
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.1, 3.15), constrained_layout=True)
    x = np.arange(len(LEVELS))
    arms = ["SELF_STATE", "ACTION_STATE", "ZERO_STATE", "YOKED_STATE", "REACTIVE"]
    offsets = np.linspace(-0.16, 0.16, len(arms))
    for arm, offset in zip(arms, offsets):
        means, low, high = [], [], []
        for j, level in enumerate(LEVELS):
            vals = df[(df.reverse_probability == level) & (df.arm == arm)].sort_values("seed_block").tracking_mse.to_numpy()
            ci = interval(vals, 8_765_700 + j * 10 + arms.index(arm))
            means.append(vals.mean()); low.append(vals.mean() - ci[0]); high.append(ci[1] - vals.mean())
        ax1.errorbar(x + offset, means, yerr=[low, high], marker="o", lw=1.5,
                     ms=4, capsize=2, color=COLORS[arm], label=arm.replace("_", " "))
    ax1.set_xticks(x, ["0", ".10", ".25", ".40"])
    ax1.set_xlabel("Actuator reversal probability")
    ax1.set_ylabel("Tracking MSE (lower is better)")
    ax1.set_title("A  Performance across reversal dose", loc="left", weight="bold")
    ax1.legend(frameon=False, fontsize=7, ncol=2, loc="upper left")
    ax1.grid(axis="y", color="#D9DEE2", lw=0.6)

    deltas = []
    for level in LEVELS:
        sub = df[df.reverse_probability == level].pivot(index="seed_block", columns="arm", values="tracking_mse")
        d = (sub.ACTION_STATE - sub.SELF_STATE).sort_index().to_numpy()
        ci = interval(d, 8_765_800 + LEVELS.index(level))
        deltas.append((d.mean(), d.mean() - ci[0], ci[1] - d.mean()))
    ax2.errorbar(x, [d[0] for d in deltas], yerr=[[d[1] for d in deltas], [d[2] for d in deltas]],
                 marker="o", color="#007C91", lw=1.8, capsize=3, ms=5)
    ax2.axhline(0, color="#555555", ls="--", lw=1)
    ax2.set_xticks(x, ["0", ".10", ".25", ".40"])
    ax2.set_xlabel("Actuator reversal probability")
    ax2.set_ylabel("ACTION_STATE − SELF_STATE MSE")
    ax2.set_title("B  Paired realized-state advantage", loc="left", weight="bold")
    ax2.grid(axis="y", color="#D9DEE2", lw=0.6)
    fig.suptitle("Synthetic tracking under actuator uncertainty · 32 training-seed blocks", fontsize=10, weight="bold")
    for ext, kwargs in [("svg", {}), ("pdf", {}), ("tiff", {"dpi": 600})]:
        fig.savefig(OUT / f"{NAME}.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


if __name__ == "__main__":
    main()
