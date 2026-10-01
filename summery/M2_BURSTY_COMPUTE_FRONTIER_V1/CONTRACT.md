# M2_BURSTY_COMPUTE_FRONTIER_V1 — post-result exploratory contract

## Question and status

Does the sensory-site motor-feedback controller's result on bursty partial-observation tracking persist as the generic recurrent controls receive more optimization updates on the same amount of data? This is a post-result exploratory extension of `M2_BURSTY_OBSERVATION_FEEDBACK_V1`; that result and related M2 results are already known. It is not an independent confirmation, a biological validation, or a general AI test.

The motivating biological computation is bounded to the published *C. elegans* thermotaxis evidence: RIM-dependent motor-state information changes AIY sensory representation and is associated with persistence of the forward motor program. The task's Markov observation gaps and tracking objective are artificial. They are not claimed to reproduce an observed biological outage regime.

## Arms

- `SENSORY_SITE`: previous motor output enters the internal sensory-state update.
- `OUTPUT_SITE`: previous motor output enters only the motor-output equation.
- `NO_FEEDBACK`: no previous motor output enters either pathway.
- `GENERIC_RNN`: a four-parameter scalar tanh recurrent controller receiving observation, visibility, and previous motor output.
- `GRU_8`: an eight-unit GRU receiving the same three inputs and a scalar action head.

All controller parameters are trained end-to-end with the same training trajectories and optimizer-update budget. Parameter counts are reported; the generic scalar RNN is the four-parameter comparator, while the GRU is a higher-capacity reference, not a parameter-matched control.

## Fixed task and split

- 32 fresh training-seed blocks: `840500` through `840531`.
- 160 training episodes per seed; 160 steps per episode; target-switch hazard `1/40`.
- Training visibility transition probability `q=0.25`; observation noise SD `0.25`.
- Evaluation uses fresh target/noise/visibility streams at `q ∈ {0.50, 0.25, 0.125}` with 128 episodes per seed and condition. Expected missing fractions are not forced per episode; realized missingness is recorded.
- Evaluate checkpoints after 60, 120, and 240 optimizer updates, with fixed batch size 16 and learning rate 0.01. No test-set tuning or checkpoint selection.
- Primary condition: long-gap evaluation `q=0.125` at 240 updates. Primary contrasts are `MSE(GENERIC_RNN) − MSE(SENSORY_SITE)` and `MSE(GRU_8) − MSE(SENSORY_SITE)`; positive favors sensory-site feedback. Report paired training-seed contrasts and percentile bootstrap intervals. Other checkpoints, arms, and visibility conditions are descriptive secondary outcomes.
- Task-native secondary outcomes: MAE, action energy, and post-gap recovery steps.

## Computation, analysis, and interpretation

The maximum update budget is held equal across arms; wall-clock training time and parameter counts are recorded because update count does not equal compute. Seeds are the independent training/task blocks; episodes are nested observations and are not treated as independent replicates. Resample seed blocks for uncertainty. Report every arm and all frozen checkpoints/visibility conditions.

This experiment tests optimization-budget sensitivity within one artificial task family. Even if sensory-site feedback retains an advantage, that supports only an algorithmic result in this simulator. It does not show that the artificial task reflects the measured biological operating conditions, establish a unique causal synapse, or establish general AI benefit. Any outcome, including a reversal at higher update budgets, will be preserved.

## Artifacts

- Runner: `model/M2_BURSTY_COMPUTE_FRONTIER_V1/run_experiment.py`
- Verifier: `model/M2_BURSTY_COMPUTE_FRONTIER_V1/verify_results.py`
- Outputs: `data/results/M2_BURSTY_COMPUTE_FRONTIER_V1/`
- Interpretation and failure lessons: this directory.
