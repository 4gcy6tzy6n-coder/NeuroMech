# M5 CF-LTD to anticipatory-lick decoding V1 — results

**Status:** completed; independent verifier passed and a separate full rerun reproduced the scientific output tables byte-for-byte. **Classification:** retrospective exploratory within-session source-data analysis. This is not an animal-level or causal result.

## Question and analysis

Using the Dryad v4 1-s-to-2-s GrC/CF release, this analysis asked whether a training-fold CF-timed LTD projection of held-out GrC activity improves prediction of anticipatory lick onsets over elapsed time and recent lick history. It analyzed 16 sessions and 1,393 author-QC trials. Same-trial identity was established directly: `midAlgn.lick` and `midAlgn.sigFilt_GrC` share their trial axis in the actual MATLAB files. The analysis produced 61,839 held-out trial-time samples and 494,712 predictions across eight model arms.

Each model predicted a new lick onset 50–200 ms later. Evaluation time points were censored so the target window ended at least 50 ms before the trial's recorded reward delay. Recent lick counts and elapsed time formed the baseline. Entire trials, not frames, were held out in five folds. CF candidate selection and LTD projection fitting used only rewarded training-fold trials; held-out CF traces were never used. Sessions are descriptive units because the release does not provide a verified animal identifier.

The source paper already reports session-level association between modeled LTD timing accuracy and lick-timing behavior (Figure 6H); this analysis is an exploratory single-trial, within-session extension, not an independent discovery. The source-rule weights remain modeled estimates, not measured GrC-to-Purkinje synaptic strengths. [Primary article](https://doi.org/10.1016/j.neuron.2024.05.019) · [Open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC11343686/) · [Dryad v4](https://doi.org/10.5061/dryad.bk3j9kdm6).

## Primary metric

Values below are mean session-level trial-averaged Brier scores. Positive gain means lower Brier score than the time-plus-lick-history baseline. Sessions are not pooled as independent animals; no inferential p-values or confidence intervals are reported.

| Model | Mean session Brier | Gain vs baseline | Sessions with positive gain |
|---|---:|---:|---:|
| Time + recent lick history | 0.114906 | 0 | 0/16 |
| Source CF-LTD projection | 0.115610 | −0.000704 | 6/16 |
| CF event-time only, no trace | 0.115799 | −0.000893 | 6/16 |
| CF event trains yoked across training trials | 0.114615 | +0.000291 | 7/16 |
| Within-cell GrC time-shuffled rule | 0.114692 | +0.000214 | 8/16 |
| Cell-shuffled CF-LTD weights | 0.115122 | −0.000216 | 7/16 |
| Raw GrC PC1 | 0.115490 | −0.000584 | 12/16 |
| Raw GrC PC16 | 0.115827 | −0.000921 | 11/16 |

The CF-LTD projection did not improve the primary baseline on average and improved it in only 6 of 16 sessions. It also failed the mechanism-specific comparison: the event-yoked projection had a lower mean Brier score, and the CF-LTD projection beat it in only 5 of 16 sessions. This does not support incremental, source-rule-specific single-trial lick information in this cohort under the tested readout.

The result was heterogeneous across delay groups. In 1-s experts, CF-LTD worsened mean Brier by 0.002837; in 2-s novices transitioning from 1 s, it worsened Brier by 0.000582; in 2-s experts, it improved Brier by 0.000971 in 3 of 6 sessions. In that last group, the event-yoked control's gain was essentially the same (+0.000987), while raw GrC PC16 had a larger descriptive gain (+0.003796). These group summaries are descriptive and should not be interpreted as group-level effects.

Sample-level average precision did not reverse the primary conclusion: CF-LTD averaged 0.8375 versus 0.8396 for the baseline and 0.8413 for the event-yoked control. Raw PC16 had higher average precision (0.8471), but it used more features and was not parameter-matched; Brier score remains primary.

## Interpretation and limits

- The result is negative for the tested CF-LTD projection/readout: it did not add robust or source-rule-specific held-out information beyond time and recent lick behavior.
- The 2-s expert subgroup shows a small descriptive gain, but its event-yoked control matched it and the generic PC16 comparison did better. This cannot support CF-LTD specificity.
- The study is within-session prediction, not cross-animal generalization. Public animal/session linkage is unavailable, the transition group includes sessions with only 7 eligible trials, and some sessions may come from the same mouse.
- `sigFilt_GrC` is offline processed data; the temporal causality of all preprocessing is not established. The analysis is not a prospective online forecast or a closed-loop AI demonstration.
- The data do not directly measure CF-induced synaptic weights. A negative result here does not falsify the biological mechanism or the paper's results.

## Reproducibility and artifacts

- [Frozen analysis contract](CONTRACT.md)
- [Failure record](FAILURE_LOG.md)
- [Runner and independent verifier](../../model/M5_CF_LTD_LICK_DECODING_V1/)
- [Canonical trial-time predictions, trial scores, session/group summaries, and hashes](../../data/results/M5_CF_LTD_LICK_DECODING_V1/canonical/)
- [Run verification record](../../data/results/M5_CF_LTD_LICK_DECODING_V1/RUN_VERIFICATION.json)

The independent verifier reconstructed trial inclusion, lick-sensor QC, held-out fold assignments, trial-time labels, and Brier/log-loss summaries from the source MAT file. It passed for 16 sessions, 1,393 eligible trials, 61,839 unique trial-time samples, 494,712 arm predictions, and 640 fold-fit records. The separate full rerun matched all seven scientific output tables byte-for-byte.
