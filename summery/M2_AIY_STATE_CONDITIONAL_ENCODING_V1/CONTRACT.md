# M2_AIY_STATE_CONDITIONAL_ENCODING_V1 — public source-data reanalysis contract

**Classification:** retrospective, outcome-informed reanalysis of published *C. elegans* source data. This is not a new animal experiment, independent confirmation, or AI-transfer result.

## Question

In constant-temperature recordings, how well does AIY activity alone predict forward versus reversal state, and is that out-of-sample decoding weaker after RIM ablation? AVA is a prespecified internal comparator because it is a premotor state-coding neuron in the source paper.

This estimates the motor-state information present in AIY without fluctuating thermal input. It does not estimate sensory gating itself or prove the causal route. The source paper's optogenetic and ablation experiments supply the causal biological context; this reanalysis quantifies a restricted, publicly released time-series view.

## Source data and units

- Wild type: eLife 68848 Figure 2 source-data workbook, sheet `Fig 2HI_const temp`. The sheet labels six columns/groups, but only five contain a complete motor-state trace; use those five, consistent with the figure's stated `N=5`.
- RIM ablation: Figure 5 source-data workbook, sheet `Fig 5C,S1B`, five labeled animal traces.
- Exact workbook hashes and byte sizes are recorded in `data/results/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/source_manifest.json`.
- Independent biological unit: animal. Time samples are repeated measures and are never treated as independent replicates.
- Group sizes are small (5 WT, 5 RIM-ablated) and not randomized within this reanalysis; show each animal and treat group uncertainty as descriptive.

## Fixed analysis

For each animal, decode the current locomotion state (`forward=1`, `reversal=-1`; omit transition/unknown state `0`) using logistic regression. The behavioral baseline is previous-sample locomotion state. The augmented predictor adds current AIY calcium; the internal comparator adds AVA calcium instead. Also report AIY-only and AVA-only decoding as secondary summaries. Use ten contiguous time blocks as folds; exclude a 10-second buffer around each test block from training. Standardization is fit on each training fold only. Fix `C=1.0`, solver, and fold boundaries before scoring.

The primary per-animal outcome is the held-out AUC gain `AUC(previous state + AIY) − AUC(previous state)`. The primary group contrast is mean animal AUC gain in WT minus mean gain after RIM ablation. Report every animal, group means, an animal-level bootstrap interval, and an exact group-label permutation reference over all 252 allocations of 5/5 labels. For AVA, report the same incremental decoding as an internal comparison. Do not use time samples, folds, or transitions as independent replicates.

## Interpretation boundary

Higher incremental AIY state-decoding AUC in WT than after RIM ablation, alongside a smaller group difference for AVA, is consistent with RIM-dependent motor-state information reaching AIY. Similar gains, poor WT decoding, or a comparable AVA group difference would weaken this reanalysis's interpretation. Because this uses a small retrospective source cohort and classification of correlated time series, it cannot establish a new causal effect, isolate a unique synaptic pathway, quantify sensory-gain gating, or demonstrate AI benefit.

## Provenance and schema deviation

Source: Ji et al. (2021), *eLife* 10:e68848, [article and source-data index](https://elifesciences.org/articles/68848/figures). The initially considered oscillating-temperature Figure 5 table does not expose a locomotion-state field, so it is excluded rather than imputed. The analysis uses only the explicit constant-temperature tables above. Raw workbooks are preserved under `data/raw/celegans/ji_etal_2021_elife_68848_v3/`; runner/verifier are under `model/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/`, results under `data/results/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/`, and interpretation/failure notes in this folder.

### Pre-outcome schema correction

The first runner attempt stopped before writing any animal-level results. Workbook inspection showed that WT animals 1–4 use a four-column layout, animal 5 has an extra temperature column before locomotion state, and the sixth labeled group has no state labels. The parser now uses explicit per-animal column layouts and includes only the five complete state traces. No neural decoding scores or group contrasts were produced before this correction. This correction was pushed as a separate commit before the analysis was rerun.
