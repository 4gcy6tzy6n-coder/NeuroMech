# M5 cerebellar interval timing transfer V1 — exploratory contract

**Status:** retrospective, post-result exploratory artificial experiment. Prior M5 artificial outcomes and the biological source-data result are known. This is not confirmatory, biological validation, or evidence of general AI benefit.

## Question

Can a fixed temporal representation extracted from the published 1-s and 2-s expert granule-cell (GrC) activity profiles support reward-time prediction in an independent synthetic interval task, and does a local eligibility update help relative to a local no-trace update and matched generic temporal bases?

## Biological input and boundary

Use the source-filtered per-cell mean GrC activity from Dryad v4 (`learning_1s_to_2s_GrC_CF.mat`), groups 1 (`1-s expert`) and 3 (`2-s expert`). For each cell, subtract its mean activity in `[-1, 0]` s relative to movement midpoint, retain positive activity in `[0, 2]` s, normalize by its positive maximum, and interpolate to a common 81-bin grid. Select 32 cells from each source group by deterministic evenly spaced indices. These are cell-level traces averaged over source-filtered trials, not independent animals and not direct synaptic measurements. The source groups and their interval labels informed feature construction; therefore all downstream tests are exploratory.

## Synthetic task

Each episode presents one of two abstract cues and a reward event at a cue-specific interval. Training and test rewards are generated independently of the biological data. The main mapping assigns cue 0 to a short interval and cue 1 to a long interval; a reversed mapping is also evaluated. Reward times include independent uniform jitter. Models emit a time-resolved reward-event score. The primary outcome is absolute error (seconds) between the true reward time and the model's maximum-score time bin.

## Frozen comparison arms

1. `BIO_PROFILE_ELIGIBILITY`: the 64 measured cell profiles as temporal basis; eligibility-decay local readout update.
2. `BIO_PROFILE_NO_TRACE`: same basis and update budget, with current-step-only local update.
3. `GENERIC_RBF_ELIGIBILITY`: 64 evenly spaced generic radial temporal basis functions, with the same eligibility update.
4. `SHUFFLED_PROFILE_ELIGIBILITY`: the biological basis with each cell's time bins independently permuted, preserving each trace's marginal values while breaking its temporal order; same update.
5. `GRU_PROFILE_BPTT`: 16-unit GRU trained with supervised sequence backpropagation on the same biological-profile episodes.
6. `GRU_CLOCK_BPTT`: same 16-unit GRU trained only on a constant clock input and cue; this tests whether recurrent step counting explains performance without biological temporal features.
7. `EMPIRICAL_TIMER`: cue-specific mean reward time estimated from training episodes; a strong explicit-timing reference.

## Analysis

Task seed is the resampling unit. Report per-seed mean absolute timing error and paired-seed contrasts. Use a paired bootstrap over task seeds for 95% intervals. Also report classification-level direction errors, but treat these as secondary. No cells or time bins are inferential units. Do not interpret a positive result as biological causality, synaptic-rule validation, or broad AI benefit.

## Falsification and limits

The proposed transfer is not supported if the biological-profile arm does not improve over its local no-trace ablation, or if it fails to match the generic basis and recurrent controls under the primary aligned mapping. A benefit only over shuffled features is insufficient because temporal order is destroyed in that control. If the constant-input GRU matches the profile-input GRU, the activity profiles add no demonstrated value beyond a learned clock. A strong empirical timer result bounds attainable performance and is not a learned model. Reversed-mapping performance tests sensitivity to task mapping; it is not a prediction of the source biology.

## Reproducibility

The runner refuses to overwrite existing outputs. The raw MAT input remains outside Git; its SHA-256 is recorded in the acquisition manifest. Outputs, environment, source checksum, runner checksum, and deterministic seed range are recorded in the run manifest.
