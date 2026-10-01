# Implementation and execution record

## Pre-analysis runner failure

The first invocation of `run_experiment.py` stopped before loading or analyzing trial outcomes. `source_weights()` used `rng.permutation(...)` in the `time_shuffled` control without initializing `rng`, raising `NameError` during setup. No canonical outcome files were produced. The empty output directory from that attempt was moved aside to `/tmp/M5_REAL_TRIAL_INTERVAL_DECODING_V1_failed_attempt` and is not part of the result set.

The runner now initializes a deterministic per-fit random generator and uses it for both event-yoking and time shuffling. The corrected runner hash is recorded in the amended `PREFLIGHT.json` before any valid analysis run. This correction changes implementation only; no outcome was inspected to motivate it. The experiment remains retrospective/exploratory as specified in the frozen contract.
