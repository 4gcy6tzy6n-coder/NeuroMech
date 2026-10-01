# M2_LTC_THERMOTAXIS_REVERSAL_V1 — results

## Status

**POST-RESULT EXPLORATORY ARTIFICIAL EXPERIMENT; mechanism criterion not met.** This run is not biological validation. The task, model family, and controls were informed by earlier M2 results, and this experiment therefore cannot be called an independent confirmation.

## What ran

The frozen run completed 32 training-seed blocks, seven trained controllers, three gradient-reversal hazards, and 128 evaluation episodes per seed × controller × hazard: 98,304 episode rows and 224 fitted models. Each learned arm received 120 Adam updates on 96 training episodes. Parameter counts were 114 for each LTC arm (one dormant parameter in `LTC_NO_FEEDBACK`), 113 for `GRU_4`, and 321 for `GRU_8`. The gradient-sign oracle is privileged and excluded from learned-model contrasts.

## Primary endpoint

The primary condition was the faster-than-training gradient-reversal hazard `1/20`; lower episode position MSE is better. Contrasts below are comparator MSE minus sensory-site MSE, so positive values favor sensory-site feedback. Intervals resample paired training-seed blocks.

| Comparator | Mean paired difference | 95% seed-block bootstrap CI | Positive blocks |
|---|---:|---:|---:|
| Output-site LTC | +0.0065 | [−0.0884, +0.0976] | 15/32 |
| No-feedback LTC | +0.0044 | [−0.0270, +0.0339] | 17/32 |
| Dense-feedback LTC | +0.00003 | [−0.0348, +0.0326] | 16/32 |
| Yoked sensory feedback | −0.0337 | [−0.0801, +0.0062] | 16/32 |
| `GRU_4` | +0.5282 | [+0.0338, +1.0477] | 21/32 |
| `GRU_8` | +1.0710 | [+0.3262, +1.9694] | 17/32 |

The sensory-site arm did **not** beat the output-site, no-feedback, or yoked controls with a resolved paired effect; it also did not beat the dense-feedback control. The frozen criterion for a self-contingent sensory-site mechanism advantage is therefore **not met**. Although both GRU contrasts favor sensory-site feedback, the absolute performance of all learned arms indicates a task-learning problem: sensory-site position MSE was 132.32, while the privileged gradient-sign oracle reached 28.82. Learned LTC action energy was only 0.00249 (mean squared action), and its preferred-band occupancy was 0.110. These outcomes are consistent with weakly moving or nearly stationary learned policies, so the apparent GRU disadvantage cannot be interpreted as evidence that the LTC mechanism is superior.

The main failure is not a subtle statistical ambiguity: the controller-training setup failed to produce useful setpoint tracking in learned arms. The oracle confirms that the task has a strong privileged solution, but does not validate that the agents received sufficiently informative inputs or that the optimizer/controller parameterization could learn it. The trial is retained as a bounded negative implementation result; no hyperparameter changes or outcome-informed rescue runs are folded into it.

## Biological and prior-art boundary

Ji et al. (2021) motivates studying RIM-dependent motor-state influence on AIY sensory representation and forward-state persistence. The artificial task's explicit gradient-sign inference rule is a derived hypothesis, not a measured worm computation. Efference-copy/state updating and LTCs are established prior art; this run claims neither as novel. See the [frozen contract](CONTRACT.md) for scope and the [failure log](FAILURE_LOG.md) for design lessons.

## Reproducibility bundle

- Raw episode and fit records, analysis summary, and run manifest: [`data/results/M2_LTC_THERMOTAXIS_REVERSAL_V1/`](../../data/results/M2_LTC_THERMOTAXIS_REVERSAL_V1/)
- Runner, analysis, plotter, and verifier: [`model/M2_LTC_THERMOTAXIS_REVERSAL_V1/`](../../model/M2_LTC_THERMOTAXIS_REVERSAL_V1/)
- Figure: [`M2_LTC_THERMOTAXIS_REVERSAL_V1.png`](../../data/results/M2_LTC_THERMOTAXIS_REVERSAL_V1/figures/M2_LTC_THERMOTAXIS_REVERSAL_V1.png)
