# M2 2D closed-loop pursuit V2 — training-distribution diagnostic

**Experiment ID:** `M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC`
**Classification:** post-result exploratory diagnostic. V1 outcomes were inspected before this contract was written. This is not an independent confirmation and does not establish biological validation.

## Question

Does training on trajectories with a deployment-like state/action distribution improve the MODE_GAIN controller's closed-loop performance relative to its parameter-matched bilinear estimator, compared with training on random-action trajectories?

## Rationale and scope

V1 used random movement axes in supervised training, whereas each deployed controller selected its next movement axis from its own estimated target residual. V1 found that MODE_GAIN's lower teacher-forced estimation loss did not translate into better navigation. A train/deployment distribution gap is one plausible explanation; V1 did not isolate it. This diagnostic changes the training trajectory policy while holding the task, learned model equations, sample count, optimizer budget, and evaluation environment fixed.

The result is conditional on the particular shared trajectory-generating policies below. It cannot establish that distribution mismatch was the unique cause of V1, or that a biological computation transfers to AI.

## Paired design

Run 30 fresh training seeds (`76000..76029`), with 512 training episodes per seed and 256 held-out test targets per seed. Use the same training target coordinates and standard-normal observation-noise innovations in both training regimes for each seed. Use the same test targets and observation-noise innovations for every regime and model within a seed. Use the same model initialization and minibatch index stream for corresponding models across training regimes.

The two training regimes are:

1. **`RANDOM_ACTION`** — initial sensory motor state is horizontal, as at evaluation; after each observation, choose the next movement axis uniformly and its direction uniformly. This is an exogenous random-action comparator.
2. **`TEACHER_MIXED_CLOSED_LOOP`** — start with the same horizontal sensory state; update an exact task-aware Kalman belief from observations, then choose the Bayes posterior-mean greedy movement on 75% of steps and a uniformly random axis/direction on 25% of steps. This generates target-directed trajectories with deliberate state/action exploration. All learned arms are trained on the same generated trajectories in each regime.

Both regimes contain the same number of target episodes, time steps, observations, supervised labels, optimizer updates (200), batch size (16), and learned model parameters. Training targets use independent `Normal(0, 0.5²)` coordinates; observation noise SD is 0.25; step size is 0.12; maximum episode length is 32 steps. Training inputs and labels follow the V1 definition: observation, current motor state, pre-observation displacement, and true target residual after that displacement.

## Models and evaluation

Train `MODE_GAIN` (8 parameters), `NO_CONTEXT` (6), `ADDITIVE_RNN_MATCHED` (8), and `BILINEAR_RNN_MATCHED` (8) under both regimes. Evaluate each on the V1 2D pursuit task under `ALIGNED` and `REVERSED` sensor mappings, with each policy controlling its own movement and state trajectory. Report the exact Kalman estimator as a task-aware reference; its test values are identical across training-regime labels and are not treated as an independent arm comparison.

The independent replicate is the training seed; held-out target IDs are crossed within seed. Primary metric is final Euclidean target distance under `ALIGNED` mapping.

## Primary estimand

For each regime `r`, define `G_r = mean(final_distance[BILINEAR_RNN_MATCHED] - final_distance[MODE_GAIN])`; positive values favor MODE_GAIN. The single primary diagnostic contrast is the training-regime interaction:

`I = G_TEACHER_MIXED_CLOSED_LOOP - G_RANDOM_ACTION`.

A positive `I` means the deployment-like training distribution shifts the relative outcome toward MODE_GAIN. It does not require MODE_GAIN to become the better model. Report a paired crossed bootstrap over training seeds and held-out target IDs (10,000 resamples; fixed seed 20261021), alongside each regime's `G_r`. Also report per-arm distances, success, mean path distance, time-to-success, train loss, reversed-mapping outcomes, and mode-gain versus no-context contrasts. No other result substitutes for the primary interaction.

## Interpretation rules

- If `I` is positive and its 95% interval excludes zero, conclude only that this teacher-mixed training distribution preferentially changes the MODE_GAIN-versus-bilinear gap in this synthetic task.
- If `I` is near zero or negative, this teacher-mixed distribution did not explain the V1 relative disadvantage under the tested setup. Other causes (update equations, optimization, policy geometry, and teacher/test occupancy mismatch) remain possible.
- If MODE_GAIN remains worse even when `I` is positive, report that distribution alignment attenuated but did not remove its disadvantage.
- Do not describe any result as a successful biological-to-AI transfer, a validated mechanism, or a general advantage.

## Provenance and stop conditions

This post-result diagnostic is not a change to V1 and must not overwrite V1 artifacts. Retain any implementation incidents and failed runs in this experiment's failure log; only a complete run with a hash-verified independent analysis is canonical. No result-dependent changes to model equations, teacher mixture, primary contrast, seeds, or interpretation rules are allowed within this version.
