#!/usr/bin/env python3
"""Plot the equal-session GrC time profiles from the source-data reanalysis."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib as mpl


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/results/M5_CEREBELLAR_INTERVAL_RETUNING_V1/source_reproduction/group_time_profiles.csv"
OUT = ROOT / "data/results/M5_CEREBELLAR_INTERVAL_RETUNING_V1/source_reproduction/M5_CEREBELLAR_INTERVAL_RETUNING_V1_profiles.svg"


def main() -> None:
    mpl.rcParams["svg.hashsalt"] = "M5_CEREBELLAR_INTERVAL_RETUNING_V1"
    with DATA.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    colors = {1: "#363636", 2: "#8C6D1F", 3: "#147D78"}
    labels = {1: "1-s expert", 2: "2-s novice / 1-s expert", 3: "2-s expert"}
    fig, ax = plt.subplots(figsize=(8.4, 4.8), constrained_layout=True)
    for group in (1, 2, 3):
        selected = [r for r in rows if int(r["source_group"]) == group]
        x = [float(r["time_from_movement_midpoint_seconds"]) for r in selected]
        y = [float(r["mean_grc_activity_z"]) for r in selected]
        ax.plot(x, y, color=colors[group], linewidth=2.2, label=labels[group])
    for t in (1, 2):
        ax.axvline(t, color="#B33A3A", linewidth=1.0, linestyle="--", alpha=0.7)
    ax.axvline(0, color="#333333", linewidth=0.9, alpha=0.7)
    ax.set(xlim=(-1, 3), xlabel="Time from movement midpoint (s)",
           ylabel="Mean GrC activity (z-scored)",
           title="Source-data reproduction: interval-related GrC time profiles")
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT, format="svg", metadata={"Date": None})
    plt.close(fig)
    lines = OUT.read_text(encoding="utf-8").splitlines()
    OUT.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
