# M2 cross-task state-feedback transfer V1

**Experiment ID:** `M2_CROSS_TASK_STATE_FEEDBACK_V1`  
**Status:** new artificial task-family experiment, specified before this experiment's outcomes. The M2 source biology and extensive prior M2 synthetic outcomes are already known, so this is exploratory and outcome-informed at the project level. It is not a biological reanalysis or confirmatory test.

## Biological anchor and abstraction boundary

Ji et al. (2021) report that AIY carries sensory and locomotor-state information; optogenetic AVA/AVB modulation of AIY depends on RIM, and RIM ablation alters downstream sensory representation and forward-run persistence under the tested thermotaxis conditions. This supports a bounded cell-class-level claim that motor-state feedback can modulate sensory processing. It does **not** show that worm locomotor state encodes observation reliability. The reliability relationship below is a new artificial hypothesis, not a biological finding.

The transferred operation is explicitly defined as: predict a prior scalar state, then weight current sensory evidence using a gain conditioned on a one-bit state input. The artificial counterfactual removes the state-to-sensory-gain interaction while preserving a parameter-matched generic recurrent controller.

## New task family

Each episode is a scalar latent-state estimation stream. The hidden state follows `x[t] = 0.97*x[t-1] + epsilon[t]`, with `epsilon ~ Normal(0, 0.05)`. A binary context `q[t]` (the abstracted motor-state input) follows a symmetric two-state Markov chain with switch probability 0.05. Observation is `y[t] = x[t] + sigma[t]*z[t]`, where `z ~ Normal(0,1)`, low-noise sigma is 0.25, high-noise sigma is 1.40, and the high-noise state is associated with q as follows:

- `ALIGNED`: `P(high noise | q=+1)=0.90` and `P(high noise | q=-1)=0.10`.
- `INDEPENDENT`: high-noise probability is 0.50 regardless of q.
- `REVERSED`: the ALIGNED mapping is reversed.

All conditions have the same marginal frequency of high and low noise. Train only on `ALIGNED`; evaluate the same trained models on all three conditions using common exogenous streams within each condition. The generator, task, and outcomes are synthetic.

## Models

The two primary policies each have one scalar recurrent state and exactly four trainable scalar parameters.

1. `MODE_GAIN_FILTER`: `prior[t] = rho * state[t-1]`; `state[t] = prior[t] + k(q[t]) * (y[t] - prior[t]) + bias`, where `rho`, two context-conditioned gains, and bias are learned. This is the mechanism-specific operation.
2. `GENERIC_RNN_1D`: `state[t] = tanh(w_y*y[t] + w_q*q[t] + w_h*state[t-1] + b)`, with four learned scalars and one scalar state. It receives the same observation and context.

Secondary references are a learned context-free scalar filter, a current-observation-only estimate, and a parameter-free linear Kalman reference using the known conditional expected observation variance. The Kalman reference is not capacity matched and is not the primary comparator.

All learned policies receive the same train episodes within each training seed, use the same number of optimization updates and the same optimizer settings, and minimize mean squared state-estimation error directly. No tuning is done on evaluation conditions.

## Sample and outcomes

- Training seeds: `42000–42019` inclusive.
- Training set: 256 episodes per training seed; horizon 160.
- Evaluation set: 512 common episodes per condition; horizon 160; generated independently from training.
- Primary analysis unit: crossed training seed and evaluation episode. Time steps are averaged within episode and are not independent samples.
- Primary estimand: `MSE(GENERIC_RNN_1D) - MSE(MODE_GAIN_FILTER)` on the `ALIGNED` test condition. Positive values favor the mechanism-specific filter.
- Primary uncertainty: 20,000 crossed bootstrap replicates, resampling model-training seeds and shared evaluation-episode IDs independently; seed `20261005`.
- Secondary: same contrast in `INDEPENDENT` and `REVERSED`; per-model MSE/MAE; learned parameters and training curves; comparison to the analytic linear-filter reference.

No minimum effect threshold is asserted. This experiment tests only whether the explicit gain parameterization helps on this synthetic estimation family after training on aligned contexts, and whether the effect depends on that relationship.

## Interpretation limits

A favorable result would be evidence for this algorithmic inductive bias on this synthetic task family, not evidence that the worm implements the fitted equation or that the mechanism is broadly useful in AI. A reversed or independent-condition cost is a boundary result. A null result weakens this specific transfer formulation, not the published biological finding. The work is retrospective relative to the M2 synthetic project and must not be called confirmatory or NMI-ready on its own.
