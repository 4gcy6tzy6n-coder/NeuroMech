#!/usr/bin/env python3
"""Render the fixed, descriptive plots from archived V1 metrics."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1"
summary = json.loads((OUT / "summary.json").read_text())
coverages = [0.25, 0.50, 0.75, 0.90]
styles = {
    "AUTHOR_STYLE_CNN": ("Author-style CNN", "#0072B2", "o"),
    "COUNTEREVIDENCE_MODEL": ("Counterevidence CNN", "#D55E00", "s"),
    "SHAM_CHANNEL_CNN": ("Shuffled-cue CNN", "#009E73", "^"),
    "FLOW_FIELD_COHERENCE": ("Local-flow coherence", "#666666", "D"),
}
fig, ax = plt.subplots(1, 2, figsize=(11.2, 4.4), gridspec_kw={"width_ratios": [1.45, 1]})
for key, (label, color, marker) in styles.items():
    vals = [summary["cell_means"][key][str(c)]["object_motion_fpr"] for c in coverages]
    ax[0].plot(coverages, vals, marker=marker, label=label, color=color, linewidth=2)
ax[0].set(xlabel="Moving-object coverage", ylabel="Object-motion false-positive rate",
          title="Held-out panorama scenes")
ax[0].set_xticks(coverages, ["25%", "50%", "75%", "90%"])
ax[0].set_ylim(-.03, 1.03)
ax[0].grid(axis="y", alpha=.25)
ax[0].legend(frameon=False, fontsize=8)

names = ["AUTHOR_STYLE_CNN", "SHAM_CHANNEL_CNN"]
labels = ["vs author-style CNN", "vs shuffled-cue CNN"]
means, low, high = [], [], []
for name in names:
    item = summary["primary"][f"CE_minus_{name}_high_coverage_object_motion_FPR"]
    means.append(item["mean"])
    low.append(item["mean"] - item["scene_group_bootstrap_95_ci"][0])
    high.append(item["scene_group_bootstrap_95_ci"][1] - item["mean"])
ax[1].errorbar(means, [1, 0], xerr=np.asarray([low, high]), fmt="o", color="#D55E00",
               capsize=4, linewidth=2)
ax[1].axvline(0, color="#333333", linewidth=1, linestyle="--")
ax[1].set_yticks([1, 0], labels)
ax[1].set_xlabel("Δ object-motion false-positive rate\n(counterevidence − comparator)")
ax[1].set_title("High coverage: 75% and 90%")
ax[1].grid(axis="x", alpha=.25)
fig.suptitle("Drosophila-inspired stationary counterevidence — exploratory image-rendering pilot", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "natural_scene_transfer_summary.png", dpi=180, bbox_inches="tight")
