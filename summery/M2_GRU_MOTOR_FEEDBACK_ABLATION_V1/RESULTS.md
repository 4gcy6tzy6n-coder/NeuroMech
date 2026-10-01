# M2 GRU motor-feedback ablation V1 — results

## Result

This exploratory attribution experiment followed the prior result in which GRU-8 performed best among the tested M2 controllers. It compared the same GRU architecture and parameter count with current own motor-state input, a zeroed second input channel, or another episode's motor signal. In the predeclared `SLOW_TRANSIENT` condition, the primary contrast `GRU_SELF_MOTOR − GRU_ZERO_MOTOR` was **−0.006239 movement MSE** (95% seed-block bootstrap interval **[−0.007273, −0.005197]**, 32 paired training-seed blocks). Negative values favor own motor feedback, so the explicit motor signal improved this GRU's held-out performance in that condition.

The secondary contrast `GRU_SELF_MOTOR − GRU_YOKED_MOTOR` was **−0.006822** (95% interval **[−0.007770, −0.005886]**). The yoke preserved the instantaneous population distribution of motor signals while changing which episode received each signal; all 128 condition × seed-block yoke checks passed. These contrasts show a local contribution of self-contingent motor feedback to this trained controller under slow transient sensor conflict, not that the circuit or a unique biological feedback pathway has been reproduced.

Mean movement MSE by condition:

| Condition | Self motor input | Zero motor input | Yoked motor input |
|---|---:|---:|---:|
| SLOW_TRANSIENT | 0.304671 | 0.310911 | 0.311493 |
| FAST_TRANSIENT | 0.520107 | 0.521739 | 0.520973 |
| SLOW_CLEAN | 0.111172 | 0.111526 | 0.110977 |
| FAST_CLEAN | 0.366772 | 0.366529 | 0.364709 |

Condition values outside the primary are descriptive. The direction and size of the gap vary by condition; there is no general improvement across all four conditions. All arms used 297 trainable parameters, identical initialization per seed block, 100 optimizer updates, and paired exogenous data streams. This is a fair architectural ablation, but it remains within a task family already examined by the project and was motivated by previously observed GRU performance.

## Interpretation and limits

This result is stronger attribution evidence than comparing different architectures: it indicates that the motor-state channel contributes information to the GRU in the tested slow-transient condition, beyond its recurrent memory and sensory input. The self-versus-yoke contrast is consistent with recipient-specific contingency, although donor reassignment also breaks alignment with each recipient's target and observation trajectory.

The task is synthetic, motor feedback is an explicit simulator variable, and the test reuses the M2 binary tracking/transient-conflict task family. The result neither demonstrates a worm-to-AI transfer nor validates the RIM–AIY causal pathway, establishes animal-level effects, or supports general AI benefit. The effect under clean/fast conditions is small and changes direction; do not claim task-independent benefit.

## Reproducibility

- 32 fresh training-seed blocks, 3 arms, 4 conditions, 128 held-out episodes per block × arm × condition.
- 96 fits, 49,152 episode rows, and 384 seed-summary rows.
- The independent verifier recomputed seed summaries and both seed-level contrasts; checked row coverage, equal parameter/update counts, metric validity, exact yoke distribution matching, and source/output hashes. Verification passed.
- A second complete run reproduced held-out episodes, seed summaries, summary JSON, yoke checks, and all fit fields except wall-clock training time byte-for-byte; details are in `data/results/M2_GRU_MOTOR_FEEDBACK_ABLATION_V1/canonical/RERUN_VERIFICATION.json`.
- Attempt 1 aborted before outcome writing because the yoke signal was float64 while GRU weights were float32. The input conversion was corrected and documented; the corrected run is canonical.
