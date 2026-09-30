# M2 source-model gradient-reversal boundary — results

**Classification:** exploratory source-derived computational stress test; not a biological experiment or AI-transfer validation.

## Main observations

At the 20-second gradient-reversal interval, the source-model sensory-feedback arm had an environment-aligned displacement rate of `0.08514`, compared with `0.01135` in the no-feedback ablation. The paired difference was `+0.07379` (95% seed-block bootstrap interval `[+0.07061,+0.07694]`), positive in 100/100 simulated seed blocks. Sensory-feedback rates remained positive across all tested schedules and declined as reversals became more frequent, from `0.11016` at 40 seconds to `0.01713` at 5 seconds. The no-feedback arm also moved in the preferred direction on average but had lower progress in each tested schedule.

| Reversal interval | Sensory-site feedback progress rate | Output-site feedback progress rate | No-feedback progress rate | Sensory-site forward occupancy | Output-site forward occupancy |
|---:|---:|---:|---:|---:|---:|
| Stable | 0.10692 | 0.00420 | 0.02790 | 17.12% | 100.00% |
| 40 s | 0.11016 | 0.00084 | 0.01932 | 16.15% | 100.00% |
| 20 s | 0.08514 | −0.000003 | 0.01135 | 15.13% | 100.00% |
| 10 s | 0.05084 | −0.000003 | 0.00754 | 13.70% | 100.00% |
| 5 s | 0.01713 | 0.00005 | 0.00679 | 12.42% | 100.00% |

The nominal primary sensory-minus-output contrast at 20 seconds was `+0.08515` (95% interval `[+0.08208,+0.08818]`; 100/100 blocks positive), but **this is not interpretable as a feedback-site effect**: putting the same coefficient directly into the motor-state equation saturated that arm at 100% forward occupancy and 200-second runs. The control was not calibrated to match the sensory arm's dynamics, and the contract explicitly does not claim it was. Its failure is a central result and motivates a feedback-contingency control rather than treating the contrast as evidence for sensory-site specificity.

## Interpretation

Within the translated source model, the sensory-site feedback term improved simulated gradient-aligned progress relative to deleting that term, including in the preselected 20-second reversal condition. Its progress diminished under faster sign reversals. This is an operating-boundary result for one published model implementation; it is not an animal-level effect estimate. The output-site condition shows that transferring the same coefficient between nonlinear state equations is not a valid strength-matched intervention by itself.

The next discriminating computational comparison should preserve the feedback signal's marginal time course while breaking its within-agent contingency (a within-condition cross-agent yoke). That can test whether self-specific motor feedback matters beyond generic positive drive. The present experiment does not answer this.

## Reproduction and limits

The independent 100-seed rerun reproduced `seed_block_metrics.csv` byte-for-byte and independently recomputed the same primary contrast. The verifier passed all 1,500 seed-interval-arm keys, manifest input/output hashes, and the bootstrap result. Seed blocks, not the 50 agents or time steps inside a block, are the uncertainty units.

The two-panel visualization is archived as [PDF](../../data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/canonical/Figure_M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1.pdf), [SVG](../../data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/canonical/Figure_M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1.svg), and [600-dpi TIFF](../../data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/canonical/Figure_M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1.tiff), with [figure source data](../../data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/canonical/figure_source_data.csv) and a [legend](FIGURE_LEGEND.md). Rendered panel alignment, text size, and collision checks passed.

The reversal schedule, position-slope signal, and simulated noise are imposed model conditions, not measurements of worm ecology. This is an exploratory reanalysis of a known source model, with no learned artificial controller or generic AI baseline. It neither validates the circuit biologically nor establishes that this computation improves AI.
