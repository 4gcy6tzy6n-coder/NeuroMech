# M2_AIY_STATE_CONDITIONAL_ENCODING_V1 — results

**Classification:** retrospective reanalysis of published source traces. This is not a new animal experiment, independent causal validation, or AI-transfer result.

## Result

In five WT and five RIM-ablated constant-temperature animal traces, AIY alone predicted forward versus reversal state above chance in WT on held-out contiguous time blocks (mean AUC `0.758`) and near chance after RIM ablation (mean `0.502`). AVA alone showed means of `0.736` and `0.631`, respectively.

The prior motor-state signal was highly persistent: adding it to the decoder made AUC approximately `0.979–0.986` in WT and `0.9995–0.9999` after RIM ablation. After controlling for the immediately preceding behavioral state, adding AIY calcium improved mean AUC by `0.01554` in WT and `0.000028` after RIM ablation. The animal-level WT-minus-RIM contrast was `0.01551` (animal bootstrap 95% interval `[0.01143, 0.01913]`; exact 5/5-label permutation reference `p=0.00794`, descriptive only).

AVA showed a similar, somewhat smaller incremental pattern: `0.00948` in WT and `0.000052` after RIM ablation; group contrast `0.00943` (bootstrap interval `[0.00338, 0.01535]`; exact permutation reference `p=0.04762`, descriptive only). With only five animals per group, these intervals and permutation values are not confirmatory. The AVA result also means the group difference is not uniquely localized to AIY by this analysis.

## Interpretation

The traces are consistent with AIY carrying a motor-state-related signal in WT that is markedly reduced after RIM ablation. However, the neural increment beyond the immediately previous motor state is small, and the internal AVA comparator changes in the same direction. This is a bounded source-data consistency check; it does not identify a novel operation beyond the published paper, establish AIY-specific information routing, or provide new causal evidence. The strongest causal interpretation remains the source paper's intervention evidence.

The primary computational lesson for the project is a boundary: decoding motor state from neural activity is easy to overstate when behavioral persistence is ignored. Future AI comparisons should distinguish neural feedback from simply carrying forward the prior action/state, and should retain a second neural/circuit placement control.

## Provenance and verification

- Frozen analysis contract: [`CONTRACT.md`](CONTRACT.md)
- Runner, plotter, independent verifier: [`model/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/`](../../model/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/)
- Per-animal predictions and source manifest: [`data/results/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/`](../../data/results/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/)
- Figure: [`M2_AIY_STATE_CONDITIONAL_ENCODING_V1.png`](../../data/results/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/M2_AIY_STATE_CONDITIONAL_ENCODING_V1.png)
- Independent verifier: `PASS`; it re-parsed the source workbooks, independently recomputed all 10 animal-level model scores, checked all 252 group allocations, and verified input/contract/runner/output hashes.
- Source hashes are pinned in `source_manifest.json`; summary output hashes are in `run_manifest.json`.

## Disposition

`SOURCE_DATA_CONSISTENT_WITH_RIM_DEPENDENT_AIY_STATE_CODE; AIY_SPECIFIC_INCREMENT_UNRESOLVED`. This analysis sharpens the interpretation boundary but does not establish a project-level biological-to-AI claim.
