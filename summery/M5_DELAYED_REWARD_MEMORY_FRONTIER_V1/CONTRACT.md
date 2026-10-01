# M5 delayed-reward bandit memory frontier V1

**Status:** post-result exploratory experiment. Prior delayed-label classification and contextual-bandit trace results are known. This run reuses the bandit task family on disjoint task seeds; it is neither confirmatory nor biological validation.

## Question

On the existing delayed scalar-reward contextual bandit, how does the accuracy–active-state frontier of a fixed eligibility trace compare with exact FIFO storage of decision-score vectors as FIFO capacity grows to cover the delay?

The experiment deliberately reports update coverage alongside accuracy: a short FIFO that has evicted the decision score cannot apply the delayed reward to that decision. The matched primary contrast alone is not interpreted without this coverage diagnostic.

## Task and seeds

Reuse the frozen generator and task parameters in `M5_DELAYED_REWARD_BANDIT_CONTRACT.md`: 16-dimensional normalized Gaussian contexts, two Bernoulli-reward actions with fixed seed-specific linear preferences, 6,000 training decisions, 2,000 held-out contexts, delays `D ∈ {1,4,16,64}`, linear-softmax policy, learning rate `0.01`, reward baseline `0.5`, and eligibility decay `γ=0.98`. Use task seeds `30..59`, disjoint from the prior run's `0..29`; keep the existing master seed `20260930`. No parameter is tuned.

Each task-seed/delay condition uses common contexts, action uniforms, and action-specific reward uniforms across arms. The policies can choose different actions and hence receive different rewards. Held-out expected reward is calculated from the known reward probabilities, without evaluation action-sampling noise.

## Arms and state accounting

Each decision's policy score is the same unit-Frobenius-normalized matrix `g_t` used by the prior bandit experiment (16 × 2 = 32 scalar values). Every arm has the same 16 × 2 learned policy weights; those common trainable values are excluded from *additional active credit-assignment state*. Shared contexts, delayed reward values, random numbers, and task storage are also excluded.

- `ELIGIBILITY_TRACE_32`: `e_t = 0.98 e_(t−1) + g_t`; when a delayed reward arrives, update along `e_t / ||e_t||` with advantage `r−0.5`. During flush, the trace decays with zero new score.
- `EXACT_FIFO_32`, `EXACT_FIFO_128`, `EXACT_FIFO_512`, `EXACT_FIFO_2048`: retain 1, 4, 16, or 64 exact 32-value score vectors. On reward arrival, apply the score for the decision that generated it if retained; otherwise skip that policy update. Update coverage is the fraction of 6,000 rewards applied.
- `NO_TRACE_CURRENT_32`: apply the arriving reward to the current decision score; during stream flush, current score is zero. Counts one 32-value transient score as its comparator state.
- `EXACT_REPLAY`: retain all delay-relevant score vectors (delay × 32 values); higher-memory reference.

Within each clock step, sample the current action from the pre-update policy, compute its score and reward, decay/add to the eligibility trace, deliver the reward due at the frozen delay and update the learners, then place the current score into each FIFO. This ordering lets a capacity-1 FIFO preserve the previous decision score for a delay-1 reward before replacing it with the new decision's score. It prevents the FIFO implementation from dropping a reward merely because the current score was inserted first.

The resource measure is the count of persistent active score/feature values, not measured process RAM, FLOPs, wall time, or energy. The distinction and excluded common task/interface state are part of the claim boundary.

## Outcomes and inference

- Task-native outcome: held-out expected reward (0–1 scale).
- Primary contrast: `ELIGIBILITY_TRACE_32 − EXACT_FIFO_32`, averaged equally over the four delays within each task seed, then across 30 task seeds. Report a paired task-seed bootstrap 95% interval with 20,000 resamples.
- Required frontier diagnostics: per-delay and per-capacity expected reward, active credit-assignment state, update coverage, and exact-replay comparison.
- Seeds are the independent units; delay and arms are paired within seed. No decision-level inferential statistics and no pooled cross-task score.

## Interpretation boundary

A positive matched contrast is evidence only about this fixed synthetic contextual-bandit task and this active-state accounting. If a FIFO's update coverage is low, its lower reward is an expected consequence of dropping delayed updates and must be reported as such. If an adequately sized FIFO or full replay is more accurate, that is part of the result. No general algorithm advantage, biological validation, architecture generalization, real-world efficacy, or NMI-level principle follows from this experiment alone.
