# M2 marginal-persistence yoke V1 — results

**Classification:** retrospective, outcome-informed source-model analysis. M2/V3/V4/V5 results were known before this follow-up. This is not biological validation or AI transfer.

## Primary result

The equal-weighted sensory-site minus marginal-persistence-yoke warm-direction-index difference over the three noise scales was **+0.45489** (95% seed-block bootstrap interval **[+0.44770, +0.46211]**; **200/200** blocks positive). The scalar motor-only comparator difference was **+0.13997** (95% interval `[+0.13637, +0.14352]`; 200/200 positive).

The yoke's warm-direction index was near zero, as expected for bout durations resampled independently of position and heading. This is not by itself evidence for a sensory feedback site: the yoke also failed to reproduce persistence adequately at the lowest noise scale.

| Noise | Sensory minus yoke direction (95% interval) | Mean forward-bout difference | Median difference | P90 difference | ≥30 s fraction difference | Occupancy difference |
|---:|---:|---:|---:|---:|---:|---:|
| 0.75 | +0.60171 [+0.58498, +0.61838] | +0.6092 s | −0.0347 s | +2.6229 s | +0.00878 | −0.01495 |
| 1.00 | +0.43100 [+0.42236, +0.43961] | +0.0575 s | −0.0097 s | +0.1672 s | +0.00099 | −0.00916 |
| 1.25 | +0.33197 [+0.32579, +0.33809] | +0.0600 s | +0.0383 s | +0.1295 s | +0.00025 | −0.00422 |

Differences are sensory-site minus yoke. The four reported forward-bout summaries and occupancy are close at noise scales 1.00 and 1.25, but V1 defined no equivalence bounds, so none is declared “matched.” At 0.75, several summaries differ materially; in particular, mean forward duration differs by `0.609 s` and the ≥30-second fraction by `0.00878`.

## Interpretation

V1 does not support a clean across-scale test of whether marginal persistence alone is sufficient because the held-out yoke mismatch is substantial at noise 0.75 and no adequacy threshold was specified. At the two higher noise scales, directional differences remain while several marginal duration summaries are close, but those exploratory per-scale comparisons are not multiplicity-adjusted and do not establish equivalence. The yoke deliberately removes all dependence of bout duration on current position, heading and temperature; it cannot determine which omitted coupling explains the difference.

The next comparison should preserve complete development motor-state trajectories (including censored boundaries and within-trajectory serial structure) as a yoke, then verify held-out persistence similarity before interpreting the warm-direction contrast. This repair follows the observed V1 mismatch and is outcome-informed.

## Implementation incident

The first V1 execution completed its simulations but stopped during CSV serialization because yoke-only reverse-bout fields were not present in the source-model rows. No held-out file or summary was written from that attempt. The serializer was corrected to emit the union of arm fields, and the fixed-seed run then completed. The correction affected output schema only, not simulation or estimands. The incident log is retained in [`FAILURE_LOG.md`](FAILURE_LOG.md).

## Verification

Independent verification passed for 120 development seed/noise records, outcome-blind development table columns, nonempty uncensored bout libraries, V5 coefficient provenance, source/contract/runner/output hashes, 2,400 complete held-out rows, persistence contrasts, and bootstrap statistics. See [`POSTRUN_VERIFICATION.json`](../../data/results/M2_PERSISTENCE_YOKED_DIRECTION_V1/POSTRUN_VERIFICATION.json).

**Disposition:** `YOKE_MATCH_INADEQUATE_AT_NOISE_0_75; HIGHER_NOISE_CONTRASTS_EXPLORATORY`.
