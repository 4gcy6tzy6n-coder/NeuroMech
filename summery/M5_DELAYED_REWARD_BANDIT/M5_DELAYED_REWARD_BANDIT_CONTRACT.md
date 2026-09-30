# M5 delayed-reward contextual-bandit transfer test

**Status:** `POST_RESULT_EXPLORATORY_CONTRACT_FROZEN_BEFORE_RUN`. Prior M5 delayed-label classification outcomes are known. This is a new task objective and an outcome-informed transfer test; it is not confirmatory and does not validate a cerebellar mechanism.

## Question

Does the fixed norm-matched eligibility update used in M5 retain a measurable benefit over a no-trace current-decision update when feedback is a delayed scalar reward in a contextual decision task, rather than a delayed supervised class label?

## Task and data-generating process

- Each independent task seed creates an unknown linear reward preference for each of two actions: `theta_a ~ Normal(0, I_16)`.
- At each training step, draw a 16-dimensional standard-normal context and normalize it to unit L2 norm. For action `a`, reward is Bernoulli with probability `sigmoid(x · theta_a)`.
- A policy is a two-action softmax with a learned 16×2 weight matrix initialized to zero. At decision time it observes only the context and samples an action from its current policy; it receives the binary reward only after the frozen delay `D ∈ {1, 4, 16, 64}`.
- Train for 6,000 contexts and evaluate on 2,000 fresh contexts per seed. Evaluation uses expected reward under the learned softmax and the known task reward probabilities, avoiding policy-sampling noise in the endpoint.
- Use 30 independent task seeds. Contexts and potential reward uniforms are shared across the three paired arms and delays within a task seed; policies may choose different actions and therefore receive different realized rewards.
- The update baseline is fixed at `0.5`; learning rate is `0.01`; trace decay is `γ=0.98`. These are carried forward unchanged from the M5 study; no hyperparameter tuning or pilot outcome inspection is allowed.

## Credit-assignment arms

For each decision, calculate the policy score `g_t = ∇_W log π(a_t|x_t)` and normalize it to unit Frobenius norm. This same per-decision normalization is applied in every arm so that the contrast isolates temporal assignment rather than score-vector magnitude.

1. `EXACT_REPLAY`: on reward arrival, update with the stored score vector from the decision that generated that reward.
2. `ELIGIBILITY_TRACE_NORM_MATCHED`: accumulate `e_t = γ e_(t−1) + g_t`; on reward arrival, update along `e_t / ||e_t||` using the delayed advantage `r−0.5`.
3. `NO_TRACE`: on reward arrival, update with the current decision's normalized score `g_t` and the delayed advantage. During post-stream reward delivery, this current score is zero.

The same policy parameter count, initial weights, reward rule, training horizon, learning rate, baseline, contexts, action-sampling uniforms and potential-reward uniforms apply to all arms. Exact replay retains per-decision score information and is a higher-memory reference, not the primary comparator.

## Outcomes and inference

- Primary outcome: mean expected reward over the 2,000 held-out contexts after training and draining all delayed rewards.
- Primary contrast: `ELIGIBILITY_TRACE_NORM_MATCHED − NO_TRACE`, averaged equally over the four delays within each task seed; then averaged over the 30 task seeds.
- Report a paired task-seed bootstrap 95% interval with 20,000 resamples. Task seed is the independent unit; decision steps and delays are nested/repeated observations.
- Secondary descriptive outcomes: generator/delay-specific expected reward, exact-replay contrast, and training reward trajectories. Do not promote secondary contrasts to confirmatory claims.

## Interpretation and stop rules

- A positive interval supports only a benefit of this fixed trace over no-trace in the specified two-action contextual bandit and delay set.
- An interval spanning zero is inconclusive for this transfer test.
- A negative interval means the trace did not help this fixed bandit; it does not refute biological eligibility mechanisms.
- Exact replay's performance and higher-memory distinction must be reported even if the primary contrast is favorable.
- This is a different task objective from supervised classification, but it remains a small synthetic task. It does not demonstrate generalization across arbitrary tasks, architectures, real datasets, or biological circuits.
- Run once and stop. Do not tune learning rate, baseline, γ, context dimension, reward function, or delay grid after inspecting results. Any next experiment requires a new explicitly post-result contract.
