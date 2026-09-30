# M2 feedback-site specificity robustness V3

Outcome-informed simulation follow-up using the published Ji et al. Figure 7 navigation model.

## Primary result

Sensory-site feedback minus mean-run-duration-calibrated motor-only feedback in warm-direction index, equally averaged across noise multipliers 0.75, 1.00, and 1.25: **+0.08057** (95% paired seed-block bootstrap CI **[+0.07752, +0.08357]**; 200/200 blocks positive).

| Noise multiplier | Difference (95% CI) | Positive blocks | Mean run duration: sensory / motor-only (s) |
|---:|---:|---:|---:|
| 0.75 | +0.08030 [+0.07410, +0.08654] | 192/200 | 9.168 / 9.203 |
| 1.00 | +0.09056 [+0.08585, +0.09544] | 199/200 | 4.564 / 4.546 |
| 1.25 | +0.07084 [+0.06714, +0.07456] | 198/200 | 3.471 / 3.508 |

## Files

- `heldout_simulation_metrics.csv` — 1,800 seed × noise × arm rows.
- `development_calibration.csv` — development-only motor coefficient calibration.
- `summary.json` — machine-readable primary and secondary summaries.
- `run_manifest.json` — versions, seed ranges, source/contract/runner hashes, and output hashes.
- `POSTRUN_VERIFICATION.json` — independent row, estimate, interval, and hash verification.
- `feedback_site_noise_robustness.png` — noise-scale visualization.

## Interpretation limit

This is evidence for feedback-placement specificity inside the implemented source model after matching mean run duration. Full run-duration distributions and internal dynamics remain unmatched. It is not a biological replication, animal-level inference, or general AI-transfer result. See [`experiment interpretation`](../../../summery/M2_FEEDBACK_SITE_SPECIFICITY_V3/RESULTS.md) and the [`limitation log`](../../../summery/M2_FEEDBACK_SITE_SPECIFICITY_V3/FAILURE_LOG.md).
