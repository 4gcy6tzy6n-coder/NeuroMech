# Figure QA — M2 discrete-state transfer V1

- Core claim and panel map: [`FIGURE_CONTRACT.md`](FIGURE_CONTRACT.md).
- Source preflight: ready, 20 passes, 1 warning, 0 failures. The warning flags `np.random.default_rng`; here it is used only for the declared percentile bootstrap over 32 seed blocks, not to simulate plotted observations.
- Visual review: the whole 95% interval for each contrast is visible; the zero reference is clear; the primary contrast is visually emphasized; no label overlaps were apparent at review size.
- PDF glyph audit: pass; minimum rendered text size 7 pt, above the 5 pt floor.
- Render-time panel alignment: single panel, not applicable.
- Automated collision audit: pass; 0 fail, 0 warn, and 0 contained overlays across 12 text boxes and 35 stroke paths. PyMuPDF was installed into a temporary QA-only directory and was not added to project dependencies.
- Outputs: editable-text SVG and PDF; 600-dpi TIFF; source-data JSON.
