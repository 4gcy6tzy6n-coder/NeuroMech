# M5 interval-retuning: source-data reproduction contract

**Status:** exploratory reproduction of an already published analysis; this is not a preregistered or independent biological confirmation.

## Question

Does the acquired 1 s-to-2 s source release reproduce the source-defined extension of movement-aligned granule-cell (GrC) activity during long-interval learning?

## Source-defined conditions and filters

Use the three condition labels in `learning_1s_to_2s_GrC_CF.m`: `1-s expert`, `2-s novice / 1-s expert`, and `2-s expert`. Preserve the source's rewarded-trial filter: `rewarded & goodmvdir` and reward delay `(rewtimes - midpt) * dtb` greater than 0.75 s for the 1-s expert group, or greater than 1.75 s for the 2-s groups. Use `midAlgn.sigFilt_GrC` and `tmpxCb`, with the baseline interval `[-1, 0]` s and analysis interval `[0, 2]` s relative to movement midpoint.

The reproduction uses all trials meeting those source filters rather than MATLAB's random/first-50 display subsampling, so it is a transparent full-eligible-trial reanalysis rather than a byte-for-byte recreation of the plotted sample.

## Outcomes

For each source group and session, compute:

1. Mean GrC activity over eligible trials, with each session contributing equally to the group time profile.
2. Per-cell active duration in `[0, 2]` s: number of time bins where mean activity exceeds that cell's mean baseline, multiplied by the session's `dtimCb`.
3. Per-cell activity-weighted time centroid in `[0, 2]` s using the source code's positive-above-baseline mask and raw activity values; report session medians and distributions descriptively.

No cell-level inferential statistics, p-values, or independent biological replication claims will be made. Cells are nested within sessions and sessions within source group/mouse. Any quantitative extension beyond this source reproduction will use source-defined biological replicate identifiers if they can be established from the dataset or paper.

## Interpretation boundary

Agreement with the paper shows that the downloaded data and this reimplementation recover a previously published pattern. It does not provide new biological validation. The paper's climbing-fiber-dependent synaptic-weight computation is modeled rather than directly measured. Any AI-side benefit must be tested separately against strong, capacity-matched models and task-aware baselines.
