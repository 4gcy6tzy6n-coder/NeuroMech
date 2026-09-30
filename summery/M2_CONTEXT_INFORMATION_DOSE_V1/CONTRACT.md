# M2 context-information dose response — contract

**Experiment ID:** `M2_CONTEXT_INFORMATION_DOSE_V1`  
**Classification:** exploratory artificial mechanism study. Earlier M2 model outcomes are known; this is a new dose-response analysis, not confirmatory evidence or biological validation.

## Question

How does a state-conditioned sensory update's relative performance change as the relationship between the observed motor-state context and the observation channel is weakened, removed, or reversed?

## Task

Each episode contains a scalar latent AR(1) process, `x[t]=phi*x[t-1]+epsilon[t]`, and a binary state `q[t]` that switches with probability 0.05. Observation is `y[t]=H(q[t],kappa)*x[t]+sigma_obs*z[t]`, where `H=0.5+kappa*q`. Test `kappa` values are `{-0.50,-0.40,...,0.50}`. Thus the average observation coefficient remains 0.5; only how informative the context is about the coefficient changes. `kappa=+0.5` is the fully aligned training condition, `0` removes context information, and negative values reverse the relation.

Training uses only `kappa=+0.5`, 256 episodes per fit, 100 steps per episode, and 200 full-batch Adam updates. Test uses one shared set of 256 episodes across all models and all 11 dose values. Latent dynamics and noise are sampled from `phi∈[0.84,0.96]`, process SD `[0.08,0.18]`, and observation SD `[0.15,0.35]`.

## Models

`MODE_GAIN_FILTER` is the four-parameter state-conditioned update. `CONSTANT_GAIN_FILTER` is its direct context-free ablation. `GENERIC_RNN_1D` and `BILINEAR_RNN_1D` are learned recurrent comparators (four and five parameters). `KALMAN_ORACLE` is a task-aware reference supplied with each test episode's true dynamics and observation mapping; it is not a capacity-matched learner.

All learned policies receive identical training streams per seed, supervised latent-state targets, 200 Adam updates, and the same test streams. Train seeds are 43000–43029. The shared test stream uses a separately derived seed. Seed is the training replicate; episode is the paired evaluation unit nested within the crossed analysis.

## Analysis

The principal curve is `MSE(CONSTANT_GAIN_FILTER) - MSE(MODE_GAIN_FILTER)` at each `kappa`, with a crossed bootstrap over training seeds and test episodes (10,000 resamples, percentile 95% interval). Positive values favor mode gain. Report the entire dose curve, estimates at `kappa=+0.20`, `0`, and `-0.20`, and the linearly interpolated zero crossing where available. The original draft named ±0.25, which the 0.10-spaced grid does not contain; this was corrected to the nearest symmetric grid points before the outcome CSV was inspected, with no change to the runner or data. Also report generic recurrent and oracle comparisons. No universal significance or success claim is made from the curve; all estimates remain task-specific.

## Interpretation boundary

The dose response tests an artificial context-to-observation mapping motivated by, but not measured in, the RIM–AIY thermotaxis biology. It estimates an operating boundary for this model family. It does not show that worms encode sensor reliability in this exact form, establish a causal biological computation beyond published evidence, or demonstrate broad AI benefit. Earlier M2 results informed this design, so the study is exploratory.
