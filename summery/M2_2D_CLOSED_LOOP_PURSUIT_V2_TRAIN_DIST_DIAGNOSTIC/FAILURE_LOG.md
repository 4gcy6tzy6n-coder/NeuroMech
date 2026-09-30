# Failure and limitation log — V2 training-distribution diagnostic

## Execution incidents

- No partial canonical run was retained. The complete run produced 153,600 unique episode-policy-regime records.
- No code or contract changes were made after inspecting V2 outcomes.

## Interpretation risks retained

- This is a post-result diagnostic derived from V1, so it is exploratory and cannot serve as independent confirmation.
- The teacher-mixed policy is task-aware and Bayes optimal for the stipulated observation model; it is not a neutral approximation of the occupancy induced by each learned controller.
- The primary interaction is a relative contrast. MODE_GAIN improved under teacher-mixed training, but the bilinear comparator worsened in aligned closed-loop performance; the interaction must not be described as a uniquely isolated MODE_GAIN effect.
- The additive capacity-matched model remained better on aligned final distance, and the no-context ablation was not clearly worse than MODE_GAIN.
- MODE_GAIN remained vulnerable to reversed context/sensor mapping even with teacher-mixed training.
- Model parameter count and optimizer budget were matched for the 8-parameter learned arms; FLOPs, optimization landscape, and effective state occupancy were not matched.
- All tasks and sensor mappings are synthetic. Biological-to-AI transfer is not established.

## Independent rerun

The complete runner was rerun into a separate temporary directory. Episode metrics, normalized training records excluding elapsed wall time, and the analyzed summary matched the canonical run exactly. The raw training-metrics file hash differs because it includes measured `training_seconds`; fitted parameters and loss fields were byte-identical.
