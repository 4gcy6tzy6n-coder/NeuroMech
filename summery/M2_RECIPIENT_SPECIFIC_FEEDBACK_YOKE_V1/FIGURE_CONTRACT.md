# Figure contract — M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1

## Core conclusion

In the tested sparse-tracking simulator, reassigning the learned sensory-site motor signal to another episode while preserving its timestep-wise cohort distribution increases tracking error; the effect is an artificial recipient-specific contingency result, not biological validation.

## Figure question and panels

**Question:** Does disrupting the recipient-to-signal correspondence change tracking, and how does that contrast vary across the tested task grid?

- **Panel a (primary):** For each of 32 training-seed blocks, plot the mean held-out paired difference `MSE(cross-agent yoke) − MSE(self-feedback)` at hazard `1/120` and missingness `0.50`. Show the grand paired mean and the frozen crossed seed/episode bootstrap 95% interval. Positive values favor self-feedback.
- **Panel b (operating range):** Show the mean paired self-versus-yoke MSE difference in the 3 × 3 hazard × missingness grid. This panel is descriptive; it does not add nine confirmatory tests.

No panel compares unlike biological or artificial outcomes. Do not interpret panel b's color scale as significance or a confidence interval.

## Archetype, outputs and risks

- Archetype: two-panel quantitative comparison with matched panel plot-area dimensions.
- Target: NMI review-stage evidence figure, 180 mm width and 85 mm height; editable PDF/SVG and 600-dpi PNG/TIFF.
- Include raw per-seed primary dots; use the crossed bootstrap interval only for the primary aggregate.
- Main risks: post-result exploratory status, reused task family, the yoke's replay nature, the small direct-control contrast, and the task-aware oracle's superiority. Put the first three in the legend and detailed text; preserve control and oracle results in the linked Results record.
- Preserve panel alignment JSON, PDF text audit, collision audit, source-data references, and a hash manifest.

## Data and exclusions

Use the canonical episode-level outcome grid. No row is excluded or subsampled. The primary data are paired episode MSE values for `SENSORY_SELF` and `SENSORY_CROSS_AGENT_YOKE`; the heatmap uses all seed and episode rows in each of the nine task cells.
