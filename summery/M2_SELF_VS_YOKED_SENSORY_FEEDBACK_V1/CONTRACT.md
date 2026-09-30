# M2 self-contingent versus yoked sensory feedback — contract

**Experiment ID:** `M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1`
**Classification:** retrospective, exploratory source-model mechanism probe. Previous M2 model and experiment outcomes are known.
**Execution status:** frozen before this experiment's simulation outcomes were generated.

## Question

In the corrected Ji et al. Figure 7 source-derived model, does sensory-site feedback improve environment-aligned movement because its moment-to-moment signal is contingent on the recipient's own motor state, beyond the effect of receiving a feedback signal with the same population-level time-varying distribution?

## Source model and task

Use the same source-derived state equations, integration step (`N_STEPS=1500`, `T_MAX=200 s`, `DT=T_MAX/N_STEPS`), 50 agents per seed block, 0.5-second sensory delay, transition timing, heading-reset process, and Gaussian noise scale 1 as `model/M2_FEEDBACK_SITE_SPECIFICITY_V5/source_model.py`. Sensory drive is `-1.5 * g(t) * (x(t)-x(t-0.5 s)) * 1[M(t)>0]`; feedback is the source term `sigmoid(15*M)` entering the AIY-like sensory-state update with coefficient 1. No parameter is fitted.

The warm-direction sign begins at +1 and reverses every 40, 20, 10, or 5 seconds; a stationary-gradient condition (`interval=0`) is also retained. Reversals change the sign on the position-difference sensory input and do not add a spatially uniform temperature jump.

## Arms

1. **`SELF_CONTINGENT`**: each agent receives its own current `sigmoid(15*M)` signal at the sensory-state update.
2. **`CROSS_AGENT_YOKED`**: each agent receives, at every time step, the simultaneously recorded `sigmoid(15*M)` signal from a different agent in its paired `SELF_CONTINGENT` seed-block trajectory. A fixed random derangement maps donors to recipients. Thus, within each seed block and environment, the multiset of feedback values across agents is exactly preserved at each time step, while recipient-specific contingency is broken. The yoke is a post-treatment replay from the paired self-feedback arm, not an independently generated intervention.
3. **`NO_FEEDBACK`**: sensory-site feedback input is zero.

All arms use identical noise, heading-reset, and initial-heading streams within a seed block. Self-arm feedback traces are generated first; yoked and no-feedback arms replay those same random streams. No outcome-informed coefficient calibration is performed.

## Estimand and analysis

**Primary environment:** 20-second reversal, selected to retain the preceding stress test's declared primary schedule.
**Primary endpoint:** aligned displacement rate `sum(-g(t)*Δx(t)) / (N_AGENTS*T_MAX)` per seed block; units are model-distance units per second.
**Primary contrast:** `SELF_CONTINGENT − CROSS_AGENT_YOKED`. The unit of inference is the simulation seed block (100 blocks; 50 agents and 1,500 steps are clustered within block). Report the mean paired difference and a two-sided 95% percentile-bootstrap interval using 20,000 seed-block resamples and analysis seed `20261015`.

Report all three arms at all five schedules. Secondary summaries are forward-state occupancy, mean forward-run duration, and self-minus-yoked aligned displacement contrasts at the other schedules. No pooling across schedules replaces the primary contrast. Also verify that the sorted feedback values across the 50 agents match exactly at every time point between the self-generated source trace and its yoke reassignment.

## Interpretation limits

- A positive primary contrast indicates that recipient-specific contingency contributes to this source-model simulation outcome beyond the preserved instantaneous population distribution of feedback values.
- The cross-agent yoke is derived from the paired self-feedback trajectory, so the contrast does not estimate an independently manipulable biological intervention and is not an animal-level causal effect.
- Exact marginal signal matching does not match each recipient's feedback history, autocorrelation, or interaction with its counterfactual state trajectory; those differences are part of breaking recipient-specific contingency.
- No result establishes a unique synapse, validates the biological mechanism, or demonstrates benefit in an artificial-intelligence system.
- This retrospective source-model probe cannot be described as a new independent confirmation. Do not tune the model or alter the primary schedule after observing outcomes.

## Reproducibility

The runner writes seed-block outcomes, a feedback-distribution check, environment/runtime information, and SHA-256 hashes of source inputs and outputs. The verifier recomputes the primary contrast and confirms complete keys, finite metrics, non-self donors, and exact per-time-step marginal preservation.
