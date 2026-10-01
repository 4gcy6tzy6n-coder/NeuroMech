# M2 premotor predictive-signal artificial transfer V1

**Classification:** post-result exploratory artificial benchmark, motivated by the source-trace V2 result. It is not a new biological test, a direct reconstruction of AIY/AVA, or confirmatory AI evidence.

## Question

Can an explicit short-horizon state-prediction signal improve an artificial estimator beyond its observation history, and does a low-parameter forecast-fusion update retain value against a small generic GRU given the same input channel and training exposure?

The recent source-trace analysis motivates testing the *computational abstraction* that an additional premotor-like signal contains information about a near-future state. It does not establish that AIY or AVA implements this equation, that such a signal is available in artificial agents, or that it encodes sensor reliability. The benchmark therefore generates the signal synthetically and treats any benefit as conditional on that stipulated information channel.

## Task

Each episode is an 80-step symmetric binary hidden-state process (`−1/+1`) with a per-step switch hazard of `0.05`. Observations are Gaussian around the current state (standard deviation `1.25`) and are omitted in Markov bursts with stationary visibility `0.5` and mean run length four steps. The target at time `t` is the hidden state four steps later. A synthetic forecast cue reports that future state correctly with probability `q`; training uses aligned `q=0.72`. Evaluation conditions use aligned `q=0.72`, uninformative `q=0.50`, and reversed `q=0.28`, with shared hidden trajectories, observation noise, and cue random draws within each test block.

## Model arms

- `PREMOTOR_FILTER`: a six-parameter recurrent observation estimator whose output logit receives an additive forecast-cue term.
- `NO_CUE_FILTER`: the exact same six-parameter model and optimizer, with the cue input fixed to zero.
- `GRU_CUE`: a two-unit generic GRU receiving observation, visibility, and the same cue.
- `GRU_NO_CUE`: the same GRU parameterization with its cue input fixed to zero.
- `CUE_ONLY`: the cue score without an observation estimator.
- `PREMOTOR_FILTER_YOKED_CUE` and `GRU_CUE_YOKED_CUE`: the corresponding trained model evaluated with the cue reassigned from a different test episode by a fixed nonidentity cyclic permutation. This preserves each timestep's cue marginal across episodes while breaking recipient-specific correspondence.

The GRU is a capacity-stronger, higher-parameter comparator; it is not described as parameter-matched. Every fitted arm receives the same training episodes, 160 Adam updates, batch size 16, and sequence-token exposure at a given training-set size. Training sizes are 32, 128, and 512 episodes. All neural models are trained only on aligned cue mapping.

## Outcomes

Primary metric is per-episode AUC for the four-step-ahead binary state target. The primary condition is training size 128 and aligned test mapping. Primary contrasts are `PREMOTOR_FILTER − NO_CUE_FILTER` (value of the cue within the structured model) and `PREMOTOR_FILTER − GRU_CUE` (structured-versus-generic comparison). `GRU_CUE − GRU_NO_CUE`, `CUE_ONLY`, data-size trends, uninformative/reversed mapping, and Brier score are secondary. Episode AUC is not calculated when an episode has only one target class; counts are reported.

Uncertainty is paired across training-seed blocks and shared test episodes. Training seeds are 62000–62019; each block has 128 test episodes per mapping. Report parameter counts, update counts, sample tokens, and fit time. No threshold or conclusion will be selected from secondary mappings after seeing outcomes.

## Interpretation

A gain over the no-cue ablation shows that the generated predictive side channel carries useful information in this simulator. A gain over the generic GRU would be evidence only for the tested low-dimensional forecast-fusion inductive bias, task, data sizes, and cue mapping. A loss to the GRU or a reversal under mismatch is retained as a boundary result. None of the outcomes establishes that the biological circuit supplies such a signal causally, transfers it to AI, or improves general AI performance.
