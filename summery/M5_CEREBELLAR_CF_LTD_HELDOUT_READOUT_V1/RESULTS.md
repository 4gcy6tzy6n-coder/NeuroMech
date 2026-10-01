# M5 CF-taught GrC readout on held-out trials — results

## Result

The author-code CF-timed LTD weights carried held-out time-progress information within source recording sessions. Across the three Dryad groups, their session-averaged held-out trial `r²` exceeded both the uniform and CF-time-shuffled controls. The fixed ridge reference was stronger on average, so the result shows predictive information in this source-derived weight ordering, not a uniquely effective or optimal computation.

| Source group | Sessions | CF-timed LTD | Uniform | CF-time shuffled | Cell shuffled | Ridge reference |
|---|---:|---:|---:|---:|---:|---:|
| 1-s expert | 5 | 0.491 | 0.273 | 0.195 | 0.128 | 0.528 |
| 2-s novice / 1-s expert | 5 | 0.435 | 0.266 | 0.163 | 0.125 | 0.513 |
| 2-s expert | 6 | 0.491 | 0.166 | 0.151 | 0.122 | 0.640 |

Values are the equal-weighted mean of session-level means across the listed group. Each session mean averages its valid split means; a split mean averages held-out trial-level squared Pearson correlations. These are descriptive summaries, not inferential estimates.

Across all 16 sessions with at least one valid split, CF-timed LTD exceeded:

- uniform weights in **15/16** sessions (mean paired session difference `+0.242`);
- CF-time-shuffled weights in **16/16** sessions (mean difference `+0.305`);
- cell-shuffled weights in **16/16** sessions (mean difference `+0.348`).

The ridge reference exceeded CF-timed LTD in **14/16** sessions (mean `CF-LTD − ridge` difference `−0.092`). The mean CF-LTD `r²` was lower than the ridge reference in every source group. Ridge is a descriptive readout reference, not a capacity-matched alternative mechanism.

The output contains 12,355 held-out trial-method rows, 392 split-method/status rows, and 5,161 split-specific cell-weight rows. There are 78 usable train/test splits out of 80 planned: two splits in one 1-s expert session had no training CF meeting the source response criterion. Those splits are retained as `NO_TRAINING_CF_CANDIDATES`; no substitute CF or proxy was introduced.

## Interpretation and boundary

This post-result exploratory analysis supports a narrow statement: **within these recordings, a CF-response-selected LTD weight vector fit on one subset of rewarded trials predicted the temporal ordering of GrC activity on held-out trials from the same session better than uniform and timing-destroyed LTD controls.** It does not show that the modeled weights are measured synaptic strengths, that CF spikes causally induce those changes in vivo, that the relation generalizes to new animals or sessions, or that the rule improves an artificial system.

The study is not independent of the original paper or the project's prior M5 results. The trial split supports within-session held-out prediction only; animal identity and linkage across sessions are not established, and session-level summaries are not treated as animal replicates. Squared correlation is direction-insensitive and measures temporal association, not calibrated time estimates. The all-to-all GrC-to-Purkinje assumption is inherited from the source model. Actual source-derived weights also do not beat the ridge reference consistently, and the CF-time-shuffled control retains nonzero temporal information.

This is useful input to the next AI experiment because it tests the author-defined local rule itself, rather than only replaying GrC profiles through a generic eligibility trace. The next transfer test should implement reward-timed CF teaching and source-window LTD directly, then compare it with the same architecture without a trace, a time-mismatched teaching event, and strong trained/replay controls. The previous M5 transfer result remains negative and is not overwritten by this biological-data reanalysis.

## Implementation incident and reproducibility

The first execution emitted divide/overflow warnings from this host's macOS Accelerate `matmul` path even though inputs were finite and the resulting output files were finite. That attempt is preserved under `data/results/M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1_attempt_01_accelerate_warnings/` and is noncanonical. The runner was changed to use explicit NumPy contractions for the small linear-algebra products. With `RuntimeWarning` promoted to errors, the full rerun completed. Its session summaries match the preserved attempt within `3.4e-16`; the numerical change did not alter the conclusion.

The final run is recorded in [`run_manifest.json`](../../data/results/M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1/run_manifest.json). The manifest pins the author code commit, runner and contract hashes, Dryad acquisition-manifest hash, raw-file SHA-256, and output hashes. The raw MAT file matches the published Dryad checksum and is not copied into Git.

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and independent artifact verifier: [`run_experiment.py`](../../model/M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1/run_experiment.py), [`verify_results.py`](../../model/M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1/verify_results.py)
- Trial-level outputs and session summaries: [`data/results/M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1/`](../../data/results/M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1/)
