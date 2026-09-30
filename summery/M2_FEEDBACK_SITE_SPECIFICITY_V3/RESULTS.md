# M2 feedback-site specificity robustness V3 — results

**Classification:** completed outcome-informed source-model simulation. V1/V2 outcomes were already known when V3 was designed. This is not a confirmatory biological experiment, not new evidence from worms, and not an AI-transfer result.

## Question and design

V3 compared feedback delivered to the sensory-processing variable (`SENSORY_SITE_FB`) with motor-only persistence feedback calibrated on development seed blocks to match mean forward-run duration. The comparison was repeated at sensory-noise multipliers 0.75, 1.00, and 1.25. Calibration selected motor-only coefficients 0.790, 0.720, and 0.655, respectively. Evaluation used 200 new test seed blocks per noise level, 50 simulated agents per block, and the source-model 1,500-step trajectory. The seed block—not agent, run, or time point—was the analysis unit.

## Primary result

The primary contrast was sensory-site minus motor-only warm-direction index, averaged equally across the three noise levels within each test seed block. The mean contrast was **+0.08057** (paired seed-block bootstrap 95% CI **[+0.07752, +0.08357]**); it was positive in **200/200** blocks.

| Noise multiplier | Sensory-site index | Motor-only index | Paired difference (95% CI) | Positive blocks |
|---:|---:|---:|---:|---:|
| 0.75 | 0.7516 | 0.6713 | +0.08030 [+0.07410, +0.08654] | 192/200 |
| 1.00 | 0.5686 | 0.4781 | +0.09056 [+0.08585, +0.09544] | 199/200 |
| 1.25 | 0.4398 | 0.3690 | +0.07084 [+0.06714, +0.07456] | 198/200 |

The mean forward-run duration was close between the arms in held-out blocks: sensory-site minus motor-only was −0.035 s at multiplier 0.75 (95% CI [−0.271, +0.201]), +0.018 s at 1.00 ([-0.032, +0.067]), and −0.037 s at 1.25 ([-0.059, −0.015]). The V3 control was calibrated only on the development-set **mean**; the small held-out duration difference at 1.25 does not alter the direction-index estimate.

## Interpretation

Within this Python implementation of the authors' navigation model, the placement of feedback at the sensory-processing variable retained a warm-direction-index advantage over motor-only feedback across the three imposed noise scales, after mean forward-run duration had been calibrated separately. This is stronger evidence for a **model-specific feedback-placement distinction** than a simple comparison against no feedback.

The comparison did not match the full forward-run distribution or occupancy. At the source noise scale, for example, median run duration was 1.46 s for sensory-site feedback and 2.26 s for motor-only feedback; the 90th percentiles were 12.12 s and 10.77 s. Thus the outcome could still reflect differences in run-duration distribution, switching dynamics, or other internal trajectories. The noise multipliers are simulation manipulations, not measured biological boundary conditions.

The result is consistent with—but does not independently validate—the paper's biological account that motor-state feedback shapes sensory representation. It does not identify a unique synaptic carrier, provide animal-level inference, establish a general AI advantage, or justify merging biological and artificial systems.

## Reproducibility and verification

- Held-out table: [`heldout_simulation_metrics.csv`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3/heldout_simulation_metrics.csv)
- Development calibration: [`development_calibration.csv`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3/development_calibration.csv)
- Machine summary and run manifest: [`summary.json`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3/summary.json), [`run_manifest.json`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3/run_manifest.json)
- Independent recomputation: [`POSTRUN_VERIFICATION.json`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3/POSTRUN_VERIFICATION.json); verifier status `PASS` for all 1,800 held-out seed × noise × arm keys, the primary estimate and interval, and recorded hashes.
- Runner: [`run_experiment.py`](../../model/M2_FEEDBACK_SITE_SPECIFICITY_V3/run_experiment.py)
- Contract: [`CONTRACT.md`](CONTRACT.md)

## Decision

`SOURCE_MODEL_FEEDBACK_PLACEMENT_EFFECT_REPRODUCED_ACROSS_TESTED_NOISE_SCALES; EXPLORATORY_ONLY`. The finding advances the M2 feedback-site hypothesis in the source model, but does not establish biological causality or AI transfer. Preserve the distributional mismatch and implementation-parity limitations in any manuscript account.
