# M2_JI2021_FEEDBACK_SITE_CONTROL_V1 — sensory-site feedback vs motor-only persistence

**Status:** post-result exploratory mechanistic counterfactual. The source model's positive-feedback outcome was known from the previous M2_JI2021_FEEDBACK_DYNAMICS run; the new feedback-site comparison and calibration procedure are frozen before this run.

## Question

In the Ji et al. Figure 7 thermotaxis model, does feedback returned to the sensory-processing interneuron produce better warm-gradient migration than a generic motor-only persistence term when the latter is calibrated to match forward-run duration?

This is a computational model comparison. It is motivated by source evidence that the motor-state signal reaches AIY through a RIM-required corollary-discharge pathway, but no unique synaptic carrier or AI benefit is inferred from the comparison.

## Model arms

1. `SENSORY_SITE_FEEDBACK`: exact source-model placement, with `fb=+1` in the A/interneuron equation and no additional motor persistence term.
2. `MOTOR_ONLY_MATCHED`: no motor-to-A feedback (`fb=0`); add one scalar `motor_fb` coefficient multiplying the same saturating motor-state function in the M equation. Select `motor_fb` on 30 development seed blocks from the frozen grid `{0.0,0.1,...,1.0}` to minimize absolute difference from source feedback's mean forward-run duration. Ties choose the smaller coefficient.
3. `NO_FEEDBACK`: `fb=0`, `motor_fb=0`.

All other author-specified parameters, 50 agents per seed block, 1,500 time steps, `noise_scale=1`, and source movement dynamics are unchanged. The independent test uses 100 new seed blocks and common random numbers across the three arms.

## Outcomes and analysis

Primary: held-out `SENSORY_SITE_FEEDBACK − MOTOR_ONLY_MATCHED` difference in the source-defined warm-direction index (`−cos(heading)` weighted over forward-run samples); positive values favor sensory-site feedback. Secondary: mean forward-run duration and final warm-axis displacement, including whether run duration remains approximately matched on held-out seeds. No tune-up is allowed after viewing the held-out results.

The simulation seed block (50 clustered agents) is the independent resampling unit. Use a paired percentile bootstrap with 20,000 resamples. This measures simulator Monte Carlo uncertainty only.

## Limits

- This comparison is post-result and model-based; it cannot confirm a biological causal route.
- Matching only mean forward-run duration does not match the full run-duration distribution, switching latency, parameter count, or energy/compute.
- The added motor-only term is a deliberately generic counterfactual, not a claim about a known biological circuit.
- Even if sensory-site feedback wins, that would show only that feedback placement matters in this source model and task; it would not establish broad AI utility.
