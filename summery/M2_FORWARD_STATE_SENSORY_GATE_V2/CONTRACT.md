# M2 forward-state sensory gate transfer V1

**Experiment ID:** `M2_FORWARD_STATE_SENSORY_GATE_V2`
**Status:** post-correction exploratory artificial benchmark. V1 had an implementation error and its metrics are invalid; V1 outcomes were inspected before this correction. This V2 is not confirmatory. Prior M2 results and biological literature were already known. No biological outcome is analyzed here.

## Biological anchor and abstraction

Ji et al. (2021; https://doi.org/10.7554/eLife.68848) model thermosensory input to AIY as gated by forward locomotor state and include positive motor-state feedback. This artificial benchmark isolates only the computational motif of a state-gated sensory channel. It does not reproduce the full published model or establish that the fitted artificial policies are biologically implemented.

## Synthetic task

The latent scalar follows `x[t] = 0.97*x[t-1] + Normal(0, sqrt(0.05))`. A binary context `q[t] ∈ {-1,+1}` switches with probability 0.05. Observation is `y[t] = H(q[t])*x[t] + 0.25*z[t]`, `z~Normal(0,1)`. The forward-state observation coefficients are:

- `ALIGNED`: H(+1)=1, H(-1)=0.
- `INDEPENDENT`: H(+1)=H(-1)=0.5.
- `REVERSED`: H(+1)=0, H(-1)=1.

All conditions have mean H=0.5. Train only on ALIGNED; evaluate the same trained models on all conditions using common evaluation streams.

## Policies and estimand

Primary learned policies have one scalar recurrent state and four trainable scalars. `MODE_GAIN_FILTER` learns a leak, separate observation gains for q=+1/-1, and bias. `GENERIC_RNN_1D` is `tanh(w_y*y+w_q*q+w_h*h_prev+b)`. Both receive identical inputs and training data and use the same optimizer/update budget. Secondary references are a context-free gain filter, current observation, and a task-aware linear Kalman filter with known H and noise variance; the latter is not capacity matched.

Train seeds 42000–42019; 256 episodes per seed; horizon 160; 250 full-batch Adam updates at learning rate 0.025. Evaluate 512 episodes per condition and seed. Primary estimand is `MSE(GENERIC_RNN_1D)-MSE(MODE_GAIN_FILTER)` in ALIGNED; positive favors the mode-gain filter. Uncertainty uses 20,000 crossed bootstrap replicates over training seeds and shared test episodes (seed 20261005). Time steps are averaged within episode, not treated as independent units.

Because V1 outputs were inspected before this corrected rerun, a secondary mechanism-specific ablation is also reported transparently: `MSE(CONSTANT_GAIN_FILTER)-MSE(MODE_GAIN_FILTER)` within each condition, with 20,000 crossed bootstrap replicates. This directly tests whether learned context-dependent gains outperform the context-free update.

## Claim boundary

This is a synthetic algorithmic abstraction motivated by an explicit source-model operation. It is neither a biological replication nor proof of AI-wide advantage, and it does not test the full biological feedback circuit. A negative result would constrain this implementation/task pairing only.
