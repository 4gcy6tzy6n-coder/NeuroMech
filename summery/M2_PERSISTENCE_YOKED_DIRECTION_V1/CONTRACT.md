# M2 marginal-persistence yoke V1

**Experiment ID:** `M2_PERSISTENCE_YOKED_DIRECTION_V1`
**Classification:** retrospective, outcome-informed source-model analysis. M2/V3/V4/V5 results were known before this follow-up. This is not confirmatory, biological validation, or AI-transfer evidence.

## Question

Can a motor program that reproduces the corrected sensory-feedback model's marginal forward and reverse bout-duration distributions, while choosing bout durations independently of position and heading, reproduce its warm-direction behavior?

This tests whether the marginal persistence distribution alone is sufficient in this model. It does not test every possible motor-only controller and does not establish feedback-site specificity.

## Arms

1. `SENSORY_SITE_FB`: corrected V5 Figure 7 translation; sensory-site feedback coefficient 1.0, motor feedback 0.
2. `MOTOR_MULTI_STAT_MATCHED`: corrected translation with no sensory-site feedback and V5's development-selected scalar motor-only coefficients `{0.75: 0.760, 1.00: 0.665, 1.25: 0.610}`.
3. `MARGINAL_PERSISTENCE_YOKE`: for each noise scale, independently sample alternating forward and reverse bout durations from a separate development set of corrected sensory-site simulations. Duration draws do not depend on current heading, temperature, position, or the warm-direction outcome. Use the source model's heading-transition rules and shared initial/reset heading random streams.
4. `NO_FEEDBACK`: corrected translation with both feedback coefficients zero.

The yoke is an intentionally optimistic comparator: it is trained on the sensory-site arm's marginal bout durations. Development extracts durations only for yoke construction; direction metrics are not used to define the yoke.

## Samples and unit

- Development seed blocks: `350000–350039`, each used to extract duration samples separately at noise scales `{0.75, 1.00, 1.25}`. Runs clipped by the start or end of the 200-second record are excluded from the resampling libraries as censored intervals.
- Held-out seed blocks: `360000–360199`.
- 50 agents per block; 1,500 steps over 200 seconds.
- Analysis unit: simulation seed block; agents and timesteps are clustered.
- Random heading initialization/resets are coupled across the source-model and yoke arms within a held-out seed. Yoke bout resampling uses a separate deterministic RNG stream.

## Outcomes

- **Primary:** equal-weighted within-seed `SENSORY_SITE_FB − MARGINAL_PERSISTENCE_YOKE` warm-direction index across noise scales. Report the mean, 95% paired percentile-bootstrap interval (20,000 seed-block resamples; seed `20261006`), and positive-block count.
- **Secondary:** sensory-site minus yoke contrasts in forward-bout mean, median, P90, ≥30-second fraction, occupancy, run count, and final warm displacement; sensory-site versus scalar-control contrasts are also reported.
- No endpoint is changed after outcomes are generated.

## Interpretation limits

If the yoke matches held-out duration summaries but fails to match warm direction, that shows marginal persistence alone is insufficient in this source model; directionally contingent coupling or other dynamics are required. It does not isolate a biological synapse or prove that a sensory-site feedback mechanism is the only explanation. If duration matching fails, the yoke comparison is inconclusive for this question. All conclusions are restricted to this model and imposed noise conditions.

## Provenance

Pin the V5 corrected source model, this contract, the author MATLAB script, V5 motor coefficients, development bout samples, random seeds, runtime, output hashes, and verifier output. Historical V3/V4/V5 files remain unchanged.
