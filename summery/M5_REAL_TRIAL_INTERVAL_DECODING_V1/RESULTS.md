# M5 real-trial reward-interval prediction V1 — results

**Status:** completed; independent deterministic rerun reproduced canonical predictions and fit records byte-for-byte. **Classification:** retrospective exploratory source-data analysis. The training-fold empty-CF handling was amended after a partial run; this is not confirmatory evidence.

## Question and design

Within each of 16 source sessions, a deterministic five-fold split held out each eligible trial once. Seven decoders predicted measured reward delay from GrC activity in a fixed 0–0.80 s post-midpoint window, before the earliest eligible reward onset. The comparison included the training-fold mean, source-style CF-timed LTD, an instantaneous CF update, CF-event yoking, time and cell shuffles, and train-only PCA16/ridge on raw GrC traces. The source release is associated with Garcia-Garcia et al., “A cerebellar granule cell–climbing fiber computation to learn to track long time intervals” ([Neuron 2024](https://doi.org/10.1016/j.neuron.2024.05.019); [Dryad v4](https://doi.org/10.5061/dryad.bk3j9kdm6)). The raw source cohort contributed 1,004 eligible trials and 7,028 held-out trial-by-arm predictions. Sessions are descriptive units; public animal/session linkage does not support animal-level inference.

## Primary outcome

Values are mean session-level held-out MAE in seconds. Δ is decoder MAE minus the training-mean MAE; positive values mean the decoder is worse. Group summaries are descriptive, with no inferential p-values or animal-level confidence intervals.

| Source group | Sessions | Training mean | CF-LTD | CF-LTD Δ | Raw GrC PCA16 | PCA Δ | CF-LTD better than mean | PCA better than mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1-s expert | 5 | 0.05198 | 0.06052 | +0.00854 | 0.04745 | -0.00453 | 0/5 | 4/5 |
| 2-s novice / 1-s expert | 5 | 0.04268 | 0.05444 | +0.01176 | 0.04272 | +0.00003 | 1/5 | 3/5 |
| 2-s expert | 6 | 0.05365 | 0.06258 | +0.00893 | 0.05033 | -0.00332 | 0/6 | 4/6 |

Across sessions (each session weighted equally), CF-LTD MAE exceeded the training-mean baseline by **0.00970 s** and improved on it in **1/16 sessions**. The raw-GrC PCA16 decoder was **0.00265 s** better on average and improved on the baseline in **11/16 sessions**; this small descriptive advantage was absent in the transition group (mean Δ +0.00003 s). In every source group, raw PCA16 had lower mean MAE than CF-LTD by 0.0117–0.0131 s. The CF-LTD projection therefore did not extract useful held-out interval information beyond the session-level timer under this setup, while a generic readout of the same neural traces showed at most modest, group-dependent signal.

The activity specificity controls do not rescue a CF-timed LTD interpretation: CF-LTD did not consistently outperform its no-trace or event-yoked variants. It did outperform cell-shuffled weights in most sessions, but both biologically structured and shuffled projections remained worse than the training mean. The main result is consequently a negative result for this source-defined projection/readout implementation, not evidence that the biological plasticity rule is ineffective in vivo.

## Runtime amendment and fit availability

A partial execution reached training folds where no CF cell passed the frozen reward-response-over-baseline criterion. The runner had accumulated predictions for earlier sessions in memory but stopped before writing canonical files; no prediction values were inspected. To keep the assigned folds and sessions rather than selecting on observed activity, the protocol was amended to map a zero-candidate fold to a zero projection (training-mean prediction) and retain it with an explicit status. In the complete run, this occurred in four of five folds for 1-s expert session 3, across the five CF-derived arms (20 fit records total). This amended analysis is post-execution and exploratory.

## Interpretation and limits

- The test evaluates within-session prediction over one fixed pre-reward window. It does not test causal CF teaching, directly measured synaptic weights, transfer between animals, behavior-level benefit, or AI performance.
- Public data do not provide a verified animal identity key; 16 sessions are not treated as 16 independent animals.
- The baseline is strong because the sessions have relatively stable reward intervals; interval heterogeneity and trial selection constrain what this decoder can identify. A null/negative projection result does not show that the biological mechanism lacks value for learning or adaptation across changing intervals.
- Raw GrC PCA16 is a generic decoder and was fit within session; its small descriptive advantage over the session mean in two groups is not an independently replicated or between-animal result.
- The result follows two implementation failures and a protocol amendment after partial execution. All failures remain in the provenance; the report is not a confirmatory preregistration.

## Reproducibility

- [Frozen contract and amendment](CONTRACT.md)
- [Implementation/runtime failure record](FAILURE_LOG.md)
- [Runner and verifier](../../model/M5_REAL_TRIAL_INTERVAL_DECODING_V1/)
- [Canonical trial predictions, fold fits, session/group summaries, and hashes](../../data/results/M5_REAL_TRIAL_INTERVAL_DECODING_V1/canonical/)
- [Preflight and amendment record](../../data/results/M5_REAL_TRIAL_INTERVAL_DECODING_V1/PREFLIGHT.json)

The independent verifier passed for 7,028 predictions, 1,004 unique held-out trials, 16 sessions, 112 session-by-arm summaries, 21 group-by-arm summaries, 480 fit records, and all six hashed output files. A fresh full run reproduced `heldout_predictions.csv` and `fold_fit_manifest.csv` byte-for-byte. The verifier checks data/summary consistency and hashes; it does not independently reimplement the source-rule fitting algorithm.

The separate Feishu experiment chapter was appended and read back successfully at document revision 87.
