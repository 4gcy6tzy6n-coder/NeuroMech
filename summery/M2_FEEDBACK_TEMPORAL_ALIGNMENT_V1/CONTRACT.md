# M2 feedback temporal-alignment experiment V1

**Classification:** exploratory, outcome-informed artificial mechanism-transfer experiment. Prior M2 biological literature and artificial transfer results are known. This is not a biological intervention, independent animal replication, or general AI claim.

## Motivation and question

The C. elegans RIM–AIY literature motivates a computation in which motor-state feedback contributes to sensory-state representation. A recent project simulator found a recipient-contingency advantage over a cross-agent yoke in one slow-transient target-tracking condition, while output placement and stronger recurrent controls had lower movement error. The next computational discriminator is whether the feedback signal must be temporally aligned with the current motor state, or whether a delayed self-signal retains the same effect.

Question: in a synthetic target-tracking controller exposed to transient contradictory observations, how does a fixed feedback delay (0, 1, or 4 steps) at the sensory-state update change held-out motor-state error, relative to output-site feedback, cross-agent yoking, no feedback, and recurrent controls?

## Task and arms

Reuse the binary target-tracking task and training procedure from `M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1`, including its four held-out conditions, target hazards, two-step contradictory sensor pulses, motor plant, noise, optimizer, 100 updates, batch size 32, and sequence length 96. All arms within a block use paired exogenous training and held-out streams.

Arms:

- `SELF_SENSORY`: current motor-state feedback enters the sensory-state update (0-step lag; 4 trainable parameters).
- `LAG1_SENSORY`: the same update receives its own motor-state feedback from one step earlier (4 parameters).
- `LAG4_SENSORY`: the same update receives its own motor-state feedback from four steps earlier (4 parameters).
- `CROSS_AGENT_YOKED_SENSORY`: sensory update receives a fixed derangement of another episode's contemporaneous feedback, matched exactly at each time across the evaluation population (4 parameters).
- `SELF_OUTPUT`: current motor-state feedback enters the output command (4 parameters).
- `NO_FEEDBACK`: no motor feedback (3 parameters).
- `GENERIC_RNN_1D`: additive scalar recurrent control (6 parameters).
- `GRU_8`: eight-unit recurrent reference (297 parameters).

For delayed-self arms, the initial lag buffer is zero; thereafter the controller uses `sigmoid(5 × motor_state[t−lag])`. All three sensory arms share the same state-update equation and optimizer. The only intended architectural difference among them is feedback latency. The lag values are fixed before the run and are not selected from the outcomes.

## Outcomes and inference

Primary condition: `SLOW_TRANSIENT` (target-switch hazard 0.01, contradictory-pulse onset rate 0.08, pulse duration 2 steps). Primary metric: held-out movement MSE. Primary contrast: `LAG4_SENSORY − SELF_SENSORY` across 32 paired training seed blocks; positive values favor current alignment. The 95% percentile bootstrap interval resamples seed blocks (20,000 draws; seed 8765433). The 1-step contrast and other arms/conditions are secondary descriptive comparisons; no post-run lag selection or pooled cross-condition effect is allowed.

Training seeds: 820000–820031. Test episodes: 128 per seed block and condition. Seed blocks, not frames or trajectories, are the inferential units.

## Interpretation limits and verification

A lower error for the current-alignment arm than for delayed feedback would support temporal alignment as a useful computational feature in this synthetic controller. It would not establish that a biological circuit implements this exact lag, that biological feedback is causal, or that the model improves general AI. If generic or GRU controls outperform the structured arms, that remains part of the result. Parameter counts are reported and not treated as compute equivalence.

The verifier checks row coverage, fitted parameter counts, exact yoke derangements and per-time population-distribution matching, seed-level aggregation, primary contrast recomputation, and artifact hashes. An independent full rerun is required for bitwise reproducibility of scientific outputs; `training_seconds` may differ.
