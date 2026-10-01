# M2 AIY state decoding — failure and limitation log

- **Wrong source table for the initial question:** the oscillating-temperature Figure 5 trace table does not expose locomotion state. It cannot support a temperature × motor-state analysis and was excluded rather than having state imputed.
- **Nonuniform workbook layout:** WT trace 5 includes an extra temperature column; the sixth labeled block lacks locomotion-state labels. The first runner stopped before writing outcome scores. Explicit column maps now retain the five complete WT state traces, matching the source figure's stated N=5. This parser correction was committed and pushed before rerunning the analysis.
- **Small biological sample:** only five animals per group are present in the selected constant-temperature source sheets. Time samples and CV folds are not independent animals.
- **Behavioral persistence ceiling:** previous-sample locomotion state nearly saturates held-out AUC, leaving little range for neural activity to add. AIY-only decoding is therefore reported alongside incremental decoding beyond prior behavior.
- **Internal-control ambiguity:** AVA also shows a WT-versus-RIM-ablated shift in its small incremental AUC. The result does not demonstrate AIY-specific residual information.
- **Retrospective cohort comparison:** the groups and analysis were already described in the published paper. Exact label permutations assume exchangeability and are reported only as descriptive references.
- **Scope boundary:** constant-temperature recordings test motor-state representation without a thermal stimulus; they do not quantify state-dependent thermal gain or AI performance.
