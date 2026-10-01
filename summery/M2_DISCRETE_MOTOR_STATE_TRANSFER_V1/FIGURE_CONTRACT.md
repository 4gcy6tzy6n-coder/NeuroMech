# Figure contract — M2 discrete-state transfer V1

**Core conclusion:** In the long-gap synthetic condition, realized binary movement-state input improves tracking relative to intended action sign, but the comparisons with zero and recipient-yoked input remain unresolved.

**Results question:** Does categorical realized motor-state feedback outperform key matched ablations on the single preselected `LONG_BURST` endpoint?

**Archetype / target:** Single-panel quantitative forest plot for an NMI Article review figure; Python/matplotlib; 180 mm wide, vector SVG/PDF plus 600-dpi TIFF.

**Panel:** One panel shows four paired seed-block contrasts `SELF_STATE − comparator`, with 95% seed-block bootstrap intervals and a zero reference. Negative values favor `SELF_STATE`; the action-sign comparison is the primary contrast and is visually emphasized. The zero, yoke, and fixed-reactive comparisons are secondary controls.

**Statistics and source:** 32 training-seed blocks; each point is the mean paired contrast across blocks. Error bars are percentile 95% bootstrap intervals over seed blocks (20,000 draws, fixed seed 8,765,501). Source rows: canonical `seed_summary.csv`; summary is recomputed by plotting source from paired block-level values.

**Reviewer risk:** The figure must not imply the primary advantage is self-contingency-specific: zero-input and recipient-yoke intervals cross zero. The fixed reactive reference is not capacity matched. Label the study as exploratory and synthetic in the legend.
