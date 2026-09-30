# M2 downstream decision-utility probe V1

**Status:** post hoc exploratory analysis of frozen `M2_FORWARD_STATE_SENSORY_GATE_V3` models and test streams. V3 outcomes were known before the decision outcomes were calculated. This analysis cannot be confirmatory.

## Question

Do differences in state estimation from V3 survive when frozen state estimates are converted into downstream actions with distinct utility functions?

## Frozen source and data

Use the exact V3 model parameters and regenerate the same held-out streams from its public seeds. No model is retrained. Conditions, environments, training seeds, and unit remain as specified in the V3 contract. Each episode is the independent evaluation unit; time steps are averaged within episode.

## Decision readouts

All decision rules and costs are fixed before this analysis:

1. `SIGN_CHOICE`: choose `+1` for estimate ≥0, otherwise `−1`; reward is 1 for matching the sign of the latent state, 0 otherwise. The initial known state at t=0 is excluded.
2. `THRESHOLD_CHOICE`: choose “engage” when estimate ≥0.5. Engagement reward is `x−0.5`; abstention reward is 0. Report mean reward and regret relative to the per-time-step oracle `max(x−0.5,0)`.
3. `PERSISTENT_SIGN_ACTION`: choose the sign of the estimate each step; reward is +1 for a correct sign and incur a 0.10 cost each time the action switches. The initial known state is excluded; no switching cost is charged before the first scored action.

The only contrasts of interest are descriptive paired per-episode differences between the frozen `MODE_GAIN_FILTER` and `CONSTANT_GAIN_FILTER`, `BILINEAR_RNN_1D`, `GRU_1D`, and `KALMAN_ORACLE` readouts. No post-hoc model selection or pooled cross-condition claim is allowed. This is a decision-readout probe, not a control-learning experiment: the state estimator has no action feedback and no policy is trained.

## Interpretation boundary

These utilities and observations are artificial. A result can show whether the V3 state estimates transfer to simple downstream decisions on the same synthetic episodes; it cannot establish a biological computation, general AI benefit, or an NMI contribution.
