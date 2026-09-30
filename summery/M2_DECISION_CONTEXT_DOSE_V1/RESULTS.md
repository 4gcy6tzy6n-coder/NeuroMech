# M2 context-information dose response on terminal decisions — results

**Classification:** exploratory artificial objective-transfer study. Earlier M2 results and a prior sequential-decision experiment are known. This is not confirmatory evidence or biological validation.

## Main result

Thirty training seeds evaluated three nested training-set sizes (64, 256, 1,024) on 11 context doses, with 256 paired test trials per seed. The primary outcome is terminal choice accuracy; contrast is `MODE_GAIN_FILTER − CONSTANT_GAIN_FILTER`, averaged equally over training sizes.

| κ | Mode-gain accuracy | Constant-gain accuracy | Difference (95% crossed CI) |
|---:|---:|---:|---:|
| −0.50 | 0.5183 | 0.6472 | −0.1289 [−0.1441, −0.1141] |
| 0.00 | 0.6209 | 0.6489 | −0.0280 [−0.0414, −0.0147] |
| +0.10 | 0.6407 | 0.6477 | −0.0071 [−0.0202, +0.0059] |
| +0.20 | 0.6595 | 0.6460 | +0.0135 [+0.0005, +0.0266] |
| +0.50 | 0.7111 | 0.6460 | +0.0651 [+0.0523, +0.0777] |

The linearly interpolated zero crossing was `κ=0.134` (crossed-bootstrap 95% interval `[0.072, 0.200]`; a crossing occurred in all 10,000 bootstrap draws). The first tested dose with a positive interval was `κ=+0.20`. This is lower than the `κ≈0.285` crossover in the continuous-estimation task, so the artificial operating boundary depends on task objective. The two thresholds are a descriptive comparison across distinct task-specific metrics and generators, not a pooled effect.

At `κ=+0.50`, mode gain exceeded the bilinear recurrent comparator by `0.1306` accuracy (seed-bootstrap 95% interval `[0.1201, 0.1410]`), but the task-aware Bayes reference remained ahead by `0.1327`. At `κ=0`, mode gain was below the constant filter and far below Bayes. At the intermediate `κ=+0.20`, pooled advantage was modest; among the separate training sizes, the estimate was clearest for 64 examples and its intervals included zero for 256 and 1,024. Per-size estimates are reported in `canonical/summary.json` and are secondary, unadjusted comparisons.

## Interpretation and limits

The state-conditioned update transfers to terminal decision accuracy when the context/evidence relation is sufficiently aligned, but the threshold differs from the continuous estimator and there is substantial cost under reversed mapping. This is objective-specific transfer within closely related synthetic observation models, not broad task-family generalization. The context-to-evidence mapping and dose parameter are artificial; the data do not measure RIM–AIY signals or establish biological-to-AI transfer. The Bayes reference uses the exact task likelihood, and the experiment cannot claim parity with an optimal decision-maker.

## Reproduction and artifacts

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner, analysis and verifier: [`model/M2_DECISION_CONTEXT_DOSE_V1/`](../../model/M2_DECISION_CONTEXT_DOSE_V1/)
- Trial-level outputs, trained parameters, summary and manifest: [`data/results/M2_DECISION_CONTEXT_DOSE_V1/`](../../data/results/M2_DECISION_CONTEXT_DOSE_V1/)
- Independent verification passed all 1,013,760 unique episode-policy rows and reproduced all 11 primary crossed-bootstrap intervals.
