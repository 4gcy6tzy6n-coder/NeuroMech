# M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1 — exploratory computation test

## Question and scope

Does routing self-generated motor state into a sensory-state update improve inference of signed position error when a hidden environmental gradient reverses and sensory observations are intermittently missing?

The biological motivation is bounded to *C. elegans* work reporting RIM-dependent motor-state effects on AIY sensory representation and forward-state persistence (Ji et al., 2021, https://elifesciences.org/articles/68848). This study operationalizes a candidate computation—using action-conditioned sensory history to infer hidden state. The paper does not establish that worms explicitly estimate gradient sign or signed position error, and this artificial task is not a biological reproduction. Efference-copy and motor-to-sensory prediction are established prior art; no novelty claim is made for those concepts alone.

This is a post-result exploratory follow-up to `M2_LTC_THERMOTAXIS_REVERSAL_V1`. It separates a state-estimation computation from the failed end-to-end control-learning setup. It cannot serve as independent confirmation or establish a general AI benefit.

## Generative task

Each episode has a hidden signed displacement `d_t`, hidden gradient sign `g_t ∈ {−1,+1}`, and self-generated movement command `u_t`. The physical state changes as `d_(t+1) = clip(d_t + c*u_t, −2, +2)`, where `c` is the environment's action-to-state coupling. The sensory signal is `y_t = g_t*d_t + ε_t`, with Gaussian sensor noise SD `0.15`. The gradient sign reverses with hazard `1/40`. Observations are visible/missing under a two-state Markov process with transition probability `q=0.25` and stationary visible probability `0.5`. Actions follow a bounded, persistent, zero-mean AR(1) process and are generated independently of model predictions, so the supervised task tests state inference rather than policy learning.

The learner receives the current masked sensory value, visibility indicator, and previous motor command. Its target is the latent signed displacement `d_t`, not the noisy sensory value. Inferring sign requires combining sensory history with the direction and magnitude of self-motion. Train only on aligned coupling `c=+1`. Evaluate on paired held-out episodes at `c=+1` (primary), `c=0` (motor cue carries no information about displacement changes), and `c=−1` (the learned action-to-state relation is reversed).

## Model arms

All LTC arms use the same four-unit equation-level liquid time-constant cell, trainable tensors, initialization family, optimizer, training examples, and update budget. Two hidden units are designated sensory-state units. The direct conductance-style ODE is numerically unfolded four times per discrete step; it is not asserted to be a bitwise `ncps` reproduction.

- `LTC_SENSORY_SITE`: previous self motor command enters only the two designated sensory-state units' input current.
- `LTC_OUTPUT_SITE`: previous motor command enters the estimate readout only.
- `LTC_NO_FEEDBACK`: motor command is not supplied to the estimator.
- `LTC_DENSE_FEEDBACK`: previous motor command enters all LTC units.
- `LTC_SENSORY_YOKED`: sensory-site update receives the motor command from another episode, cyclically permuted within each evaluation/training batch.
- `GRU_2`: near-capacity-matched generic recurrent control; report exact parameter count.
- `GRU_4`: larger generic recurrent reference.
- `SIGNED_STATE_ORACLE`: privileged reference given current `g_t` and `y_t`; not included in learned-model contrasts.

## Frozen training and analysis

- 32 training-seed blocks, 256 episodes per seed, 128 steps per episode.
- 160 full-batch Adam updates at learning rate `0.003`; batch size is 32 episodes, sampled with replacement from each seed's fixed training set.
- Evaluation uses 256 fresh paired episodes per seed × model × coupling condition.
- Primary endpoint: mean squared error for signed displacement estimation, averaged within episode and then within training-seed block.
- Secondary endpoints: absolute displacement error and signed prediction bias.
- Primary condition: aligned held-out coupling `c=+1`.
- Primary contrasts: comparator MSE minus `LTC_SENSORY_SITE` MSE. Positive values favor sensory-site feedback. Compare output-site, no-feedback, dense-feedback, yoked, `GRU_2`, and `GRU_4`.
- Generalization contrasts at `c=0` and `c=−1` are secondary and are reported without changing the primary decision.
- Independent unit: training-seed block. Use 20,000 paired percentile bootstrap resamples, RNG seed `20261004`.
- Report exact trainable parameter counts, final training loss, held-out endpoint summaries, and privileged-oracle performance. Do not treat episodes or time steps as independent units.

## Interpretation

Evidence for the bounded computation requires sensory-site feedback to outperform both output-site and yoked feedback on the primary state-estimation endpoint, with uncertainty intervals excluding zero in the predicted direction. A gain over generic recurrent controls is a separate resource/comparator result. No primary difference, a yoked control matching sensory-site, or a benefit that does not generalize to fresh held-out episodes fails to support the specific self-contingent sensory-update claim. A near-oracle result does not establish biological identity. Regardless of outcome, this is an artificial computation test, not new biological evidence or a general AI claim.

No post-result parameter changes, selective seed exclusions, or alternate-primary substitutions are allowed within this version. A revised task or training setup must use a new experiment ID and contract.

## Artifacts

- Runner: `model/M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1/run_experiment.py`
- Analysis / verifier / figure: `model/M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1/`
- Results: `data/results/M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1/`
- Results and failure lessons: this directory.
