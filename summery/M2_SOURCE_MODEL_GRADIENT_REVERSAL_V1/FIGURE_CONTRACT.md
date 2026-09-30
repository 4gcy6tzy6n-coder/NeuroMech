# Figure contract — gradient-reversal stress test

**Core conclusion:** In the translated Ji et al. source model, sensory-site feedback increases simulated warm-direction progress relative to no feedback across the tested gradient schedules, while moving the same coefficient into the motor equation saturates the output arm and does not provide a valid site-matched comparison.

**Results question:** Does sensory-site feedback retain simulated gradient-aligned progress as the preferred direction reverses, and does the output-site control support a site-specific inference?

**Archetype and destination:** Two-panel quantitative figure, suitable as exploratory Supplementary/Extended Data material if this line enters an NMI Article. Final dimensions 180 mm × 90 mm; Python/matplotlib; PDF, SVG, and 300-dpi TIFF/PNG.

| Panel | Role | Evidence |
|---|---|---|
| a | Hero result and primary-control diagnostic | Paired seed-block progress-rate contrasts: sensory-site minus no feedback and sensory-site minus output-site across all reversal schedules. The output-site series is explicitly marked as compromised by saturation. |
| b | Control adequacy / failure boundary | Forward-state occupancy by arm across the same schedules, revealing 100% occupancy in the output-site arm. |

**Evidence hierarchy:** 100 paired simulation seed blocks, 50 agents per block, source-derived update equations. The inferential unit is the seed block; agents and time steps are not independent. Error bars are paired or seed-block percentile bootstrap 95% intervals from 20,000 resamples.

**Source data:** `canonical/seed_block_metrics.csv`; the unmodified per-block observations are retained. No values are excluded.

**Reviewer risk:** All evidence is simulated. The output-site control saturates, so the nominal sensory-versus-output contrast cannot support a feedback-site causal claim. Panel a keeps the valid feedback-versus-ablation contrast visible; panel b exposes the failed comparator.
