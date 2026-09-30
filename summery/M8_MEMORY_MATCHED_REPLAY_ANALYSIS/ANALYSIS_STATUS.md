# M8 memory-matched replay comparison

**Status:** post-result exploratory analysis. M8 outcomes were already known when this contrast was selected. It is not a preregistered test or a new independent experiment.

## Question and accounting rule

Compare exact replay with the truncated horizon matched to each feedback delay (`HORIZON_D`) using the same active feature-history budget: D × 64 float values. This is an algorithmic state-size accounting from the M8 contract, not measured process memory; the runner holds source task arrays in shared experiment memory for all arms, and all arms share delayed prediction history.

## Analysis

Outcome is paired held-out accuracy difference `EXACT_REPLAY − HORIZON_D`. For the across-condition contrast, first average equally across the three input correlations and three delays within each task seed, then average over the 30 independent task seeds. A 20,000-draw paired task-seed bootstrap gives a descriptive 95% percentile interval. Report delay-specific contrasts and all cells; no p-values or confirmatory/multiplicity claims.

## Interpretation boundary

This reuses the M8 outcomes and task seeds, so it adds no independent replication. The comparison concerns one synthetic random-feature classification family and idealized active learner-state size. It does not establish a general memory-efficiency result, biological transfer, superiority on other tasks, or an NMI-level contribution.
