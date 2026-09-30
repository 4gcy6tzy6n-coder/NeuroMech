# M2 forward-state sensory gate transfer V3

**Experiment ID:** `M2_FORWARD_STATE_SENSORY_GATE_V3`
**Status:** exploratory follow-up; V1 implementation failure and V2 outcomes were known before this run. This is not confirmatory evidence.

**Biological anchor:** Ji et al., “Corollary discharge promotes a sustained motor state in a neural circuit for navigation,” *eLife* 10:e68848 (2021), [author article and Figure 7 model](https://elifesciences.org/articles/68848v2). The source model gates thermosensory input by locomotor state. V3 tests an artificial input-channel abstraction, not the full source model.

## Question

Does a state-conditioned sensory update retain an advantage over its context-free ablation after training across varied latent dynamics, when compared with both a parameter-near matched generic recurrent model that can express an input×context interaction and a wider GRU? How does the computation behave when state-to-observation alignment is absent or reversed, and when latent persistence is outside the training range?

## Synthetic task and data

Each episode has 160 steps, a scalar latent state `x[t]=phi*x[t-1]+epsilon[t]` with `x[0]=0`, binary context `q[t] ∈ {-1,+1}` switching with probability 0.05, and observation `y[t]=H(q[t])x[t]+sigma_obs*z[t]`.

Training episodes are ALIGNED and independently draw `phi~Uniform(0.84,0.96)`, `sigma_process~Uniform(0.08,0.18)`, and `sigma_obs~Uniform(0.15,0.35)`. There are 512 training episodes per seed. Test environments are:

- `IN_RANGE`: same parameter distributions as training;
- `HIGH_PERSISTENCE`: `phi=0.985`, process SD `0.18`, observation SD `0.25`;
- `LOW_PERSISTENCE`: `phi=0.75`, process SD `0.18`, observation SD `0.25`.

For each test stream, conditions share the same latent state, context and observation-noise innovations. `ALIGNED` has `H(+1)=1,H(-1)=0`; `INDEPENDENT` has `H(+1)=H(-1)=0.5`; `REVERSED` has `H(+1)=0,H(-1)=1`. Thus all conditions share the same input and latent innovations; only the context-to-signal mapping changes.

## Models

All trainable models use the same training episodes, supervised latent-state MSE, Adam optimizer, 300 updates, and training seed. `MODE_GAIN_FILTER` has one recurrent scalar state and four parameters: leak, forward gain, reverse gain and bias. The direct mechanism ablation is the three-parameter `CONSTANT_GAIN_FILTER`. `GENERIC_RNN_1D` has four parameters; `BILINEAR_RNN_1D` adds an unconstrained `y*q` term (five parameters) so a generic recurrent update can express multiplicative context–input interaction; `GRU_1D` is a one-hidden-unit GRUCell with learned readout and a larger parameter count. A task-aware scalar Kalman filter uses known episode dynamics and the actual observation coefficient; it is a reference, not a learned or capacity-matched model.

## Samples and estimands

Training seeds: 42000–42019. Each of the three test environments has 512 shared episodes and 160 time steps; time steps are averaged within each episode. The primary estimand is `MSE(CONSTANT_GAIN_FILTER)-MSE(MODE_GAIN_FILTER)` in `IN_RANGE × ALIGNED`; positive values favor state-conditioned gain over the direct context-free ablation. The primary interval is a 20,000-replicate crossed bootstrap over training seeds and shared test episodes (seed 20261005). Secondary contrasts compare the mode-gain filter with the bilinear RNN and GRU and examine the other mapping/environment conditions. No pooling across conditions is performed.

## Interpretation boundary

This is a synthetic benchmark motivated by a published circuit-model operation. Its sensory channel and tasks are artificial assumptions. Even a robust advantage across these tests would support only an algorithmic inductive bias in the tested family, not the biological implementation, a universal AI principle, or an NMI-level contribution by itself. Results are exploratory because earlier versions and their outcomes were inspected before V3.
