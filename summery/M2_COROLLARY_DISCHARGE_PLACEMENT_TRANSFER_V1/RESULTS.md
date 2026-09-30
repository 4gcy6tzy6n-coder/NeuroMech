# M2 corollary-discharge placement transfer V1 — results

**Classification:** post-result exploratory artificial mechanism-transfer study; not biological validation or independent confirmation.

## Primary result

At the training-range hazard `h=0.05`, the sensory-site feedback model reached **88.94%** accuracy, versus **82.14%** for the equal-parameter output-persistence model. The paired contrast `SENSORY_SITE_CD − OUTPUT_SITE_PERSISTENCE` was **+6.80 percentage points** (crossed-bootstrap 95% CI **[+6.48, +7.12]**); all 30 training-seed means were positive.

## Critical comparator results

The positive placement contrast does not mean that sensory feedback improved overall performance over the other controls. At `h=0.05`, no-feedback accuracy was **89.05%** (sensory-site minus no-feedback `−0.12` percentage points; descriptive crossed 95% interval `[−0.16, −0.07]`), the two-unit generic RNN was **90.21%** (`−1.28` points relative to sensory-site), and the Bayes filter was **90.30%** (`−1.37` points). The direct sensory-site arm therefore did not beat the no-feedback or stronger generic/task-aware references.

| State-switch hazard | Sensory-site feedback | Output persistence | No feedback | Generic 2-unit RNN | Bayes filter |
|---:|---:|---:|---:|---:|---:|
| 0.01 | 93.25% | 94.63% | 91.74% | 94.90% | 96.52% |
| 0.05 | 88.94% | 82.14% | 89.05% | 90.21% | 90.30% |
| 0.20 | 78.39% | 63.89% | 81.55% | 79.23% | 82.19% |

The sensory-site model's mean switch-recovery lag was 1.30 steps at `h=0.05`, compared with 3.56 for output persistence. Its false action-switch rate was 7.30%, compared with 3.36% for output persistence and 11.63% for no feedback. At `h=0.01`, output persistence had the higher accuracy and much lower false-switch rate, but recovered more slowly after true changes. At `h=0.20`, sensory-site feedback substantially outperformed output persistence, but still lost to no feedback and Bayes.

## Interpretation

In this synthetic telegraph-state task, the location of a previous-action signal changed the stability–switching tradeoff. Feeding the signal into the sensory-state update avoided some of the long recovery lag produced by output inertia. This is a mechanistic placement effect relative to one matched yoke, not an overall performance advantage: the no-feedback, generic RNN, and Bayes references were at least as accurate in the primary condition.

The task is an abstraction, not a reconstruction of *C. elegans* thermotaxis or the Ji et al. circuit model. The experiment does not show that biological AIY feedback implements these equations, that the observed synthetic hazard relation exists in the worm, or that the mechanism is a general AI principle.

## Reproducibility

- [Contract](CONTRACT.md)
- [Runner, analyzer, and independent verifier](../../model/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/)
- [Canonical episode outcomes and manifest](../../data/results/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/canonical/)
- The independent verifier checks all 230,400 episode-policy-hazard keys, output/source hashes, and the primary crossed-bootstrap interval.
- A separate 30-seed rerun reproduced episode outcomes byte-for-byte; all non-timing training fields also matched exactly. `training_seconds` differed, as expected for an environment-dependent runtime measure.
