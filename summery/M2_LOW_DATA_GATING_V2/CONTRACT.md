# M2 low-data conditional-update benchmark V2

**Experiment ID:** `M2_LOW_DATA_GATING_V2`
**Classification:** post-result exploratory artificial benchmark. V1 and prior M2 synthetic outcomes are known; V2 uses disjoint task seeds and a stronger parameter-matched comparator. It is not confirmatory or biological validation.

## Question

Does a compact state-conditioned sensory-update rule outperform a generic recurrent rule that can express an input-by-context interaction, when both have four parameters and receive identical training tokens? Does any contrast change if the context-to-observation map is independent or reversed?

## Task and data

The task is the same fixed scalar AR(1) family and mapping definition as V1: `x_t=phi*x_(t-1)+eps_t`; binary context `q_t` switches with probability 0.05; observation `y_t=H(q_t)*x_t+sigma_obs*z_t`. Training uses ALIGNED `H(+1)=1,H(-1)=0`. Evaluation conditions are ALIGNED, INDEPENDENT (`H=0.5`), and REVERSED (`H(+1)=0,H(-1)=1`). These are synthetic mappings, not claims about the measured worm computation.

Training seeds are `71000..71019`, disjoint from V1. There are 20 seed clusters; each seed generates nested training pools of 16, 64, 256, or 1024 sequences and 256 held-out sequences per evaluation condition. Sequences have 160 time steps. Paired models share the same training pool, minibatch-index sequence, initialization convention, held-out sequences, and evaluation-noise streams.

## Models and resource matching

`MODE_GAIN_FILTER` has four trainable parameters and uses context-conditioned gains on a sensory prediction error. `GENERIC_BILINEAR_RNN_1D` also has four trainable parameters and uses an unconstrained tanh update with `y`, `q`, `y*q`, and prior hidden state. Each fit uses 250 Adam updates at learning rate 0.02, batch size 16, gradient clipping at 5, and 640,000 sequence-step tokens. The models have equal parameter counts, update counts, minibatch sizes and token budgets. Exact FLOPs are not assumed equal; training wall-clock is recorded as secondary information.

## Outcomes and estimand

Primary: sequence-mean squared error averaged equally over the four data sizes in ALIGNED evaluation. Contrast: `MSE(GENERIC_BILINEAR_RNN_1D) − MSE(MODE_GAIN_FILTER)`; positive favors the structured update. The unit is the paired training seed. Report a 20,000-resample seed bootstrap 95% interval and the per-size contrasts. INDEPENDENT and REVERSED are separately reported boundary conditions; no pooling with ALIGNED is used for the primary.

## Interpretation

This is a synthetic test of a conditional inductive bias against a parameter-matched generic model that can express multiplicative context-input interaction. Any observed benefit is limited to this architecture and task family. It cannot establish that the mapping is biologically measured, that the model reproduces worm physiology, or that the result generalizes to other task families or AI systems. No post-result tuning or seed selection is allowed.
