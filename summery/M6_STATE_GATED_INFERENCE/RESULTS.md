# M6 — State-gated sensory inference: results

**Classification:** outcome-informed exploratory computation on a new synthetic task family. The study followed earlier M2 outcomes. It is not biological validation, not a confirmatory test, and not evidence of general AI transfer.

## Primary result

The primary contrast is episode MAE for `STATE_GATED_GAIN − INNOVATION_ADAPTIVE` on the high-reversal-noise profile, averaged equally over three held-out hazard values. Positive values mean the state-gated filter is worse.

| Target-switch hazard | State gate MAE | Innovation-adaptive MAE | Gate − adaptive | Crossed 95% interval |
|---:|---:|---:|---:|---:|
| 0.005 | 0.2093 | 0.1622 | +0.04716 | [+0.04307, +0.05122] |
| 0.040 | 0.2606 | 0.1837 | +0.07689 | [+0.07206, +0.08175] |
| 0.075 | 0.2994 | 0.1958 | +0.10356 | [+0.09801, +0.10916] |
| Equal-weight mean | — | — | **+0.07587** | **[+0.07314, +0.07864]** |

The state-gated gain lost to the parameter-count-matched innovation-adaptive filter in all three high-noise cells. The adaptive filter uses the magnitude of its own prediction residual to adjust gain, without receiving the context label.

## What the comparison does show

On the high-reversal-noise profile, the state gate beat a single global gain descriptively at all three hazards (MAE 0.209/0.261/0.299 vs 0.244/0.292/0.332). This indicates that the explicit context input helped relative to a fixed global gain in this task. It did not beat the equally parameterized generic residual-adaptive filter.

The learned state gains were approximately `g_forward=0.909` and `g_reversal=0.253`; the innovation-adaptive filter learned intercept `−1.938` and residual coefficient `+1.005`. The state gate's performance depends on the synthetic relation between context and observation noise: its errors rose under equal and especially reversed noise mappings. Those relations were stipulated by the task generator; they are not established by the *C. elegans* experiments.

## Strong reference

The oracle HMM, given the true target-switch hazard and observation-noise mapping, had near-zero error in this deliberately simple two-state telegraph task. The gap shows that all learned filters remain far from the task-specific model-based solution. It also means this task is useful for debugging adaptation behavior but is not a difficult stand-alone benchmark for an NMI-level AI claim.

## Implementation incident

Two exploratory output directories are retained as invalid. In both, the learned-filter evaluation initially accumulated `abs(estimate)` instead of `abs(estimate − target)`; an attempted intermediate patch did not modify the executed line. Those outputs are marked invalid and are excluded from every result above. The final `results_v2_corrected_metric/` run uses the target-relative error. The fitted parameters were unchanged because training already used the target-relative objective; all evaluation metrics and contrasts were recomputed from scratch.

## Interpretation

The task supports a narrow negative finding: a learned context-specific gain can outperform a single global gain when the synthetic context reliably predicts sensor noise, yet lose to a same-size generic filter that adapts to prediction residuals. The counterfactual profiles show the cost of encoding the wrong context–reliability mapping. This does not refute motor-state feedback in worms; it shows that a direct state-gated gain abstraction is not sufficient to outperform a generic adaptive estimator here.

The study remains same-family generalization across held-out trajectories and hazard values sampled from the training support. It does not test a separate task family, closed-loop behavior, biological data, or a broad RNN baseline. A future study must change the task family and add computationally matched recurrent baselines before making a broad transfer claim. Do not tune this same benchmark against the reported results.
