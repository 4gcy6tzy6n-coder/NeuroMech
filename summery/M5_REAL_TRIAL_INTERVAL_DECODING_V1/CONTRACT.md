# M5 real-trial reward-interval prediction V1

**Classification:** retrospective, post-result source-data reanalysis. The Garcia-Garcia et al. source data and prior M5 analyses are known. This does not constitute an independent biological replication or an AI-transfer result.

## Question

Do source-defined climbing-fiber (CF)-timed granule-cell (GrC) LTD weights contain held-out, single-trial information about the actual reward delay beyond a training-fold session-mean timer, when the model only receives GrC activity recorded before reward onset? Does this compact population projection outperform event-yoked/no-trace controls and a strong generic decoder of the same neural traces?

## Source data and target

Use only the acquired Dryad v4 `learning_1s_to_2s_GrC_CF.mat` file and its pinned acquisition manifest. Analyze the three source groups: 1-s expert, 2-s novice/1-s expert, and 2-s expert. Within each session, include author-QC trials `rewarded & goodmvdir & (mvlen > 7)`. Target is the measured trial delay `(rewtimes − midpt) × dtb` in seconds. Sessions are the reporting units; the public file does not provide a verified animal key, so do not treat sessions as independent animals or report animal-level inference.

The input window is fixed at movement-midpoint through `0.80 s`, independent of each trial's reward time. The inspected eligible source trials have minimum reward delays above `1.0 s`, so this window ends before the earliest reward event. No reward-aligned test traces, post-reward frames, true test delay, or test labels may be used to construct model inputs. All training and test trials remain within the same source session; the claim is within-session out-of-fold prediction only.

## Cross-validation and models

Within each session, make one deterministic five-fold partition of eligible trials. Every eligible trial is held out exactly once; all model fitting, source weight estimation, PCA scaling, and ridge readout fitting for a fold use only the other four folds. The independent biological unit is unresolved beyond session, so fold repetition is not used as a population sample.

For CF-LTD models, estimate CF candidates from training-fold `rewAlgn/sp_CF` reward-response increase (`0–0.25 s`) over baseline (`−0.3` to `−0.025 s`), following the source analysis. Fit per-cell scales using training-fold GrC activity only. The source LTD arm applies its inclusive `−0.15` to `−0.025 s` pre-CF eligibility window, source logistic transform, per-CF centering/normalization, averaging over selected CFs, and negative LTD sign. The `NO_TRACE` arm uses only the CF event frame. `CF_EVENT_YOKED` permutes complete training CF event trains across training GrC trials within fold, retaining the event distribution while breaking trial pairing. `GRc_TIME_SHUFFLED` independently permutes each training cell's time samples before source-weight fitting. `CELL_SHUFFLED` permutes fitted source weights across GrC identities.

For each source projection, form its one-dimensional GrC population signal from only the fixed pre-reward `midAlgn` window. Fit a fixed-ridge linear decoder (`alpha=10`) on its time samples to predict reward delay, using training folds only. The strong generic comparator flattens the same raw pre-reward GrC traces, standardizes features from training data, projects onto at most 16 training-only principal components, then uses ridge regression (`alpha=10`). The `TRAINING_MEAN` arm predicts each trial using the training-fold mean reward delay. No hyperparameter search or model selection on held-out folds is allowed.

## Outcomes and reporting

Primary outcome: held-out trial absolute reward-delay error in seconds, pooled by concatenating each session's five out-of-fold predictions. Report one MAE per session and per source group for all arms. The primary descriptive contrasts are source CF-LTD against the training-mean timer, CF-event-yoked control, no-trace update, and raw-GrC PCA/ridge. Report the per-session paired differences, their direction counts, target SD, and the fraction of baseline MAE removed. Do not calculate p-values or confidence intervals across sessions as if sessions were animals; group summaries are descriptive because animal identity linkage is unavailable.

## Interpretation boundary

A lower held-out error than the session-mean timer would show within-session predictive information in this released source cohort, not causal teaching, animal-level generalization, measured synaptic weights, or AI benefit. If all neural decoders tie the session mean, the source data do not identify useful single-trial interval variation under this window. If raw-PCA decoding wins while CF-LTD does not, the result supports neural timing information but not specificity of the source rule. If the CF-LTD model wins, the result remains exploratory and session-bounded. All outcomes and failures are retained.

## Reproducibility

Before the analysis run, pin the raw Dryad SHA-256, this contract hash, runner hash, exact source session/trial/fold inventory, Python/NumPy/h5py versions, and output path in `data/results/M5_REAL_TRIAL_INTERVAL_DECODING_V1/PREFLIGHT.json`. Write canonical outputs beneath `canonical/`. The verifier recomputes all session and group metrics from trial-level predictions, checks fold exclusivity and hashes, and records its scope. A separate full rerun must reproduce canonical prediction rows before the round is published.
