# M5 delayed-reward trace-horizon sweep V1

**Classification:** outcome-informed exploratory follow-up. Earlier delayed-reward bandit, trace-vs-replay, and eligibility results are known. This experiment neither re-tests the biological source nor serves as confirmatory or NMI-level generalization evidence.

## Question

In the existing stationary contextual bandit with delayed scalar reward, does a fixed eligibility decay horizon change performance relative to immediate-score assignment, and how does each compare with exact replay? The task delivers one reward for one prior action. This is a deliberately stringent setting for a trace that pools several recent score vectors.

## Task, seeds, and arms

Reuse the task generator and learning schedule specified in `summery/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/CONTRACT.md`: 16-dimensional normalized Gaussian contexts; two actions with seed-specific fixed linear reward probabilities; 6,000 training decisions; 2,000 independent held-out contexts; delays `D ∈ {1,4,16,64}`; linear-softmax policy; learning rate `0.01`; reward baseline `0.5`; score vectors normalized to unit Frobenius norm. Use task seeds `61–90`, disjoint from previously used seed ranges `0–59` and the separate implementation smoke check on seed 60. Within seed and delay, all arms share contexts, choice uniforms, and action-specific reward uniforms.

Compare `TRACE_GAMMA_0.50`, `TRACE_GAMMA_0.75`, `TRACE_GAMMA_0.90`, `TRACE_GAMMA_0.98`, `EXACT_REPLAY`, and `NO_TRACE_CURRENT_32`. Each trace holds one 32-value eligibility state. Exact replay retains the delay-relevant score history (`32 × (D+1)` values). No-trace assigns the arriving reward to the current score. Shared model weights and task/environment state are excluded equally from additional transient credit state; this is a logical active-state count, not a measured RAM/compute/energy benchmark. An exact 32-value FIFO is omitted because a deterministic delay D requires retaining D pending score vectors; the previous M5 memory-frontier study already compared that capacity frontier and its update-coverage consequences.

For each delayed reward, trace arms update along the unit-normalized recurrence `e_t = γ e_(t−1) + g_t`, where `g_t` is that arm's current policy score. Exact replay applies the stored score for the decision that generated the reward using a delay-sized ring. Updates occur after the current action is selected, and before its score is entered in the replay ring.

## Outcomes and analysis

Primary outcome: held-out expected reward, averaged over held-out contexts. The independent unit is the task seed; delays and arms are paired within seed. Report every `γ × D` cell. Primary contrasts are each trace minus `NO_TRACE_CURRENT_32`; secondary contrasts are each trace minus `EXACT_REPLAY`. Do not pool across delays, because that would conceal horizon-by-delay interactions. For the 16 trace-versus-no-trace primary cell contrasts, use paired seed-bootstrap intervals with Bonferroni familywise coverage (two-sided per-cell confidence level `1 − 0.05/16`; 20,000 resamples). Report exact-replay contrasts with ordinary paired 95% bootstrap intervals as descriptive secondary analyses.

No gamma is selected after seeing the test-seed results. A positive cell contrast only supports a task-bounded advantage over assigning the delayed reward to the current score. It does not show superiority to exact replay, general delayed-credit advantage, biological validation, or broad AI benefit. The biological M5 evidence motivates testing temporally decaying teaching eligibility; it does not specify these gamma values or establish that a cerebellar synapse implements this bandit rule.

## Reproducibility

The preflight record is stored at `data/results/M5_DELAYED_REWARD_TRACE_HORIZON_V1/PREFLIGHT.json`; canonical run outputs are written to its `canonical/` subdirectory. The run records the frozen contract and code hashes, environment, seed range, task settings, output hashes, and all seed-level paired outcomes. The verifier recomputes all cell estimates and intervals from raw seed rows and checks row completeness and the output manifest. The runner refuses to overwrite a nonempty result directory.
