# M2_LTC_THERMOTAXIS_REVERSAL_V1 — failure log

## Preflight correction

The first preflight correctly found finite outputs and losses but marked `LTC_NO_FEEDBACK` as having a gradient failure because its `beta` parameter is intentionally disconnected from the forward pass. The model arms preserve the same parameter tensor layout, while the no-feedback ablation disables this route. The preflight was corrected to require finite gradients for active parameters and explicitly expect the one dormant `beta`; the full run began only after the corrected preflight passed. This did not change the model equation, training schedule, or outcome data.

## Main experimental failure

The experiment did not produce useful setpoint tracking in any learned arm. At the primary condition, learned position MSEs clustered around 132; sensory-site action energy was 0.00249 and preferred-band occupancy was 0.110. In comparison, a privileged gradient-sign oracle achieved MSE 28.82. The oracle establishes that a much better policy is possible with additional state information, but it cannot tell whether the bottleneck is sensor informativeness during gaps, optimization, action scaling, parameterization, or their interaction.

Because sensory-site feedback failed to separate from output-site, no-feedback, dense-feedback, and yoked controls, the preregistered interpretation criterion was not met. The worse GRU MSEs do not rescue the mechanism claim: all learned policies were weak, and comparisons against an underperforming task solution are not evidence of useful transfer.

## Design and inference lessons

- Add a frozen task-viability criterion based on non-privileged controller performance before interpreting mechanism contrasts.
- Record a no-action baseline and learning curves from the start; final training loss alone does not show closed-loop task competence.
- Keep the oracle diagnostic and report its privileged information separately.
- Distinguish nominal parameter count from effective trainable parameter count when an ablation intentionally disconnects a parameter.
- Do not tune this result post hoc. Any revised observation scale, action range, objective, or optimizer budget requires a new version, a new contract, and fresh seeds.

This is an artificial implementation/task-design failure, not evidence against the biological RIM–AIY finding.
