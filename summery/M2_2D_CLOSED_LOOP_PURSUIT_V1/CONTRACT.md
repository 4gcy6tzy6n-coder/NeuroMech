# M2-inspired 2D closed-loop pursuit — contract

**Experiment ID:** `M2_2D_CLOSED_LOOP_PURSUIT_V1`  
**Classification:** exploratory artificial sensorimotor study. Previous M2 results informed the design. It is not biological validation.

## Question

Does a state-conditioned sensory update help an agent reach a two-dimensional target when its own motor state determines which sensory coordinate is reliable, compared with parameter-matched recurrent adaptive estimators?

## Task

Each episode has a fixed target `theta=(theta_x,theta_y)` drawn from independent `Normal(0,0.5²)` coordinates, agent position initially `(0,0)`, 32 control steps, and movement step length `0.12`. At time `t`, the motor state `q∈{+1,-1}` identifies the current movement axis: `+1` horizontal, `−1` vertical. In ALIGNED conditions the observation matrix is diagonal with gains `(0.95,0.10)` when `q=+1` and `(0.10,0.95)` when `q=−1`; REVERSED swaps those rows. Observation is `y=H_q*(theta-position)+Normal(0,0.25² I)`. Thus the average coefficient per coordinate across equally sampled motor states is 0.525 in both mappings; only state/coordinate alignment differs.

At each closed-loop step, the controller selects the coordinate with the largest absolute estimated target residual and moves one step toward the estimated target along that axis. The chosen axis sets the next motor state and therefore future sensory quality. Stop early when Euclidean target distance is ≤0.12. Training trajectories use 512 targets per training seed, 32 steps, and random balanced axis/direction actions, providing exogenous motor-state coverage. Models receive `y`, current motor state `q`, and the displacement applied before the observation; their supervised target is the true target residual after that displacement.

## Models

- `MODE_GAIN`: 8 trainable parameters; a two-coordinate prediction-error update with coordinate-specific gain by movement state, learnable prior retention and bias.
- `NO_CONTEXT`: 6-parameter direct ablation using coordinate-specific gains that ignore motor state.
- `ADDITIVE_RNN_MATCHED`: 8-parameter diagonal recurrent update with additive motor-state input.
- `BILINEAR_RNN_MATCHED`: 8-parameter diagonal recurrent update with unconstrained observation×motor-state interaction.
- `KALMAN_ORACLE`: exact Gaussian posterior-mean estimator for the static target, supplied the true prior, sensor matrix and noise. This is a task-aware reference, not a learned or capacity-matched model.

All learned models use the same training targets, action trajectories, noise innovations, supervised objective, optimizer, 200 updates and batch size 16. Run 30 training seeds (`75000..75029`) and 256 held-out target episodes per seed and mapping. The trained-seed block is the independent replicate; episodes are paired across models within seed and mapping.

## Outcomes

Primary: final Euclidean target distance in ALIGNED, contrast `distance(BILINEAR_RNN_MATCHED)-distance(MODE_GAIN)`; positive favors the mechanism-shaped update. Also report success fraction, average distance over steps, time-to-success, direct-ablation contrast, and the same comparisons under REVERSED mapping. Primary uncertainty is a crossed bootstrap over training seeds and held-out target episode IDs (10,000 percentile resamples, fixed seed 20261020). Report compute and parameter counts; the two 8-parameter learned systems have matched parameter count and training budget, while measured runtime can differ.

## Interpretation boundary

This is a new artificial 2D pursuit task with an invented motor-state/sensory-coordinate mapping. It tests whether an M2-inspired adaptive update survives a closed-loop geometry change and a parameter-matched bilinear estimator. It does not show that worms use this mapping, does not validate a new biological mechanism, and does not establish broad AI benefit. Results are exploratory and task-specific.
