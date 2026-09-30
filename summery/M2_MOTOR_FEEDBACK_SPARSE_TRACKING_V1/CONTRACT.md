# M2 motor-feedback sparse-sensation tracking — contract

**Experiment ID:** `M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1`

**Classification:** post-result exploratory artificial mechanism-transfer study. Prior M2 source-model and artificial results informed this question. This is not confirmatory evidence, biological validation, or evidence of general AI benefit.

## Question and biological anchor

Does placing a motor-state signal in a sensory-state update help a closed-loop controller track an external target when its observations are intermittent, compared with placing the same signal only in the action output, omitting it, or using a parameter-matched generic recurrent controller?

The bounded biological anchor is the published RIM-to-AIY motor-state feedback result in *C. elegans* thermotaxis: motor-state information reaches a sensory-processing interneuron and influences sensory representation/locomotor persistence (Ji et al., 2021, eLife, https://elifesciences.org/articles/68848). This experiment tests an abstract information-flow arrangement. Its one-dimensional target-tracking task is not thermotaxis, its observation dropouts are artificial, and it does not claim that worms implement these equations.

## Environment

Each episode has a target state `s_t ∈ {-1,+1}` that switches with a Markov hazard. The agent has cursor position `x_t ∈ [-1,1]` and receives a noisy relative-position observation `y_t = s_t - x_t + ε_t`, with `ε_t ~ Normal(0, 0.25²)`. With probability `p_missing`, the sensory sample is occluded and `y_t=0`; the sensory channel has no additional dropout flag. The agent emits motor command `m_t ∈ [-1,1]`; cursor position advances by `0.08*m_t` and is clipped to `[-1,1]`. Target state is shared across model arms within each seed/condition/episode. The model sees current relative sensation and its own previous motor command, but not target state, cursor position, or occlusion indicator.

Training condition: target hazard `1/120`, `p_missing=0.50`, observation SD `0.25`; 32 training seeds `410000..410031`, 256 training episodes per seed, sequence length 240. Evaluation uses 256 held-out episodes per training seed and the crossed hazard/missingness grid `{1/240, 1/120, 1/40} × {0.25, 0.50, 0.75}` at the same observation SD. Episode IDs and exogenous target/observation random streams are paired across all arms.

## Models

All learned arms have exactly three trainable scalar parameters; the action nonlinearity and gain are fixed across them.

- `SENSORY_SITE_FEEDBACK`: `h_t = ρh_(t−1) + αy_t + βm_(t−1)`; `m_t=tanh(1.5h_t)`. The prior motor command enters the state used to interpret current sensation.
- `OUTPUT_SITE_PERSISTENCE`: `h_t = ρh_(t−1) + αy_t`; `m_t=tanh(1.5h_t + βm_(t−1))`. The same motor signal enters only the output.
- `NO_FEEDBACK`: `h_t = ρh_(t−1) + αy_t + b`; `m_t=tanh(1.5h_t)`. The third parameter is a static bias.
- `GENERIC_RNN_1H`: `h_t=tanh(w_hh h_(t−1)+w_y y_t+w_m m_(t−1))`; `m_t=tanh(1.5h_t)`. It also has three trainable parameters and can learn a generic recurrent sensorimotor interaction.
- `ORACLE_RELATIVE_ERROR`: uses the true current `s_t-x_t` and the common fixed action rule. It is a task-aware upper reference, not a learned or capacity-matched model.

Learned models start from fixed, arm-specific raw parameter values; training seed variation comes from the paired target/noise/dropout streams. Learned arms receive identical training episodes, optimizer updates, batch sizes, and held-out conditions. Training minimizes closed-loop mean squared target distance plus `0.002*m_t²` action cost, through the differentiable cursor and controller recurrence. The oracle is not trained.

## Analysis plan

Primary endpoint: per-episode mean squared tracking error at the training condition (`hazard=1/120`, `p_missing=0.50`). Primary contrast: `MSE(GENERIC_RNN_1H) − MSE(SENSORY_SITE_FEEDBACK)`, where positive favors the sensory-site mechanism. Estimate a paired crossed-bootstrap 95% interval over training seeds and held-out episode IDs using 10,000 resamples and RNG seed `20261018`. Report model means, training-seed consistency, parameter/update/token counts, and the primary interval. The other eight condition-specific model contrasts, recovery delay after target flips, and action energy are secondary and are not pooled.

The archive must also report the placement contrast against `OUTPUT_SITE_PERSISTENCE` and the ablation contrast against `NO_FEEDBACK`; a primary win against the generic RNN alone does not establish that feedback placement caused it. If the sensory-site arm does not beat both direct controls, the proposed mechanism-specific AI benefit is unsupported in this experiment. If the generic model wins, retain that as evidence that this three-parameter hand-specified update was not useful under the tested conditions. No threshold or model may be changed after inspecting these outcomes.

## Reproducibility and scope

Save episode-level data, training traces, summary, and source hashes under `data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/`; keep model and independent verifier under `model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/`; retain interpretation and failures in this directory. The verifier checks the complete seed × condition × episode × arm grid, the frozen model sizes and training protocol, and independently recomputes primary summaries and bootstrap intervals.

Even a positive result supports only this artificial task and its tested dropout/hazard range. It does not establish a causal biological mechanism, test a living worm, compare with all modern adaptive controllers, or demonstrate general AI benefit. A later independent replication or broader task-family comparison would be needed for stronger claims.
