# Figure QA record

- Figure source: `model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/plot_results.py` (Python/Matplotlib; saved Python backend preference).
- Core inference: primary-condition matched comparison plus the operating-boundary grid; each heat-map value is the mean of paired test-episode MSE differences. The crossed-bootstrap 95% interval and `n` are printed below the heat map.
- Final size: 180 × 91 mm; 600-dpi raster exports; editable SVG/PDF text.
- Source preflight: 19 PASS, 0 FAIL, 2 WARN; full report is in `source-validation.json`. The width warning reflects that the validator cannot evaluate the named `FIGSIZE_IN` constant; rendered PDF dimensions are 180 mm wide. Its uncertainty-encoding warning is limited to heat-map cells: intervals are not encoded per cell, and only the prespecified primary contrast and direct controls have crossed-bootstrap intervals in the machine-readable summary. Do not interpret the secondary cells as individually significant.
- PDF glyph audit: PASS; minimum rendered text 6 pt, no glyph below 5 pt; machine report is in `pdf-text-audit.json`.
- Collision audit: PASS; 0 FAIL, 0 WARN.
- Alignment: one plot area; multi-panel alignment is not applicable.
- Visual review: inspected the final PNG at display scale. Condition labels, cell signs/values, primary-condition outline, and oracle row are legible; near-zero values display as `+0.000` to avoid a false visual sign.
- Source data: all 368,640 episode rows are retained in `canonical/episode_results.csv`; the heat map aggregates by condition and arm using arithmetic means across the full paired grid.
