# M2 action-conditioned state-space comparison on 2D pursuit — V1 contract

**Experiment ID:** `M2_ACTION_CONDITIONED_RKN_2D_PURSUIT_V1`

**Classification:** post-result exploratory artificial comparison. It uses the previously studied 2D pursuit task and outcomes from related M2 transfers are known. It cannot establish independent task generalization, biological validation, or a novel general AI principle.

## Question

Does the M2-inspired context-conditioned sensory update improve closed-loop pursuit over an established action-conditioned recurrent state-space model (ac-RKN) when both learn from the same trajectories and observation dropouts? The comparison targets whether the biological abstraction adds value beyond conditioning a recurrent latent-state transition on action.

## Task and data

Reuse the 2D pursuit task equations in `M2_2D_CLOSED_LOOP_PURSUIT_V1`: each episode has a fixed target sampled from independent `Normal(0, 0.5²)` coordinates; the agent starts at `(0,0)`; each of 32 steps moves one coordinate by `0.12`; observation is the target residual multiplied by a movement-state-dependent sensor matrix plus `Normal(0,0.25² I)` noise. `ALIGNED` and `REVERSED` use the same sensor matrices as the earlier contract. Add an outcome-independent 20% whole-observation dropout; dropped vectors are zero-filled and marked invalid. A model may skip its observation update on invalid steps.

Generate 512 training episodes per training seed using balanced random axis and direction actions. All fitted arms use identical target, action, noise, and dropout streams within each seed. Evaluate 256 paired held-out targets per seed under closed-loop control in both sensor mappings. Fresh training seeds are `76100..76123`; held-out exogenous streams are generated independently from the training streams. No held-out outcome is used for model selection.

## Model arms

- `MODE_GAIN`: the existing 8-parameter M2-inspired coordinate-wise prediction-error update, including motor-state-conditioned sensory gains and action displacement in the prior.
- `BILINEAR_RNN_8P`: an 8-parameter unconstrained observation-by-context recurrent estimator, carried forward as a capacity-matched generic control.
- `ACRKN_L1`: an action-conditioned recurrent Kalman cell based on the official ac-RKN implementation. It receives the same observation/context stream, an explicit validity mask, and the action displacement as a latent transition input. Latent observation dimension is 1, transition basis count is 1, and the control network has no hidden layer. Its parameter count is reported; it is not represented as parameter-matched to the 8-parameter arms.
- `MODE_GAIN_ACTION_YOKE`: the same fitted `MODE_GAIN` parameters and policy, but the estimator receives a fixed deranged donor episode's previous action displacement; the physical environment still applies the recipient's own chosen action. This preserves the cohort's action-feedback marginal at each step while breaking recipient correspondence.
- `KALMAN_ORACLE`: the known-task Gaussian posterior estimator, given the true sensor matrix, noise variance, and target prior. It is an unmatched task-aware reference.

All learned arms receive 200 Adam updates with batch size 16 on the same number of training episodes and sequence steps. Fixed learning rates are 0.02 for `MODE_GAIN`/`BILINEAR_RNN_8P` and 0.003 for `ACRKN_L1` (the ac-RKN paper's default order of magnitude). Report trainable parameter count, optimizer updates, sequence tokens, and measured CPU training time for every fit. No hyperparameter tuning on held-out episodes is allowed.

## Outcomes and inference

Primary endpoint: final Euclidean target distance in `ALIGNED`, smaller is better. Primary contrast: `final_distance(ACRKN_L1) − final_distance(MODE_GAIN)`; positive favors `MODE_GAIN`. The 95% interval uses 10,000 paired crossed-bootstrap resamples over 24 training-seed blocks and 256 held-out episode IDs (seed `20261031`). Episodes and time steps are not independent replicates. Secondary measures are success fraction (final distance ≤0.12), mean distance over steps, the same contrasts in `REVERSED`, and `MODE_GAIN_ACTION_YOKE − MODE_GAIN` under both mappings. The yoke donor permutation is seed-fixed before outcome scoring and has no fixed points.

## Provenance and interpretation

The ac-RKN cell is adapted from ALRhub's official CoRL 2020 implementation at commit `7a8ae18c17ff3f324f58a6d2ef8ee93265a6fa07`, under its MIT license. Any compatibility edits and the exact vendored source hashes will be recorded. The M2 controller's previous action input is an abstraction, not a claim that the worm implements the ac-RKN equation or the artificial observation mapping.

A positive result supports only a task-conditional artificial performance difference on this 2D pursuit benchmark. A win over ac-RKN would not establish broad AI benefit or biological causality; a loss is a meaningful boundary against the M2 abstraction's algorithmic contribution. The same task family and outcome-informed project history make this exploratory, not confirmatory.
