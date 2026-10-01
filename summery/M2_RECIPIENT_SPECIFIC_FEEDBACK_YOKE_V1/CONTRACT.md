# M2 recipient-specific motor-feedback yoke — V1 contract

**Experiment ID:** `M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1`

**Classification:** post-result exploratory artificial mechanism-transfer study. It is outcome-informed by M2 source-model, binary decision, and sparse-tracking results. It is not independent confirmation, biological validation, or evidence of general AI benefit.

## Question and biological anchor

Does recipient-specific motor feedback at a sensory-state update improve closed-loop tracking relative to a cross-agent yoke that preserves the donor motor-signal distribution but breaks its correspondence to the recipient's current target and sensory history?

The biological anchor is limited to published evidence that motor-state feedback is represented in AIY, depends on RIM, and supports locomotor persistence during *C. elegans* thermotaxis (Ji et al., 2021, eLife; recorded in `summery/MECHANISM_EVIDENCE_REGISTRY.md`). The synthetic previous-action signal is an abstraction of recipient-specific motor-state feedback; the experiment does not assert that worms track visual targets or implement these equations.

## Task and held-out design

Reuse the frozen one-dimensional sparse-sensation tracking environment from `M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1`: a binary target switches with Markov hazard; cursor position is bounded to `[-1,1]`; observation is `target − cursor + Normal(0, 0.25²)` and may be occluded, in which case the observation is exactly zero; movement changes cursor position by `0.08 × motor_command`. This task is adaptive and action-coupled, unlike the earlier noninteractive binary-state classification task.

Use 32 fresh training seed blocks `420000..420031`, 256 training episodes per seed, length 240, target hazard `1/120`, and missingness `0.50`. Train on shared exogenous target/noise/visibility sequences with 100 Adam updates, batch 16, learning rate `0.01`, and the same closed-loop loss and action penalty as the prior sparse-tracking contract. Evaluate 256 held-out episodes per training seed at the frozen grid of hazards `{1/240, 1/120, 1/40}` and missingness `{0.25, 0.50, 0.75}`. Pair target/noise/visibility streams across policy arms.

For every held-out condition, first run the trained sensory-site policy in ordinary self-feedback mode on each of the 256 paired exogenous episodes and save its motor-command sequence. Construct a seed-fixed random derangement of episode IDs (no episode donates to itself) and feed each recipient the precomputed self-action sequence of its matched donor. This preserves the empirical cross-agent motor-signal distribution exactly at every time step while breaking the within-recipient correspondence between motor signal and current target/observation history. The donor permutation is fixed before scoring, and no recipient outcome may select a donor or alter the permutation.

## Frozen policy arms

All learned arms have three trainable scalar parameters and receive equal optimizer updates and sequence-step budgets.

- `SENSORY_SELF`: `h_t = ρ h_(t−1) + α y_t + β m_(t−1)`; `m_t = tanh(1.5 h_t)`. The prior motor command is the recipient's own.
- `SENSORY_CROSS_AGENT_YOKE`: the same trained model and fitted parameters, but the feedback input is the bijectively assigned donor command at time `t−1`.
- `OUTPUT_SITE_PERSISTENCE`: `h_t = ρ h_(t−1) + α y_t`; `m_t = tanh(1.5 h_t + β m_(t−1))`.
- `NO_FEEDBACK`: `h_t = ρ h_(t−1) + α y_t + b`; `m_t = tanh(1.5 h_t)`.
- `GENERIC_RNN_1H`: `h_t = tanh(w_h h_(t−1) + w_y y_t + w_m m_(t−1))`; `m_t = tanh(1.5 h_t)`. This is parameter-matched to the three-parameter placement arms.
- `ORACLE_RELATIVE_ERROR`: uses the true current relative target position and the common fixed action rule. It is a task-aware reference, not a matched learned controller.

Use the exact coefficient bounds, initialization scheme, loss, and training optimizer from `M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1`; the runner will pin these by source hash. The yoke is an evaluation-time counterfactual on the fitted sensory-site policy, not a separately trained model.

## Outcomes and analysis

Primary endpoint: held-out episode mean squared tracking error in the training-range condition `(hazard=1/120, missingness=0.50)`. Primary contrast: `MSE(SENSORY_CROSS_AGENT_YOKE) − MSE(SENSORY_SELF)`; positive favors recipient-specific feedback. Estimate a paired crossed-bootstrap 95% interval over the 32 training-seed blocks and 256 held-out episode IDs (10,000 resamples, seed `20261029`). Report the mean paired difference in each seed block and the fraction of positive blocks.

Secondary outcomes, reported separately by condition: contrasts of `SENSORY_SELF` against output-site persistence, no-feedback, the parameter-matched generic RNN, and the task-aware oracle; switch-recovery delay after target reversals; action energy; and the self-versus-yoke contrast across hazard/missingness shifts. Do not pool conditions into one score. MSE reductions under this synthetic task do not imply biological or general AI benefit.

## Interpretation boundary

- A positive primary contrast supports only recipient-specificity of this motor-feedback signal in this simulated, action-coupled tracking task.
- A null/negative primary contrast means recipient-specific feedback did not improve tracking over the distribution-preserving cross-agent yoke under this design; it does not refute the biological findings.
- If recipient-specific feedback beats the yoke but loses to the parameter-matched generic RNN or no-feedback arm, report the specific contingency effect without claiming a net performance advantage.
- If the yoke preserves each time-point cohort distribution but has strong recipient mismatch, this identifies dependence on individual alignment; it does not distinguish all possible latent-history or donor-coupling mechanisms.
- A positive result remains post-result exploratory. It cannot establish animal-level causality, a unique biological carrier, independent replication, or a general AI principle.

## Provenance and execution freeze

This contract is fixed before the new V1 runner and before producing its outcome files. Prior results motivated the yoke, so the study is retrospective/exploratory by design. Preserve all outcomes and execution incidents. Do not alter the seed range, primary contrast, donor permutation, evaluation grid, optimizer budget, or interpretation after results are generated; any changed design requires a new experiment ID.
