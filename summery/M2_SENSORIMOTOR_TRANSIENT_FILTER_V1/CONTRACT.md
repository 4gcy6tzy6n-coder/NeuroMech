# M2_SENSORIMOTOR_TRANSIENT_FILTER_V1 — motor feedback under transient and sustained sensory change

**Classification:** post-result exploratory artificial mechanism-transfer test. The biological M2 evidence and earlier artificial M2 results are known. The current experiment has a frozen within-study protocol, but it is not an independent confirmation or biological validation.

## Biological motivation and claim boundary

Ji et al. report that AIY represents thermosensory and motor-state information; the motor-state component depends on RIM, and RIM ablation allows temperature-related activity to propagate into downstream premotor circuitry while reducing the ability to sustain forward movement during positive thermotaxis. This motivates testing whether a motor-state signal inserted at a sensory-state update can suppress brief contradictory sensory transients while still allowing response to sustained changes. The paper does **not** specify the equations below, transient-noise statistics, actuator dynamics, or an AI benefit. This is a source-inspired computational test only.

## Question and directional hypothesis

In a binary sensorimotor tracking task with action-dependent motor inertia, does feeding the **actual previous motor state** into a sensory-state update reduce tracking error around brief contradictory sensory pulses compared with putting the same feedback parameter at the output? Does this placement preserve responses to sustained target-state changes? The directional primary hypothesis is lower pulse-window movement MAE for sensory-site than output-site feedback in `TRANSIENT_PULSE`.

## Task generator

Each episode is a 96-step sequence with a hidden target mode `z_t ∈ {−1,+1}`. The target changes sign with a condition-specific Bernoulli hazard. The sensory observation is `z_t + N(0, 0.25)` except during transient pulses, when its sign is contradicted (`−z_t + N(0, 0.25)`). Pulse onsets follow a Bernoulli process while no pulse is active. Actual motor state follows `m_t = 0.70 m_(t−1) + 0.30 u_(t−1) + ε_t`, with `ε_t ~ N(0, 0.03)`. The observed feedback available to the controller is this actual motor state, not its previous command.

Models train on the same generated mini-batches within each seed block, using hazard `0.02`, pulse-onset probability `0.02`, pulse duration uniformly sampled from one or two steps, Gaussian observation noise SD `0.25`, and motor noise SD `0.03`. Evaluation uses paired, held-out episodes under the following conditions:

| Condition | Target-switch hazard | Pulse-onset probability | Pulse duration |
|---|---:|---:|---:|
| `CLEAN_STABLE` | 0.01 | 0 | none |
| `TRANSIENT_PULSE` | 0.01 | 0.06 | 2 steps |
| `LONG_PULSE` | 0.01 | 0.03 | 4 steps |
| `SUSTAINED_SWITCH` | 0.05 | 0.02 | 2 steps |
| `COMBINED_STRESS` | 0.05 | 0.06 | 4 steps |

## Model arms

- `SENSORY_SITE_1D` (4 trainable parameters): `h_t = tanh(w_y y_t + w_h h_(t−1) + w_m m_t)`; command `u_t = tanh(w_u h_t)`.
- `OUTPUT_SITE_1D` (4 trainable parameters): `h_t = tanh(w_y y_t + w_h h_(t−1))`; command `u_t = tanh(w_u h_t + w_m m_t)`.
- `NO_FEEDBACK_1D` (3 trainable parameters): the sensory-site model without the motor-state input.
- `GENERIC_RNN_1D` (6 trainable parameters): biased scalar recurrent model with both observation and motor-state inputs to its hidden update.
- `GRU_8` (higher-capacity reference): an 8-unit GRU receiving the same observation and actual motor-state feedback.
- `DIRECT_SENSOR` (fixed reference): command from the current sensory sample only, with no learned memory or motor feedback.
- `TARGET_ORACLE` (privileged ceiling): uses the current hidden target and known actuator equation to issue a one-step-ahead motor command; it is not a biologically plausible model or a fair learned-model comparator.

The first five arms are learned models; the last two are evaluation-only references and receive no fitting. All learned models receive the same training-seed blocks, 100 Adam updates, batch size 32, sequence length 96, learning rate 0.01, MSE objective on actual motor state, and gradient clipping at 5. Parameters and wall-clock time are reported; equal updates are not treated as equal compute. Test episodes are shared across model arms within each seed block. The training and test random streams are disjoint.

## Outcomes and analysis

**Primary endpoint:** within each eligible test episode, average absolute movement-state error `|m_t − z_t|` over the union of transient-pulse windows and the following two steps, excluding pulse windows within three steps of a true target transition; then average eligible episodes within each seed block. The union prevents overlapping post-pulse windows from counting a timestep twice. Primary contrast is `OUTPUT_SITE_1D − SENSORY_SITE_1D` in `TRANSIENT_PULSE`; positive values favor sensory-site feedback. The unit for uncertainty is the paired training/task seed block (`n=20`), not episode or timestep. Report the paired mean and percentile bootstrap 95% interval over seed blocks (20,000 resamples).

Secondary outcomes are whole-episode motor-state MSE, sign accuracy, command energy, and latency to reacquire the new target after an actual target transition (first three consecutive steps with movement sign matching the new target; capped at 24 steps). Report every model and evaluation condition. Secondary outcomes are descriptive and are not used to redefine or replace the primary endpoint. No outcome-driven model selection, hyperparameter search, or exclusion is allowed.

The hypothesis is considered **supported only in the narrow computational sense** if the primary contrast favors sensory-site feedback and its 95% seed-block interval excludes zero; the report must still show switching latency and all strong-control results. No single positive comparison establishes biological equivalence, unique AI benefit, or broad generalization. If the primary interval includes zero or favors the output-site control, the result is null/adverse for this implementation. Because prior project outcomes are known and the generator is synthetic, even a positive result remains exploratory.

## Reproducibility

The runner emits episode-level metrics, seed-block summaries, fit metadata, and a manifest with hashes. The verifier independently recomputes episode-to-seed summaries, the primary contrast and bootstrap interval, verifies row completeness, parameter counts, and output hashes. A fresh full run must reproduce the episode metrics byte-for-byte before this round is published.
