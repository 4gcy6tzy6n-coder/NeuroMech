# Figure contract — M5 eligibility/memory frontier V1

**Results-level question:** Can the fixed eligibility trace improve delayed-credit accuracy when exact replay is restricted to the same small active feature-state budget, and what accuracy cost remains relative to larger replay buffers?

**Figure-level claim:** Across the three tested input generators, a 64-value eligibility trace trades accuracy for compact state: it loses to exact replay at delay 1, improves over a one-vector FIFO at delays 4–64, and remains below exact replay once enough replay memory is available.

**Archetype:** quantitative grid; three aligned generator panels (IID Gaussian, AR(1) Gaussian, sparse sign).

**Panel roles:** Each panel displays task-seed mean held-out accuracy against actual peak active feature-state values. Exact FIFO/replay points expose the accuracy-memory frontier by delay; delay-specific trace points and the delay-averaged current-feature point at 64 values show the fixed-budget alternatives. Panels preserve the generator strata; no scores are pooled across tasks for the plotted series.

**Data and uncertainty:** All 30 task seeds per generator and four delays are retained. Exact-replay and trace points show arithmetic mean accuracy; vertical bars show percentile 95% bootstrap intervals over task seed (20,000 resamples) within each fixed generator×delay×arm cell. The current-feature point averages the four delays within each task seed before computing its mean and interval. Arm comparisons use the same task seeds. No multiple-comparison claim is made from this descriptive figure.

**Output contract:** double-column width 183 mm; PDF with editable text, SVG and 600-dpi PNG; 5-pt minimum PDF glyph; equal plot-area widths, shared y scale, and 1.5-pt alignment tolerance. Include the plotting source, alignment JSON, PDF text audit, and collision audit with the figure.

**Failure modes guarded against:** do not omit the delay-1 reversal; do not imply memory and accuracy are interchangeable; do not display full replay as a same-budget baseline; do not call algorithmic state values measured RAM or energy; keep the M5 synthetic/task-limited scope explicit.
