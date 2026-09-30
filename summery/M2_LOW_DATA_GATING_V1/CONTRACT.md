# M2 low-data conditional-update benchmark V1

**Experiment ID:** `M2_LOW_DATA_GATING_V1`
**Classification:** post-result exploratory artificial benchmark. Earlier M2 synthetic runs are public and known; this study is a new sample-efficiency question, not a confirmatory test or a biological validation.

## Question

Does a compact state-conditioned sensory-update rule learn more accurately from limited aligned training data than a parameter-matched unconstrained recurrent update, and how does each behave if the state-to-observation mapping changes?

## Task

Each sequence is a scalar latent AR(1) process, `x_t = phi*x_(t-1) + eps_t`, with per-sequence `phi ~ Uniform(0.84, 0.96)`, process-noise SD `Uniform(0.08, 0.18)`, and observation-noise SD `Uniform(0.15, 0.35)`. A binary context `q_t ∈ {-1,+1}` switches with probability 0.05. The observation is `y_t = H(q_t)*x_t + sigma_obs*z_t`. The training mapping is ALIGNED: `H(+1)=1`, `H(-1)=0`. Evaluation uses the same latent/context/noise innovations in ALIGNED, INDEPENDENT (`H=0.5` for both states), and REVERSED (`H(+1)=0`, `H(-1)=1`) conditions. These are deliberately synthetic task mappings; the mapping is not claimed to be measured biology.

## Models and resource matching

Both models have one scalar recurrent state and exactly four trainable parameters. `MODE_GAIN_FILTER` applies context-dependent gains to the sensory prediction error. `GENERIC_RNN_1D` uses an unconstrained tanh recurrent update with sensory input, context, and prior state. Each receives the same training sequences, initialization convention, minibatch indices, optimizer, number of optimizer steps, batch size, gradient clipping, and evaluation streams. Adam uses learning rate 0.02; training uses 250 updates of 16 sequences each. Training-set sizes are 16, 64, 256, and 1024 sequences. The training-seed unit controls independently sampled task pools; evaluation episodes are nested within seed and condition. Equal parameter count and equal optimizer-step/sample-token budgets are matched; exact wall-clock/FLOP equivalence is not assumed and measured runtime is retained.

## Outcomes

Primary outcome: per-sequence mean-squared latent-state estimation error, averaged equally over the four training-set sizes in ALIGNED evaluation. Primary contrast: `MSE(GENERIC_RNN_1D) − MSE(MODE_GAIN_FILTER)`; positive values favor the state-conditioned update. The inferential unit is the paired training seed. Report a paired seed bootstrap 95% interval and each training-size contrast. ALIGNED, INDEPENDENT, and REVERSED conditions are reported separately; no cross-condition pooling beyond the prespecified equal-weighted ALIGNED primary summary.

There are 20 paired training seeds (`70000..70019`), 256 held-out sequences per training seed and condition, and 160 time steps per sequence. Hyperparameters and training sizes are fixed before the run. No tuning or seed selection is allowed after outcome inspection.

## Interpretation limits

This experiment can test a low-data inductive-bias claim on this scalar synthetic family. It cannot establish that the artificial observation mapping is the worm circuit's computation, that the model reproduces the source biology, or that the benefit generalizes to other tasks or AI systems. A null or negative outcome is retained as evidence against the narrow low-data advantage.
