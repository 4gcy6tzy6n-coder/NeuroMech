# M2 feedback-site specificity robustness V3

**Experiment ID:** `M2_FEEDBACK_SITE_SPECIFICITY_V3`  
**Status:** outcome-informed simulation follow-up; this contract is frozen before V3 outcomes are computed. V1/V2 and other M2 results were already inspected. This is not a confirmatory preregistration, new biological evidence, or evidence of general AI benefit.

## Question

In the published Ji et al. Figure 7 circuit model, does feedback delivered to the sensory-processing variable `a` produce a stronger warm-directed behavior than motor-only persistence feedback after calibrating the motor-only arm to match mean forward-run duration separately at several sensory-noise scales?

## Mechanistic scope

The source model's `sensory_site_feedback` term is applied to `a`; `motor_only_feedback` is applied to `m`. These are model interventions. The comparison does not claim that the biological RIM-to-AIY connection is the unique carrier, and it does not estimate animal-level uncertainty.

## Model and arms

Use the archived Figure 7 source archive and the same Python implementation/equations, time step, trajectory horizon, agent count, smoothing, thermal gradient, and transition dynamics as V2. Use common random numbers across arms within each seed block.

Noise multipliers are `{0.75, 1.00, 1.25}` applied to the source model's sensory-noise term. At each multiplier:

1. `SENSORY_SITE_FB`: sensory feedback coefficient 1.0, motor feedback 0.
2. `MOTOR_ONLY_MATCHED`: sensory feedback 0, motor feedback chosen from `{0.60, 0.605, …, 0.85}` using development blocks only to minimize absolute difference in mean forward-run duration from `SENSORY_SITE_FB`; ties choose the smaller coefficient.
3. `NO_FEEDBACK`: both coefficients 0.

The control is matched on **mean forward-run duration only**. Run-duration distribution, forward occupancy, run count, switching latency and internal state are measured but not tuned. This prevents a mean match from being presented as a full dynamical match.

## Samples and independent unit

- Development seed blocks: `310000–310039` inclusive.
- Held-out test seed blocks: `311000–311199` inclusive.
- Each seed block contains 50 agents and 1,500 time steps.
- Independent analysis unit: simulation seed block. Agents are clustered within block; time points and individual runs are not treated as independent replicates.
- Seed namespaces do not overlap V1/V2. All arms and noise conditions within a block share the same base random arrays.

## Outcomes

- **Primary:** paired difference `SENSORY_SITE_FB − MOTOR_ONLY_MATCHED` in the warm-direction index, averaged equally over the three noise multipliers within each test seed block. Positive favors sensory-site feedback. Report the mean and 95% paired percentile-bootstrap CI over 20,000 seed-block resamples (bootstrap seed `20261003`).
- **Secondary:** same contrast separately at each noise multiplier; mean, median, 90th percentile and ≥30-second fraction of forward-run duration; forward occupancy; forward-run count; final warm displacement; sensory-site minus motor-only mean run duration.
- No secondary measure may replace the primary outcome.

## Interpretation

This study estimates robustness of a source-model counterfactual across three imposed noise levels. A positive result supports a difference between feedback placements in this model after matching one persistence summary. It does not establish a universal feedback-site advantage, a real-worm effect size, a unique biological synaptic mechanism, or transfer to AI systems. A null or reversed contrast is retained as an adverse result. Because V1/V2 outputs were already inspected, all V3 conclusions remain exploratory and outcome-informed.

## Reproducibility

The runner records source archive, contract and script SHA-256 digests, environment versions, selected development coefficients, output hashes, row counts and the bootstrap seed. The run is single-pass; no parameter retuning follows the held-out outcomes.
