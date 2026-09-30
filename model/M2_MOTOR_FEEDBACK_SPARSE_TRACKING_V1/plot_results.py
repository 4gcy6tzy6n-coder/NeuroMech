#!/usr/bin/env python3
"""Render a single-panel condition-boundary figure from archived summaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 7,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.75,
    "legend.frameon": False,
})

ROOT = Path(__file__).resolve().parents[2]
ID = "M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1"
DEFAULT_RESULTS = ROOT / "data" / "results" / ID / "canonical"
DEFAULT_OUT = ROOT / "data" / "results" / ID / "figures"
FIGSIZE_IN = (7.0866, 3.5827)  # 180 × 91 mm at final physical size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    summary = json.loads((args.results_dir / "summary.json").read_text())
    conditions = list(summary["means_by_condition"])
    rows = ["GENERIC_RNN_1H", "OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "ORACLE_RELATIVE_ERROR"]
    labels = ["Generic RNN (1 state)", "Output-site persistence", "No feedback", "Task-aware oracle"]
    values = np.array([[summary["means_by_condition"][c][a]["tracking_mse"]
                        - summary["means_by_condition"][c]["SENSORY_SITE_FEEDBACK"]["tracking_mse"]
                        for c in conditions] for a in rows])
    # Positive values mean lower error for the sensory-site feedback model.
    bound = float(max(np.abs(values.min()), np.abs(values.max())))
    cmap = LinearSegmentedColormap.from_list("benefit_boundary", ["#D27B61", "#F4E8DD", "#FFFFFF", "#D8ECE8", "#3B8C83"])

    fig, ax = plt.subplots(figsize=FIGSIZE_IN)
    image = ax.imshow(values, cmap=cmap, norm=TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound), aspect="auto")
    ax.set_yticks(np.arange(len(rows)), labels=labels)
    hlabels = {1/240: "1/240", 1/120: "1/120", 1/40: "1/40"}
    xlabels = [f"{hlabels[min(hlabels, key=lambda h: abs(h - float(c.split(';')[0].split('=')[1])))]}\n{int(round(float(c.split('missing=')[1]) * 100))}%" for c in conditions]
    ax.set_xticks(np.arange(len(conditions)), labels=xlabels)
    ax.set_xlabel("Target-switch hazard\nSensory samples missing")
    ax.set_title("Tracking advantage depends on target dynamics and missingness", loc="left", pad=9, fontsize=8.5, weight="bold")
    ax.set_ylabel("Comparator")
    ax.tick_params(axis="both", length=0, pad=3)
    ax.set_xticks(np.arange(-0.5, len(conditions), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.3)
    ax.tick_params(which="minor", bottom=False, left=False)
    for r in range(len(rows)):
        for c in range(len(conditions)):
            val = values[r, c]
            ink = "#183B39" if val >= 0 else "#633B2D"
            display = "+0.000" if abs(val) < 0.0005 else f"{val:+.3f}"
            ax.text(c, r, display, ha="center", va="center", fontsize=6.5, color=ink)
    # Emphasize the frozen training condition; all other cells remain visible.
    primary_col = conditions.index("hazard=0.0083333333;missing=0.50")
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((primary_col - 0.48, -0.48), 0.96, 2.96, fill=False,
                           edgecolor="#272727", linewidth=1.2, clip_on=False))
    cb = fig.colorbar(image, ax=ax, fraction=0.027, pad=0.025)
    cb.set_label("Δ MSE", fontsize=6.5, labelpad=5)
    cb.ax.tick_params(labelsize=6, length=2)
    primary = summary["primary_generic_control"]
    direct = summary["direct_matched_controls"]
    foot = ("Training condition: hazard 1/120, 50% missing. Generic RNN − feedback = "
            f"{primary['mean_competitor_minus_sensory_mse']:+.5f} "
            f"(crossed 95% CI {primary['crossed_bootstrap_ci95'][0]:+.5f} to {primary['crossed_bootstrap_ci95'][1]:+.5f}); "
            f"output and no-feedback contrasts = {direct['OUTPUT_SITE_PERSISTENCE']['mean_competitor_minus_sensory_mse']:+.4f}, "
            f"{direct['NO_FEEDBACK']['mean_competitor_minus_sensory_mse']:+.4f}. "
            "32 training seeds × 256 paired test episodes per condition.")
    fig.text(0.115, 0.015, foot, ha="left", va="bottom", fontsize=6.1, wrap=True)
    fig.subplots_adjust(left=0.205, right=0.94, top=0.86, bottom=0.25)

    # This is a single plot-area figure; record the alignment gate as not applicable.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        from audit_panel_alignment import require_matplotlib_panel_alignment
        require_matplotlib_panel_alignment(fig, json_out=args.output_dir / "figure.alignment.json",
                                           tolerance_pt=1.5, strict=True)
    except ImportError as exc:
        raise RuntimeError("Set PYTHONPATH to the nature-figure audit scripts before rendering") from exc

    prefix = args.output_dir / "M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1"
    fig.savefig(Path(str(prefix) + ".svg"))
    fig.savefig(Path(str(prefix) + ".pdf"))
    fig.savefig(Path(str(prefix) + ".png"), dpi=600)
    fig.savefig(Path(str(prefix) + ".tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    print(f"wrote figure bundle to {args.output_dir}")


if __name__ == "__main__":
    main()
