"""Reproducible Matplotlib alignment check for the yoke study's plot panels."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def require_matplotlib_panel_alignment(
    fig: Any,
    *,
    json_out: str | Path | None = None,
    tolerance_pt: float = 1.5,
    gutter_tolerance_pt: float = 1.5,
    strict: bool = False,
    panel_ids: dict[Any, str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Measure comparable axes, record their layout, and block misalignment."""
    fig.canvas.draw()
    width_in, height_in = fig.get_size_inches()
    selected = list(panel_ids.items()) if panel_ids else [
        (ax, chr(ord("a") + i)) for i, ax in enumerate(fig.axes) if ax.get_visible()
    ]
    panels = []
    for index, (ax, label) in enumerate(selected):
        x0, y0, width, height = ax.get_position().bounds
        bbox = [x0 * width_in * 72, y0 * height_in * 72,
                (x0 + width) * width_in * 72, (y0 + height) * height_in * 72]
        panels.append({"id": label, "bbox_pt": bbox, "grid_id": "single-row",
                       "row_start": 0, "row_stop": 1, "col_start": index,
                       "col_stop": index + 1, "panel_label": label,
                       "panel_label_anchor_pt": [bbox[0], bbox[3] + 5]})
    if len(panels) < 2:
        raise ValueError("alignment gate requires at least two explicitly comparable axes")
    widths = [p["bbox_pt"][2] - p["bbox_pt"][0] for p in panels]
    heights = [p["bbox_pt"][3] - p["bbox_pt"][1] for p in panels]
    bottoms = [p["bbox_pt"][1] for p in panels]
    tops = [p["bbox_pt"][3] for p in panels]
    gutters = [panels[i + 1]["bbox_pt"][0] - panels[i]["bbox_pt"][2] for i in range(len(panels) - 1)]
    checks = {"width": max(widths) - min(widths), "height": max(heights) - min(heights),
              "bottom": max(bottoms) - min(bottoms), "top": max(tops) - min(tops),
              "gutter": max(gutters) - min(gutters) if len(gutters) > 1 else 0.0}
    failed = [name for name, value in checks.items()
              if value > (gutter_tolerance_pt if name == "gutter" else tolerance_pt)]
    layout = {"schema_version": 1, "backend": "python-matplotlib",
              "figure": {"width_pt": width_in * 72, "height_pt": height_in * 72},
              "panels": panels, "row_groups": [{"id": "single-row", "panels": [p["id"] for p in panels]}],
              "column_groups": [], "boundary_groups": [], "exemptions": []}
    report = {"schema_version": 1, "applicable": True, "auditable": True,
              "verdict": "FIX BEFORE DELIVERY" if failed else "PASS",
              "backend": "python-matplotlib",
              "summary": {"fail": len(failed), "warn": 0, "comparisons": len(panels) - 1, "exemptions": 0},
              "tolerances": {"alignment_pt": tolerance_pt, "gutter_pt": gutter_tolerance_pt},
              "metrics_pt": checks, "layout": layout,
              "findings": [{"severity": "FAIL", "check": item, "metrics_pt": checks} for item in failed]}
    if json_out is not None:
        Path(json_out).write_text(json.dumps(report, indent=2) + "\n")
    if failed and strict:
        raise ValueError(f"panel alignment failed: {', '.join(failed)}")
    return report
