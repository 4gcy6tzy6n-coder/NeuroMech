# M5 CF-LTD to anticipatory-lick decoding V1

**Classification:** retrospective, exploratory, within-session source-data analysis. The paper, its source analyses, and earlier M5 results are known. This is not an independent biological replication, a causal test, or an AI-transfer result.

## Question

Does a source-rule CF-timed LTD projection of GrC activity add held-out, within-session information about near-future anticipatory lick onsets beyond elapsed time and the animal's recent lick history? Does it add more than no-trace, CF-event-yoked, time-shuffled, cell-shuffled, or generic GrC projections?

This asks about predictive association in the processed public recording. It does not claim the projection causes licking or is an experimentally measured synaptic weight.

## Frozen inputs and trial definition

Use only Dryad v4 `learning_1s_to_2s_GrC_CF.mat` and the pinned acquisition manifest. Use the actual `midAlgn.sigFilt_GrC`, `rewAlgn.sp_CF`, `midAlgn.lick`, `rewAlgn.lick`, `tmpxCb`, `tmpxx`, `dtimCb`, `dtb`, `rewarded`, `goodmvdir`, `mvlen`, `rewtimes`, and `midpt` fields. The downloaded records do not contain a `valid_lick_trials` field; reproduce the author MATLAB source's lick-sensor QC directly from `rewAlgn.lick`: apply the 300-sample causal moving average to the binary trace and retain trials whose maximum in `[-1.75, +1.75] s` from reward is `<0.99`.

Use the author source group labels and eligibility rule: group 1 has a 1-s expected delay and requires `rewdel > 0.75 s`; groups 2–3 have a 2-s expected delay and require `rewdel > 1.75 s`, where `rewdel = (rewtimes - midpt) * dtb`. Retain rewarded trials with `goodmvdir`; retain omission trials with `goodmvdir` and `mvlen > 6 mm`, matching `learning_1s_to_2s_GrC_CF.m`. Apply the lick-QC mask to both. If trial-level laser data are present, also exclude trials with laser activity in the author lick-analysis window `[-2, +2] s` around reward. The target is built from movement-aligned lick contacts; it does not use reward-aligned test signals.

Each session is analyzed separately. There is no verified animal identifier in the release, so sessions are descriptive reporting units; no animal-level inference or pooled animal claim is permitted.

## Prediction target and timing

At each imaging-time sample `t` in the anticipatory interval, predict whether at least one new lick onset occurs in `(t + 0.05 s, t + 0.20 s]`. Derive onsets as positive transitions in the author-provided binary lick sensor trace, matching the event definition in the authors' MATLAB analysis. Use movement-midpoint-aligned traces. Candidate sample times are `0` through `0.75 s` for the 1-s group and `0` through `1.75 s` for the 2-s groups. For each trial, retain a candidate time only when the target window ends at least 0.05 s before that trial's `rewdel`; `rewdel` is used only to censor evaluation samples and is never a predictor. This prevents post-reward lick events from entering the anticipatory target when trial delay varies. The outcome horizon is identical across groups.

The baseline has an intercept, eight fixed radial time-basis features over the group's anticipatory interval, and lick-onset counts from the preceding `0.25 s` and `1.0 s`. No held-out future lick, reward-time value, or behavioral trace outside the observed past is an input. The task is conditional temporal decoding, not autonomous behavior generation. The released `sigFilt_GrC` preprocessing is offline and its temporal causality is not established, so results must not be described as prospective closed-loop forecasts.

## Cross-validation and models

Within each session, assign eligible trials once to five deterministic folds (`seed=20261001`), stratified only by reward/omission status when each class has at least five trials; otherwise use a seeded shuffled five-fold partition without stratification. Every fold holds out entire trials; all frames from a held-out trial stay together. No frame or event is treated as an independent biological replicate.

Fit an L2 logistic regression (`C=1`, `lbfgs`, fixed solver settings, no hyperparameter search) on training-fold trial-time samples. Standardize learned neural features using training-fold samples only. Source-rule weights, CF selection, generic PCA, and readout fits use training-fold data only. Fit source CF-LTD weights on training-fold rewarded trials using the pinned V1 source-rule implementation; do not use test CF traces. If no training CF passes the source reward-response criterion, retain the fold with a zero projection and mark it `NO_CF_CANDIDATE_ZERO_SIGNAL`.

