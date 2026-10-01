# M2 continuous tracking motor-state transfer V1 — results

## Primary result

This fresh task-family transfer test compared equal 378-parameter GRUs receiving realized motor state, no motor signal, previous command, or a distribution-matched motor-state yoke. In the predeclared `LONG_MISSING_BURSTS` profile, the primary contrast `GRU_SELF_MOTOR − GRU_ACTION_COPY` was **+0.009096 tracking MSE** (95% seed-block bootstrap interval **[+0.001446,+0.016816]**, 32 paired model-training blocks). Positive values mean realized motor-state feedback performed worse than the model's previous command input.

The secondary self-minus-zero contrast was `+0.020579` (95% interval `[+0.007303,+0.034529]`), and self-minus-yoke was `+0.014082` (`[+0.000423,+0.027845]`), also adverse to the self-motor arm. Condition means were:

| Profile | Self motor | Zero motor | Previous command | Yoked motor |
|---|---:|---:|---:|---:|
| TRAIN_LIKE | 0.892526 | 0.871519 | 0.882947 | 0.878523 |
| LONG_MISSING_BURSTS | 1.668827 | 1.648249 | 1.659732 | 1.654745 |
| LOW_MISSING | 0.514928 | 0.505435 | 0.516451 | 0.507557 |
| FAST_TARGET | 0.430023 | 0.420819 | 0.428327 | 0.421499 |

These are synthetic controller outcomes. The result contradicts generalizing the prior M2 motor-input benefit to this continuous 2D setting; it does not refute the biological RIM–AIY findings.

## Task-adequacy diagnostic and limitation

After the canonical run, a fixed reactive controller and a privileged task-state controller were evaluated on the same test streams. The reactive rule (`command = clipped current relative-position observation`, zero command during missing observations) had lower MSE than every trained GRU arm in every profile: `1.423654` in `LONG_MISSING_BURSTS` versus `1.648249–1.668827` for the GRUs. A controller given the exact target-relative position and target velocity achieved `0.013945`; this is a deliberately privileged upper bound, not a fair model arm.

These diagnostics were not preregistered and do not enter the primary contrast. They reveal that the learned GRUs were not competitive with a simple task-native controller under the chosen training schedule. This substantially limits interpretation: the experiment shows an adverse input-ablation contrast among these fitted GRUs, but it does not establish that the feedback abstraction itself is generally harmful or that this is an adequate AI benchmark. The post-run diagnostic is recorded at `data/results/M2_CONTINUOUS_TRACKING_MOTOR_STATE_TRANSFER_V1/POSTRUN_TASK_VIABILITY_ORACLE.json`.

## Biological interpretation boundary

The source evidence concerns locomotor-state representation in AIY at cell-class granularity. This artificial task supplies a continuous two-dimensional actuator-velocity vector. That representation choice is not directly licensed by the biological evidence. Poor performance may reflect that mismatch, optimization/training weakness, or both; this run does not distinguish those explanations. A follow-up should use an independently justified state variable, validation-based model selection, and a strong task-native controller from the outset. Do not tune this canonical run or reinterpret its adverse direction as evidence against the biology.

## Reproducibility

- 32 fresh training-seed blocks; 4 arms; 4 profiles; 128 held-out episodes per block × arm × profile.
- 128 fitted models, 65,536 episode rows, and 512 seed-summary rows.
- Independent verification passed: row/profile/arm coverage, equal parameter and update counts, metric validity, recomputed seed summaries and contrasts, exact per-time/per-coordinate yoke-distribution checks, and source/output hashes.
- A complete independent rerun reproduced the episode, seed-summary, yoke-check, and summary files byte-for-byte; learned parameters and fit records matched apart from wall-clock training time.
