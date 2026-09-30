# M2 feedback-site specificity V4 — multi-statistic persistence calibration

**Experiment ID:** `M2_FEEDBACK_SITE_SPECIFICITY_V4`
**Classification:** retrospective, outcome-informed source-model stress test. M2 V1–V3 and the V3 held-out outcomes were already inspected before this follow-up. It is not a confirmatory test, new biological evidence, or an AI-transfer result.

## Question

Does the V3 sensory-site feedback advantage over motor-only feedback persist when the motor-only coefficient is selected using several forward-run persistence summaries instead of mean run duration alone?

## Model and calibration

Use the same Python implementation of the published Ji et al. Figure 7 source model, condition equations, common-random-number construction, trajectory horizon, number of agents, and metrics as V3. Reuse only V3's **development** table (seed blocks 310000–310039); no V3 test rows are used to select V4 coefficients.

For each noise multiplier (0.75, 1.00, 1.25), choose a motor-only feedback coefficient from the V3 development grid 0.600–0.850 in 0.005 increments. The calibration target is the sensory-site arm's development-set mean of four summaries: mean forward-run duration, median duration, 90th percentile duration, and fraction of runs at least 30 seconds. Standardize each discrepancy by the across-grid standard deviation of that summary's motor-only development means, then minimize the unweighted sum of squared standardized discrepancies. Ties select the smaller coefficient. The warm-direction index is excluded from calibration.

This is a four-summary calibration, **not** a match of the full run-duration distribution, forward occupancy, switching latency, or latent state.

## Arms and held-out evaluation

At each noise multiplier compare:

1. `SENSORY_SITE_FB`: sensory feedback coefficient 1.0, motor feedback 0.
2. `MOTOR_MULTI_STAT_MATCHED`: sensory feedback 0, motor feedback set by the development-only rule above.
3. `NO_FEEDBACK`: both feedback coefficients 0.

Held-out simulation seed blocks are 320000–320199 inclusive, disjoint from V3 development and test blocks. Each contains 50 agents and 1,500 time steps. Seed block is the analysis unit; agents, forward runs, and time points are clustered within block.

## Outcomes and decision

- **Primary:** within-block sensory-site minus multi-statistic-matched motor-only warm-direction index, averaged equally across the three noise multipliers. Report the mean, 95% paired percentile-bootstrap interval over 20,000 seed-block resamples (seed 20261004), and number of positive blocks.
- **Secondary:** same contrast by noise multiplier; held-out differences in the four calibration summaries; forward occupancy, number of forward runs, final warm displacement, and the no-feedback arm.
- The primary decision is descriptive: positive, negative, or interval includes zero. No new threshold or success claim is inferred from this retrospective run.
- No calibration changes are allowed after inspecting the V4 held-out output.

## Interpretation limits

A positive primary contrast after this stronger summary calibration would narrow—but not remove—the run-duration-distribution confound. A non-positive contrast would show that the V3 placement contrast is sensitive to its comparator construction. Either outcome concerns only this source-model implementation and these imposed noise scales. It does not identify a unique biological synapse, estimate an animal-level effect, or demonstrate benefit in an artificial system.

## Provenance

The runner records the V3 development input hash, V3 source runner hash, V3 source archive hash, this contract hash, selected coefficients, seed ranges, runtime versions, output hashes, and row counts. The V4 evaluator is executed once on its fixed seed range.