Compare:

- `TIME_LICK_HISTORY`: elapsed-time and observed past-lick baseline.
- `CF_LTD`: baseline plus one source-rule CF-LTD weighted GrC projection.
- `CF_NO_TRACE`: baseline plus a projection using only CF-event-time eligibility.
- `CF_EVENT_YOKED`: baseline plus source-rule weights fitted after permuting complete training CF event trains across rewarded training trials.
- `CF_TIME_SHUFFLED`: baseline plus source-rule weights fitted after within-cell training-trial temporal shuffling.
- `CF_CELL_SHUFFLED`: baseline plus a random permutation of fitted CF-LTD weights across GrC identities.
- `RAW_GRC_PC1`: baseline plus one train-only principal component of raw GrC activity.
- `RAW_GRC_PC16`: baseline plus up to 16 train-only principal components as a higher-capacity generic reference.

All models share identical held-out trials and trial-time targets. Model feature counts and folds are reported. PC16 is explicitly not a parameter-matched comparison.

## Outcomes and reporting

Primary metric: held-out Brier score for next-window lick occurrence. The primary descriptive contrast is `Brier(TIME_LICK_HISTORY) - Brier(CF_LTD)`; positive values favor incremental CF-LTD information. Compute each trial's mean Brier score across eligible time points, then average trials within each session. Also report per-session contrasts against every control, session direction counts, and group-level descriptive summaries. No p-values or confidence intervals across sessions are used because animal linkage is unavailable and sessions may not be independent.

Report held-out log loss and average precision as secondary metrics. Do not select a model, endpoint, window, or subset from these secondary outcomes.

## Interpretation limits

A positive CF-LTD contrast would support incremental held-out temporal association in this released cohort, conditional on the model's recent-lick history and fixed time basis. It would not establish causal CF teaching, direct synaptic weights, trial-general causal forecasting, animal-level generalization, or AI benefit. If generic PCA beats CF-LTD, the result does not support specificity of the source rule. A null or negative result bounds this implementation and dataset; it does not falsify cerebellar plasticity in vivo.

The result is exploratory because this is a post-publication reanalysis and the underlying paper already reports session-level links between modeled LTD readout accuracy and lick-timing behavior. Any new claim must be framed as a single-trial, within-session extension, not an independent discovery.

## Reproducibility

Before the run, record the raw-data, acquisition-manifest, contract, source-rule, and runner SHA-256 values, software versions, exact session/trial/fold inventory, and output path in `data/results/M5_CF_LTD_LICK_DECODING_V1/PREFLIGHT.json`. Write canonical outputs under `canonical/`. The verifier checks complete trial-fold coverage, no train/test trial overlap, model/artifact hashes, metric recomputation from per-trial predictions, and all output checksums. A separate full rerun must reproduce the prediction rows byte-for-byte before publication to GitHub.

## Sources

- Garcia-Garcia et al., *Neuron* (2024), DOI [10.1016/j.neuron.2024.05.019](https://doi.org/10.1016/j.neuron.2024.05.019); open text: [PMC11343686](https://pmc.ncbi.nlm.nih.gov/articles/PMC11343686/).
- Dryad dataset v4, DOI [10.5061/dryad.bk3j9kdm6](https://doi.org/10.5061/dryad.bk3j9kdm6).
- Author analysis code at commit `124c83e1af83e9680e05f9827448579d02345fa3`: [learning_1s_to_2s_GrC_CF.m](https://github.com/wagnerlabnih/garcia-garcia-neuron-2024/blob/124c83e1af83e9680e05f9827448579d02345fa3/learning_1s_to_2s_GrC_CF.m) and [learning_1s_to_2s_licking.m](https://github.com/wagnerlabnih/garcia-garcia-neuron-2024/blob/124c83e1af83e9680e05f9827448579d02345fa3/learning_1s_to_2s_licking.m).
