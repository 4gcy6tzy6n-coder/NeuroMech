# M2 2D closed-loop pursuit V2 — training-distribution diagnostic

**Experiment ID:** `M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC`
**Classification:** post-result exploratory diagnostic. It was designed after inspecting V1 and is not an independent confirmatory experiment or biological validation.

## Primary result

The primary statistic was `G_teacher_mixed − G_random`, where `G = final_distance(BILINEAR_RNN_MATCHED) − final_distance(MODE_GAIN)` under the aligned mapping. Positive `G` favors MODE_GAIN.

| Shared training distribution | MODE_GAIN | Bilinear matched | `G` (bilinear − mode) |
|---|---:|---:|---:|
| Random action | 0.10935 | 0.09050 | −0.01885 (95% CI [−0.02791, −0.01059]) |
| Teacher-mixed closed loop | 0.08989 | 0.09383 | +0.00394 (95% CI [+0.00051, +0.00750]) |

The paired crossed-bootstrap interaction was **+0.02279** (95% CI **[+0.01341, +0.03318]**); the seed-level interaction was positive in 26/30 training seeds. Thus the deployment-like training distribution shifted the MODE_GAIN-versus-bilinear comparison by a measurable amount in this task, reversing the mean final-distance ranking. The random-action regime reproduces the direction of V1's bilinear disadvantage for MODE_GAIN.

## Other aligned outcomes

| Arm | Random-action final distance / success | Teacher-mixed final distance / success |
|---|---:|---:|
| MODE_GAIN | 0.10935 / 85.2% | 0.08989 / 92.3% |
| NO_CONTEXT | 0.10400 / 86.8% | 0.08845 / 94.3% |
| ADDITIVE_RNN_MATCHED | 0.09558 / 88.7% | 0.08664 / 94.7% |
| BILINEAR_RNN_MATCHED | 0.09050 / 91.2% | 0.09383 / 89.2% |
| KALMAN_ORACLE | 0.08669 / 91.5% | 0.08669 / 91.5% |

The interaction is not evidence that MODE_GAIN is generally best. Under teacher-mixed training it remained slightly worse than the no-context ablation in final distance (difference `no-context − mode = −0.00144`, 95% CI [−0.00442, +0.00164]) and success (92.3% vs 94.3%). The additive matched model had the lowest final distance (0.08664) and highest learned-model success (94.7%). The teacher-mixed data improved MODE_GAIN's mean final distance by 0.01947 relative to the random-action regime, but also changed the comparator outcomes; the interaction reflects the joint difference between regimes, not a uniquely isolated benefit of the biological abstraction.

## Mapping-shift outcomes

Under the reversed mapping, MODE_GAIN improved from 0.41448 final distance and 28.5% success with random-action training to 0.17805 and 65.5% after teacher-mixed training. It remained worse than NO_CONTEXT (0.08752; 95.4% success) and ADDITIVE_RNN_MATCHED (0.08712; 95.0%) in that condition. This retains a substantial context-mismatch liability; the teacher-mixed training did not make the state-conditioned update robust to reversal.

## Interpretation

The result supports a bounded explanation: training trajectory distribution can materially alter the ranking of two learned estimators in this closed-loop task, so V1's random-action training condition was not a neutral proxy for deployment. It is consistent with distribution mismatch contributing to V1's MODE_GAIN-versus-bilinear result. It does **not** prove that this was the sole cause: the teacher is a task-aware Kalman policy, its trajectories need not match any learned model's own occupancy, and learning dynamics and policy geometry remain entangled.

The mechanism-shaped update did not outperform every matched alternative, and the task's state/sensor mapping is artificial. These runs provide no biological validation, no general AI claim, and no evidence that the worm circuit implements this exact estimator.

## Reproducibility

- [Frozen diagnostic contract](CONTRACT.md)
- [Runner, analyzer, and independent verifier](../../model/M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/)
- [Canonical episode and fit records](../../data/results/M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/canonical/)
- Independent verifier passed all 153,600 unique episode-policy-regime keys, 27 recomputed contrasts/intervals, and source/output hashes.
- A full independent rerun reproduced episode rows, fitted parameters/losses, and analyzed summary exactly; wall-clock training-time fields are expected to differ.
