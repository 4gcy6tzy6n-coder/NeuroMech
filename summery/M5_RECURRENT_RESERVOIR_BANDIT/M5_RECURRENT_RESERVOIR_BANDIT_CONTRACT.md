# M5 eligibility update in a recurrent reservoir policy

**Status:** `POST_RESULT_EXPLORATORY_CONTRACT_FROZEN_BEFORE_RUN`. The M5 classification and feed-forward contextual-bandit results are known. This is an outcome-informed architecture follow-up, not confirmatory evidence or biological validation.

## Question

Does the fixed norm-matched eligibility update retain an advantage over a no-trace update when policy features come from an actual recurrent dynamical state rather than directly from the current context?

## Recurrent policy architecture

- Input is a 16-dimensional unit-norm context. A fixed random reservoir with 16 hidden units evolves as
  `h_t = α h_(t−1) + (1−α) tanh(W_in x_t + W_rec h_(t−1))`,
  where `α=exp(−1/4)`, `W_in` is drawn from a frozen seed-specific Gaussian distribution, and `W_rec` is orthogonal with spectral radius `0.8`.
- The recurrent core is fixed during training. A trainable 16×2 linear softmax readout selects one of two actions from `h_t`; the readout starts at zero.
- This is a recurrent reservoir policy with a learned readout, not a fully trained RNN/LNN and not a liquid time-constant network. The distinction must remain explicit.

## Task and fixed training setup

- Use the same two-action contextual-bandit reward rule as the prior M5 bandit test: each task seed draws unknown action preferences `theta_a ~ Normal(0,I_16)`; reward probability is `sigmoid(x·theta_a)`.
- Use 6,000 training contexts and 2,000 fresh held-out contexts per task seed. Reservoir state starts at zero at the start of each train/test stream; contexts and action-specific potential reward uniforms are shared across paired arms and delays within seed.
- Thirty independent task seeds; feedback delays `D ∈ {1,4,16,64}`.
- Fixed advantage baseline `0.5`, learning rate `0.01`, and trace decay `γ=0.98`; no tuning based on prior or current outcomes.
- The hidden-state sequence is generated once per seed and is common to all update arms because the fixed reservoir does not depend on actions or readout weights.

## Credit-assignment arms

For each decision, compute the softmax score for the readout, `g_t = ∇_(W_out) log π(a_t|h_t)`, and normalize it to unit Frobenius norm in every arm.

1. `EXACT_REPLAY`: apply the delayed scalar advantage to the decision's stored score vector.
2. `ELIGIBILITY_TRACE_NORM_MATCHED`: accumulate `e_t=γe_(t−1)+g_t`; apply the delayed advantage along `e_t/||e_t||`.
3. `NO_TRACE`: apply the delayed advantage to the current decision score; during reward-drain steps the current score is zero.

The recurrent core, policy readout parameter count, optimizer, baseline, training horizon, task, and common random numbers are matched across arms. Exact replay is a higher-memory reference, not the primary comparator.

## Primary analysis

- Primary outcome: held-out expected reward under the learned softmax policy, averaged over 2,000 held-out contexts. Expected reward is computed from the simulator's true reward probabilities only for evaluation; learners never receive `theta` or probabilities.
- Primary contrast: `ELIGIBILITY_TRACE_NORM_MATCHED − NO_TRACE`, averaged equally across four delays within each task seed, then across 30 task seeds.
- Paired task-seed bootstrap 95% interval with 20,000 resamples. Task seed is the independent unit; delays and arms are paired repeated conditions.
- Report per-delay and trace-minus-exact-replay means descriptively; do not treat decision steps as independent.

## Interpretation and stop rule

- Positive primary interval: evidence for a trace advantage over no-trace in this fixed recurrent-reservoir contextual bandit only.
- Interval spanning zero: inconclusive in this architecture/task.
- Exact replay and its performance gap must always be reported.
- This run does not test recurrent-core learning, architecture-family generalization, a full LNN, a biological circuit, or connectome-derived structure.
- Run once and stop. Do not tune reservoir radius, leak, learning rate, baseline, trace decay, or task after seeing results. Further changes need a new post-result contract.
