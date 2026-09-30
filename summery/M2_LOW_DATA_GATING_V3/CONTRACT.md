# M2 conditional-update benchmark V3: linear controls and Kalman reference

**Experiment ID:** `M2_LOW_DATA_GATING_V3`
**Classification:** post-result exploratory artificial benchmark. V1/V2 outcomes are known; V3 uses disjoint task seeds and is not confirmatory or biological validation.

## Question

Is the M2-inspired context-conditioned gain useful beyond a context-free linear state filter, and does it outperform a more expressive unconstrained linear bilinear state update? A task-aware Kalman filter provides an analytical reference under the known synthetic process.

## Task, seeds, and units

Use the scalar AR(1) family and observation mappings from V1/V2: `x_t=phi*x_(t-1)+eps_t`, binary state `q_t`, `y_t=H(q_t)*x_t+sigma_obs*z_t`. Training is ALIGNED (`H(+1)=1,H(-1)=0`); evaluation is ALIGNED, INDEPENDENT (`H=0.5`), and REVERSED (`H(+1)=0,H(-1)=1`). These observation rules are artificial and are not asserted to be a measured biological mechanism.

Use 20 paired task seeds `72000..72019`, with 16/64/256/1024 nested training sequences and 256 held-out sequences per seed and mapping; each sequence has 160 steps. The task seed is the inferential unit. Training pools, minibatch index streams, initialization rules and held-out streams are paired across learned models.

## Models

- `MODE_GAIN_FILTER`: four parameters; state-dependent gains update a leaky state estimate with a bounded bias.
- `CONSTANT_GAIN_FILTER`: three parameters; same leaky prediction-error form but one gain shared across both contexts. This is the context-free mechanism ablation.
- `LINEAR_BILINEAR_RNN`: five parameters; an unconstrained linear update includes `y`, `q`, `y*q`, `h`, and `q*h` terms, allowing separate context effects on current evidence and state persistence. Its recurrence coefficients are bounded for numerical stability. This is intentionally more expressive and has one extra parameter.
- `KALMAN_ORACLE`: uses each test sequence's true AR coefficient, process/observation noise and actual observation mapping. It is a task-aware analytical reference, not a learned or capacity-matched competitor.

Each learned fit receives 250 Adam updates (`lr=0.02`), batch size 16 and 640,000 sequence-step tokens, with gradient clipping at 5. Report parameter counts and measured runtime. Parameter count is not equal across all learned arms; the bilinear control is deliberately more expressive.

## Outcomes

Primary contrast: `MSE(LINEAR_BILINEAR_RNN) − MSE(MODE_GAIN_FILTER)` in ALIGNED, averaged equally across the four train sizes. Positive favors the state-conditioned filter. Also report `MSE(CONSTANT_GAIN_FILTER) − MSE(MODE_GAIN_FILTER)` to test whether context helps over the direct ablation, and every model/mapping/train-size absolute MSE. Use paired task-seed bootstrap intervals (20,000 resamples) and do not treat time steps or episodes as independent task seeds. Mapping conditions are never pooled for the primary.

## Interpretation

This is a synthetic scalar estimation benchmark. A result may distinguish this update family from these controls under this task and budget; it cannot validate the worm computation, establish an AI-general principle, or substitute for biological intervention. The Kalman result indicates how much task-specific performance remains available to a known-parameter estimator. All outcomes, including control wins or task nonviability, are retained.
