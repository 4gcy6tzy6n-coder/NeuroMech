# M2 motor-feedback sparse-sensation tracking — results

**Classification:** post-result exploratory artificial mechanism-transfer study. It is not biological validation or evidence of general AI benefit.

## Primary condition

At target-switch hazard `1/120` and 50% sensory dropout, mean per-episode tracking MSE was `0.2581` for sensory-site feedback, `0.3020` for the three-parameter generic one-state RNN, `0.2622` for output-site persistence, `0.2623` for no feedback, and `0.2283` for the task-aware oracle.

The primary contrast `MSE(GENERIC_RNN_1H) − MSE(SENSORY_SITE_FEEDBACK)` was **+0.04386** (crossed seed/episode bootstrap 95% interval **[+0.04247, +0.04526]**; positive in **32/32** training-seed clusters). Sensory-site feedback also exceeded the equal-parameter output-persistence control by **+0.00403** (95% interval **[+0.00333, +0.00475]**) and the no-feedback control by **+0.00416** (95% interval **[+0.00333, +0.00502]**); both direct contrasts were positive in 32/32 seeds.

## Operating boundary

The advantage depended on target dynamics and missingness. At hazard `1/40`, sensory-site feedback had lower MSE than both direct controls at every tested missingness rate: `0.5310` vs `0.5533/0.5533` (25% missing), `0.5546` vs `0.5832/0.5827` (50%), and `0.6467` vs `0.6700/0.6680` (75%), where the paired values are sensory-site / output-persistence / no-feedback. Under slower switching with 75% missingness, the pattern reversed: at hazard `1/240`, sensory-site MSE was `0.2122`, versus `0.1902` and `0.1923`; at the training hazard `1/120`, it was `0.3405`, versus `0.3198` and `0.3199`. Thus the result is a regime-dependent tracking benefit and cost, not a universal advantage.

The oracle's MSE was lower in all nine conditions. The experiment therefore shows neither task-optimal behavior nor superiority over a task-aware estimator.

## Interpretation and limitations

This artificial task asks whether a previous motor command helps a sensory-state estimate account for changes in relative target position during intermittent sensing. It is an information-flow abstraction motivated by RIM-to-AIY motor-state feedback in *C. elegans*, not a model of thermotaxis or a claim that the worm performs optical target tracking.

The generic comparator has only one hidden state and three trainable parameters. The direct placement controls are also three-parameter models, but the test does not cover stronger multi-unit recurrent networks or modern adaptive controllers. Occlusion is represented by an exact zero sensory sample, which makes missingness partly inferable from the input distribution; ambiguous missingness was not tested. Training used fixed arm-specific initial values and equal update/token budgets, but not hyperparameter sweeps or multiple initialization families. These design limits leave optimization and comparator strength as live alternatives to a general mechanistic advantage.

The appropriate claim is narrow: **in this simulated target-tracking task, a three-parameter motor-feedback sensory update improved closed-loop performance over the tested one-state generic RNN and direct placement/ablation controls in the training condition, with clear costs under slow switching and heavy missingness.** The result motivates a stronger-capacity and ambiguous-missingness follow-up; it does not establish biological-to-AI transfer or publication-level novelty by itself.

## Reproducibility

- Protocol: [`CONTRACT.md`](CONTRACT.md)
- Model, runner, analyzer, verifier: [`model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/`](../../model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/)
- Episode outcomes, fit records, summary and source manifest: [`data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/canonical/`](../../data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/canonical/)
- The independent verifier checks all 368,640 episode rows, 128 learned fits, source/result hashes and the primary/direct-control bootstrap estimates.
- A fresh full rerun reproduced the episode CSV byte-for-byte and all non-runtime training fields exactly; see [`REPRODUCIBILITY.json`](../../data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/canonical/REPRODUCIBILITY.json).
- Figure legend and rendered QA: [`FIGURE_LEGEND.md`](FIGURE_LEGEND.md) and [`figure QA notes`](../../data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/figures/QA.md).
