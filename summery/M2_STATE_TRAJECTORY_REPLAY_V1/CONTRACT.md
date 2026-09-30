# M2 full motor-state trajectory replay V1

**Experiment ID:** `M2_STATE_TRAJECTORY_REPLAY_V1`
**Classification:** retrospective, outcome-informed source-model follow-up after V1 marginal-duration yoke mismatch. This is not confirmatory, biological validation, or AI-transfer evidence.

## Question

Can a motor-state sequence replayed from an independent development simulation reproduce the corrected sensory-feedback model's warm-direction behavior when the replayed sequence preserves the full 200-second forward/reverse timing pattern but is independent of the held-out trajectory's position and heading?

This is a stronger control than bout resampling: it preserves serial structure, within-trajectory duration dependence, and start/end censoring from development sequences. It does not reproduce test-specific sensory/thermal coupling.

## Arms

1. `SENSORY_SITE_FB`: corrected V5 Figure 7 translation, sensory feedback coefficient 1.0, motor feedback 0.
2. `MOTOR_MULTI_STAT_MATCHED`: corrected source model with the V5 development-selected motor-only coefficients `{0.75: 0.760, 1.00: 0.665, 1.25: 0.610}`.
3. `FULL_TRAJECTORY_REPLAY`: for each noise scale, draw a complete 1,500-step forward/reverse mode sequence from an independent development sensory-site simulation and apply it to held-out heading streams. Replay choice is independent of held-out position, heading, and warm-direction outcomes.
4. `NO_FEEDBACK`: corrected source model with both feedback coefficients zero.

The yoke library is defined only from binary motor-mode sequences. Direction index, position, and warm displacement are not used to select or match sequences.

## Samples and unit

- Development seed blocks: `370000–370039`, separately simulated at each noise scale `{0.75, 1.00, 1.25}`.
- Held-out seed blocks: `380000–380199`.
- 50 agents per block, 1,500 steps over 200 seconds.
- Analysis unit: seed block; agents/timesteps are clustered.
- Heading initialization/reset streams are shared between source-model and replay arms within held-out seed; replay trajectory selection has a separate deterministic RNG stream.

## Outcomes

- **Primary:** equal-weighted within-seed `SENSORY_SITE_FB − FULL_TRAJECTORY_REPLAY` warm-direction index across noise scales; mean, 95% paired percentile-bootstrap interval over 20,000 seed-block resamples (seed `20261007`), and positive-block count.
- **Control adequacy:** held-out differences in forward duration mean, median, P90, ≥30-second fraction, forward occupancy, run count, plus corresponding reverse-mode duration summaries. Report them before interpreting the primary contrast. No equivalence criterion was frozen; report descriptive mismatch without declaring equivalence.
- **Secondary:** sensory-site minus scalar motor-only direction contrast and held-out forward/reverse summaries.

## Interpretation limits

If the full-trajectory replay matches held-out motor-state summaries and still lacks warm-direction behavior, this supports a role for coupling between the motor-state trajectory and sensory/environmental context in this source model. It does not show that sensory-site feedback is the unique explanation, prove a biological synapse, or generalize to animals/AI. If replay fails persistence adequacy, the comparison remains inconclusive. Prior results were known, so all findings are exploratory.

## Provenance

Pin the corrected source model, author MATLAB file, this contract, V5 coefficient source, packed development mode sequences, seeds, runtime, output hashes, and verification. Do not edit V1/V5 historical outputs.
