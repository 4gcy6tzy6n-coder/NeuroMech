"""Minimal reproducible Matplotlib panel-alignment gate for the V2 figure."""
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
    require_panel_labels: bool = False,
    strict: bool = False,
    panel_ids: dict[Any, str] | None = None,
) -> dict[str, Any]:
    """Measure a single row of comparable panels and fail on misalignment."""
    fig.canvas.draw()
    width_in, height_in = fig.get_size_inches()
    panel_ids = panel_ids or {}
    panels = []
    for index, ax in enumerate(ax for ax in fig.axes if ax.get_visible()):
        x0, y0, width, height = ax.get_position().bounds
        panel_id = panel_ids.get(ax, chr(ord("a") + index))
        bbox = [x0 * width_in * 72, y0 * height_in * 72,
                (x0 + width) * width_in * 72, (y0 + height) * height_in * 72]
        panels.append({
            "id": panel_id,
            "bbox_pt": bbox,
            "grid_id": "single-row",
            "row_start": 0,
            "row_stop": 1,
            "col_start": index,
            "col_stop": index + 1,
            "panel_label": panel_id,
            "panel_label_anchor_pt": [bbox[0], bbox[3] + 6],
        })
    if len(panels) < 2:
        raise ValueError("alignment audit requires at least two visible panels")
    widths = [p["bbox_pt"][2] - p["bbox_pt"][0] for p in panels]
    heights = [p["bbox_pt"][3] - p["bbox_pt"][1] for p in panels]
    bottoms = [p["bbox_pt"][1] for p in panels]
    tops = [p["bbox_pt"][3] for p in panels]
    gutters = [panels[i + 1]["bbox_pt"][0] - panels[i]["bbox_pt"][2] for i in range(len(panels) - 1)]
    metrics = {
        "width_spread_pt": max(widths) - min(widths),
        "height_spread_pt": max(heights) - min(heights),
        "bottom_spread_pt": max(bottoms) - min(bottoms),
        "top_spread_pt": max(tops) - min(tops),
        "gutter_spread_pt": max(gutters) - min(gutters) if len(gutters) > 1 else 0.0,
    }
    findings = [name for name, value in metrics.items()
                if value > (gutter_tolerance_pt if name.startswith("gutter") else tolerance_pt)]
    layout = {
        "schema_version": 1,
        "backend": "python-matplotlib",
        "figure": {"width_pt": width_in * 72, "height_pt": height_in * 72},
        "panels": panels,
        "row_groups": [{"id": "single-row", "panels": [p["id"] for p in panels]}],
        "column_groups": [],
        "boundary_groups": [],
        "exemptions": [],
    }
    report = {
        "schema_version": 1,
        "applicable": True,
        "auditable": True,
        "verdict": "FIX BEFORE DELIVERY" if findings else "PASS",
        "backend": "python-matplotlib",
        "summary": {"fail": len(findings), "warn": 0, "comparisons": len(panels) - 1, "exemptions": 0},
        "tolerances": {"alignment_pt": tolerance_pt, "gutter_pt": gutter_tolerance_pt},
        "layout": layout,
        "findings": [{"severity": "FAIL", "check": name, "metrics": metrics} for name in findings],
    }
    if json_out is not None:
        Path(json_out).write_text(json.dumps(report, indent=2) + "\n")
    if findings and (strict or require_panel_labels):
        raise ValueError(f"panel alignment failed: {', '.join(findings)}")
    return report
