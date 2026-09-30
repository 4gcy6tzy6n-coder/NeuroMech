# M2 feedback-site specificity V5 — corrected source-delay indexing

**Experiment ID:** `M2_FEEDBACK_SITE_SPECIFICITY_V5`
**Classification:** retrospective, outcome-informed source-model stress test. All prior M2/V3/V4 outcomes were known before this follow-up. This is not confirmatory, new biological evidence, or AI-transfer evidence.

## Question

Does the sensory-site versus motor-only warm-direction contrast remain in a corrected Python translation of the published Figure 7 model, after selecting the motor-only coefficient from development data using four forward-run persistence summaries?

## Source-index correction

The author MATLAB script uses `delti=round(.5*N/tmax)` and, before each update at one-based loop index `ti`, selects `XS(max(1,ti-delti),3)`. Since `XS` contains rows `1..ti-1` before the update, the equivalent Python zero-based index at loop counter `t=ti-1` is `max(0,t-delti)`. The V3/V4 Python implementation used `max(0,t-1-delti)`, one sample earlier. V5 uses the source-equivalent index. This correction changes only the delayed-position lookup; all other equations and processing follow the archived V3 translation.

## Development calibration

Use the corrected source model and development seed blocks `330000–330039`. At each imposed sensory-noise multiplier `{0.75, 1.00, 1.25}`, compare the sensory-site arm against motor-only coefficients `{0.600, 0.605, …, 0.850}`. Select the coefficient minimizing the unweighted sum of squared standardized errors over mean, median, 90th-percentile forward-run duration, and fraction of runs at least 30 seconds. Each summary is standardized by its standard deviation across the motor-only coefficient grid. Ties select the smaller coefficient. The warm-direction index is excluded from calibration.

This rule chooses the least-bad scalar coefficient; it does not certify distributional equivalence. Persistence mismatch remains a measured limitation, regardless of the selected coefficient.

## Held-out evaluation

Evaluate three arms at each noise multiplier:

1. `SENSORY_SITE_FB`: sensory feedback coefficient 1.0, motor feedback 0.
2. `MOTOR_MULTI_STAT_MATCHED`: sensory feedback 0, motor feedback selected on development data.
3. `NO_FEEDBACK`: both feedback coefficients 0.

Use held-out seed blocks `340000–340199`, each with 50 agents and 1,500 steps. Seed block is the unit of analysis; agents and timesteps are clustered within block. Common random numbers are shared across arms within a block.

## Outcomes

- **Primary:** equal-weighted within-block sensory-site minus motor-only warm-direction index over the three noise multipliers. Report the mean, 95% paired percentile-bootstrap interval over 20,000 seed-block resamples (seed `20261004`), and positive-block count.
- **Secondary:** per-noise contrasts; mean, median, 90th percentile and ≥30-second fraction of forward-run duration; occupancy, run count and final warm displacement.
- No post hoc endpoint replaces the primary contrast.

## Interpretation limits

This is a source-model sensitivity follow-up, not independent validation. A positive result would show only that the contrast persists under this corrected translation and a scalar motor-only comparator whose persistence match must be checked; it would not establish a unique biological synapse, animal-level effect, or benefit in artificial systems. A non-positive or control-mismatched result is retained without repair.

## Provenance

The runner records the corrected source-model, author MATLAB source, contract and generated development-data hashes, environment versions, calibration choices, seed ranges, output hashes and row counts. The V3/V4 results remain immutable historical artifacts and are not silently replaced by V5.
