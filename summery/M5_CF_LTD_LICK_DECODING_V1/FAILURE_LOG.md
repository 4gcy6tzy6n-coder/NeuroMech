# Failure and implementation record

## Attempt 1 — conservative minimum-trial guard

- **Observed:** the first full run stopped at the first session, which had 11 eligible trials, because the runner required `FOLDS * 3` trials.
- **Outputs:** no held-out predictions, metrics, or scientific outcome summaries were produced. The run had written only the outcome-blind preflight inventory; it is retained as `data/results/M5_CF_LTD_LICK_DECODING_V1/preflight_attempt_1.json`.
- **Diagnosis:** the guard was stricter than the five-fold algorithm requires. Each session only needs at least five trials to assign one or more whole trials to each test fold. The small-session limitation is already reported; the session should not be discarded.
- **Correction:** lower the technical guard to `n_trials >= FOLDS`, retain seeded KFold when reward/omission strata are too small, and keep every session in descriptive reporting.
- **Outcome exposure:** none. No predicted values or outcome metrics existed at the time of the correction.

## Attempt 2 — heterogeneous fit-manifest columns

- **Observed:** all session folds completed, then CSV serialization stopped because CF projection arms contain source-fit metadata columns absent from generic/baseline arms.
- **Outputs:** prediction and per-trial score files had been written to the incomplete canonical directory before the error. They are preserved under `data/results/M5_CF_LTD_LICK_DECODING_V1/failed_attempt_2_partial/` and are not used as canonical results. The preflight is retained as `preflight_attempt_2.json`.
- **Diagnosis:** the CSV writer derived columns from the first row, although the fold manifest intentionally records different metadata for projection and non-projection fits.
- **Correction:** construct a stable ordered union of keys across all rows, leaving fields not applicable to an arm empty.
- **Outcome exposure:** no prediction or metric values were inspected. The correction is limited to output serialization.
