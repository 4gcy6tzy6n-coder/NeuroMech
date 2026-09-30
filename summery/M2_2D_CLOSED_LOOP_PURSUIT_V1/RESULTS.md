# M2-inspired 2D closed-loop pursuit V1 — results

**Classification:** exploratory artificial sensorimotor experiment informed by prior M2 results. This is not biological validation.

## Primary result

Thirty training seeds were evaluated on 256 shared target/noise episodes under each of two sensor mappings. The primary contrast was `final_distance(BILINEAR_RNN_MATCHED) - final_distance(MODE_GAIN)` in ALIGNED; positive values would favor MODE_GAIN.

| ALIGNED policy | Final distance | Success fraction | Mean distance during control |
|---|---:|---:|---:|
| MODE_GAIN (8 parameters) | 0.1129 | 84.2% | 0.2636 |
| NO_CONTEXT (6 parameters) | 0.1107 | 84.8% | 0.2374 |
| ADDITIVE_RNN_MATCHED (8) | 0.0970 | 88.4% | 0.2429 |
| BILINEAR_RNN_MATCHED (8) | 0.0920 | 90.5% | 0.2350 |
| KALMAN_ORACLE | 0.0857 | 92.1% | 0.1945 |

The matched bilinear baseline had lower distance than MODE_GAIN by `0.02088` (paired crossed-bootstrap 95% interval for `bilinear − mode`: `[-0.03244, -0.01055]`) and higher success by `6.38` percentage points (`[+2.94, +10.07]`). The additive matched baseline also beat MODE_GAIN in final distance by `0.01591` (`[-0.02665, -0.00577]`). MODE_GAIN and its direct no-context ablation were indistinguishable in this run: `no-context − mode = -0.00216` distance (`[-0.01515, +0.01070]`).

The mismatch condition was sharply adverse. Under REVERSED mapping, MODE_GAIN success was 30.2% and final distance 0.4051; NO_CONTEXT success was 86.0% and final distance 0.1110. The bilinear baseline reached 79.2% success and the task-aware oracle 95.4%.

## Training versus closed-loop outcome

On the shared exogenous supervised training trajectories, MODE_GAIN had the lowest mean final-window training loss (`0.0354`), compared with `0.0543` for the bilinear model and `0.0574` for the additive model. That estimator-fit advantage did not carry over to closed-loop pursuit. The likely issue is a training/deployment distribution gap: training motor axes were randomly assigned, while test axes were selected by each controller's own evolving target estimate. This is a candidate explanation, not an isolated causal diagnosis.

## Interpretation and limits

The state-conditioned update did not improve the ALIGNED navigation outcome over the context-free ablation and lost to both parameter-matched recurrent estimators. Its large failure under REVERSED mapping shows sensitivity to context/sensor mismatch. The task-specific result argues against treating a scalar-estimation advantage as sufficient evidence of sensorimotor transfer.

The motor-state/sensory-coordinate mapping, target process, and controller are artificial. The matched 8-parameter comparisons address capacity count and training updates, but not exact FLOPs or optimization landscape. The Kalman estimator uses the true task model. No result here establishes a new biological finding or broad AI principle.

## Reproducibility

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner, analysis, and verifier: [`model/M2_2D_CLOSED_LOOP_PURSUIT_V1/`](../../model/M2_2D_CLOSED_LOOP_PURSUIT_V1/)
- Episode outcomes, fits, summary, and manifest: [`data/results/M2_2D_CLOSED_LOOP_PURSUIT_V1/`](../../data/results/M2_2D_CLOSED_LOOP_PURSUIT_V1/)
- Independent verification passed all 76,800 unique rows and reproduced 16 crossed-bootstrap intervals. A full independent rerun produced byte-identical episode outcomes and summaries; all fit parameters and loss values also matched (elapsed-time fields naturally differed).
