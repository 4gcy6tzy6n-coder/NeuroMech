#!/usr/bin/env python3
"""Plot paired self-minus-yoked progress across reversal schedules."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SKILL_SCRIPTS = Path.home() / ".codex/skills/nature-figure/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

RESULTS = ROOT / "data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical"
FIG_BASE = RESULTS / "Figure_M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1"
INTERVALS = (0.0, 40.0, 20.0, 10.0, 5.0)

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 8,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.8,
    "legend.frameon": False,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
})


def main() -> None:
    with (RESULTS / "seed_block_metrics.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    by_key = {(int(r["seed_block"]), float(r["reversal_interval_s"]), r["arm"]):
              float(r["aligned_progress_rate"]) for r in rows}
    seeds = sorted({key[0] for key in by_key})
    summary = json.loads((RESULTS / "summary.json").read_text())
    source_rows = []
    means, low, high = [], [], []
    for interval in INTERVALS:
        diffs = np.asarray([
            by_key[(seed, interval, "SELF_CONTINGENT")]
            - by_key[(seed, interval, "CROSS_AGENT_YOKED")]
            for seed in seeds
        ])
        contrast = summary["means_and_contrasts_by_interval"][str(interval)]["contrasts"][
            "self_minus_cross_agent_yoked_progress"
        ]
        mean = float(contrast["mean"])
        lo, hi = map(float, contrast["ci95_seed_block_bootstrap"])
        means.append(mean)
        low.append(mean - lo)
        high.append(hi - mean)
        for seed, delta in zip(seeds, diffs):
            source_rows.append({"seed_block": seed, "reversal_interval_s": interval,
                                "self_minus_yoked_progress_rate": float(delta)})

    source_path = RESULTS / "figure_source_data.csv"
    with source_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(source_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(source_rows)

    width_mm = 180.0
    height_mm = 90.0
    fig, ax = plt.subplots(figsize=(width_mm / 25.4, height_mm / 25.4), constrained_layout=True)
    x = np.arange(len(INTERVALS))
    colors = ["#708090", "#708090", "#24788F", "#708090", "#A65A5A"]
    for i in range(len(INTERVALS)):
        ax.errorbar(x[i], means[i], yerr=[[low[i]], [high[i]]], fmt="o", ms=5.2,
                    color=colors[i], ecolor=colors[i], elinewidth=1.2, capsize=3.2,
                    capthick=1.0, zorder=3)
        label_y = means[i] + high[i] if means[i] >= 0 else means[i] - low[i]
        ax.annotate(f"{means[i]:+.3f}", (x[i], label_y), xytext=(0, 6 if means[i] >= 0 else -7),
                    textcoords="offset points", ha="center", va="center", fontsize=7,
                    color=colors[i])
    ax.axhline(0, color="#30343B", linewidth=0.8, linestyle=(0, (3, 2)), zorder=1)
    ax.set_xticks(x, ["Stationary", "40", "20", "10", "5"])
    ax.set_xlabel("Warm-gradient reversal interval (s)")
    ax.set_ylabel("Self-contingent − yoked aligned progress\n(model-distance units per second)")
    ax.set_xlim(-0.45, 4.45)
    ax.set_ylim(-0.012, 0.084)
    ax.set_title("Recipient-specific feedback advantage depends on reversal rate", loc="left", fontsize=10, pad=10)
    ax.text(0.99, 0.96, "Mean paired difference; 95% seed-block bootstrap CI; n = 100",
            transform=ax.transAxes, ha="right", va="top", fontsize=7, color="#40464F")
    ax.tick_params(length=3, pad=3)
    ax.spines["left"].set_color("#60666F")
    ax.spines["bottom"].set_color("#60666F")
    require_matplotlib_panel_alignment(
        fig,
        json_out=f"{FIG_BASE}.alignment.json",
        overlay_svg=f"{FIG_BASE}.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
    )
    fig.savefig(FIG_BASE.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(FIG_BASE.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(FIG_BASE.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    fig.savefig(FIG_BASE.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    def file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    figure_paths = [FIG_BASE.with_suffix(ext) for ext in (".pdf", ".svg", ".tiff", ".png")]
    manifest = {
        "figure_id": "Figure_M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1",
        "core_claim": "Recipient-specific sensory-site feedback improves aligned displacement over a population-marginal-matched yoke at stationary through 10-s reversal schedules, while the small contrast reverses at 5 s in this source-model simulation.",
        "archetype": "single-panel paired quantitative contrast",
        "backend": "Python / Matplotlib",
        "physical_size_mm": [width_mm, height_mm],
        "primary_condition_s": 20.0,
        "uncertainty": "two-sided 95% percentile bootstrap over 100 paired simulation seed blocks; 20,000 draws; seed 20261015 for primary condition",
        "figure_source_data": source_path.name,
        "plot_script_sha256": file_sha256(Path(__file__).resolve()),
        "summary_input_sha256": file_sha256(RESULTS / "summary.json"),
        "figure_source_data_sha256": file_sha256(source_path),
        "export_sha256": {path.name: file_sha256(path) for path in figure_paths},
        "formats": ["PDF", "SVG", "TIFF 600 dpi", "PNG 300 dpi"],
    }
    (RESULTS / "figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote figure assets to {FIG_BASE}")


if __name__ == "__main__":
    main()
