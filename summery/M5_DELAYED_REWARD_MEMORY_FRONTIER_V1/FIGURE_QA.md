# Figure QA — M5 delayed-reward bandit memory frontier V1

## Evidence layout

Four aligned panels show one reward delay per panel (D=1, 4, 16, 64). Each panel plots held-out expected reward against active score-state values on the same log2 scale. The eligibility trace is highlighted; exact FIFO points trace the state/accuracy frontier; current-score assignment is a muted same-state reference; exact replay is marked where it coincides with a FIFO whose capacity covers the delay. Each mean has a 95% bootstrap interval over 30 task seeds.

The figure note reports update coverage limitations for the one-vector FIFO, since its accuracy at longer delays reflects that it drops almost all reward updates. The error bars are descriptive intervals, not pairwise significance tests. Exact FIFO and full replay overlap at adequate capacity because the verifier checked exact equality at every task seed and delay.

## Export and automated QA

- Canvas: 183 mm wide × 112 mm high; raster exports: 600 dpi PNG and TIFF; vector exports: PDF and editable-text SVG.
- Source: [`figure_source.py`](../../model/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/figure_source.py); plotted seed means and intervals: [`figure_source_data.csv`](../../data/results/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/figures/figure_source_data.csv).
- Static figure preflight: 18 PASS, 3 WARN, 0 FAIL. All warnings are understood: final dimensions are set by `WIDTH_IN`/`HEIGHT_IN` and verified from the PDF; the apparent simulated-data warning is the seed bootstrap RNG (observations are read from the canonical task-metric CSV); the log-axis warning is harmless because every active-state x value is explicitly positive (32–2,048).
- Render-time panel alignment: PASS at 1.5 pt tolerance.
- PDF text audit: PASS; 35 text runs, minimum 5.5 pt, none below 5 pt.
- Rendered collision audit: PASS; 0 FAIL, 0 WARN, 4 contained marker/fill overlays reviewed as intentional.
- Final-size visual review: all four panels, axes, shared legend, intervals, annotations, and bottom note inspected; no clipping or overlap observed.

The plot is a research figure for this exploratory result, not a final manuscript figure or evidence of NMI publication readiness.
