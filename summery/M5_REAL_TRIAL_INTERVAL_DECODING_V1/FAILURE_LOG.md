# Implementation and execution record

## Pre-analysis runner failure

The first invocation of `run_experiment.py` stopped before loading or analyzing trial outcomes. `source_weights()` used `rng.permutation(...)` in the `time_shuffled` control without initializing `rng`, raising `NameError` during setup. No canonical outcome files were produced. The empty output directory from that attempt was moved aside to `/tmp/M5_REAL_TRIAL_INTERVAL_DECODING_V1_failed_attempt` and is not part of the result set.

The runner now initializes a deterministic per-fit random generator and uses it for both event-yoking and time shuffling. The corrected runner hash is recorded in the amended `PREFLIGHT.json` before any valid analysis run. This correction changes implementation only; no outcome was inspected to motivate it. The experiment remains retrospective/exploratory as specified in the frozen contract.

## Partial analysis stopped on empty CF candidate set

The second invocation processed eligible trials and reached model fitting, then stopped because one training fold had no CF cell above the frozen response criterion. Predictions for earlier sessions existed only in process memory; the runner exited before writing canonical files, and no prediction values or outcome summaries were inspected. The empty output directory was retained without result files.

The protocol now assigns a zero projection to a fold with no selected CF candidate, equivalent to an intercept-only/training-mean decoder, and explicitly labels that fit in the fold manifest. This avoids dropping sessions or folds based on observed activity. Because the protocol amendment follows partial execution, all resulting estimates are exploratory and not confirmatory. A separate CSV writer issue was also corrected: the fit manifest has heterogeneous metadata across model arms, so the writer now emits the union of columns rather than failing on arm-specific fields.
