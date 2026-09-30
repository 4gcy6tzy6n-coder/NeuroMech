# M2 source-model gradient-reversal boundary — contract

**Experiment ID:** `M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1`  
**Classification:** exploratory source-derived computational stress test. Prior M2 biology, model, and artificial outcomes are known. This is not a new biological experiment, independent confirmation, or AI-transfer validation.

## Question

In the published Ji et al. Figure 7 model, does placing positive motor-state feedback at the sensory-processing state versus at the motor-output state change navigation performance when the preferred thermal-gradient direction reverses at different rates?

The biological source supports a bounded RIM-dependent motor-state feedback signal represented in AIY and a role in sustained forward locomotion during thermotaxis. The equation below is the published minimal model abstraction; the exact continuous update is not claimed to be directly measured in neurons.

## Source-derived task

Translate the corrected source model in `model/M2_FEEDBACK_SITE_SPECIFICITY_V5/source_model.py`, preserving `N=1500`, `T_MAX=200 s`, `dt=T_MAX/N`, 50 simulated agents per seed block, source sensory delay `0.5 s`, all neural gains/thresholds, heading transitions, and Gaussian noise scale `1`. Use the source-equivalent zero-based delayed-position index `max(0, t-delay_steps)`.

The scalar warm-gradient direction `g(t)` starts at `+1`. Conditions are stationary (`REVERSAL_INTERVAL=0`) or reverse sign every `40`, `20`, `10`, or `5` seconds. Direction reversal changes the sign of the spatial temperature slope while preserving the position-difference form of sensory input; it does not inject a spatially uniform temperature jump. Sensory drive is `I_s(t) = -1.5 * g(t) * (x(t)-x(t-0.5s)) * 1[M(t)>0]`. This is an artificial environmental stress condition, not an estimate of natural gradient dynamics.

## Frozen arms

Use three arms with the same source-model state variables, sensory input, noise, heading reset stream, and feedback coefficient magnitude `1`:

1. **`SENSORY_SITE_FB`**: add `+sigmoid(15*M)` to the AIY-like `dA/dt` input, as in the source model.
2. **`OUTPUT_SITE_FB`**: add `+sigmoid(15*M)` to the motor-like `dM/dt` input, with no sensory-site feedback. This is a placement control, not a calibrated persistence match.
3. **`NO_FEEDBACK`**: no positive feedback at either site.

Use common random numbers within each seed block across all 15 arm-by-environment cells. Do not fit coefficients or change the source equations based on outcomes.

## Outcomes and inference

**Primary endpoint:** environment-aligned displacement rate, computed as `-mean(g(t) * Δx(t)) / dt` and averaged over agents within each simulation seed block. Positive values indicate movement along the currently preferred warm direction.

**Primary contrast:** `SENSORY_SITE_FB − OUTPUT_SITE_FB` at the preselected 20-second reversal interval, summarized by the mean across 100 paired seed blocks and a 95% paired percentile-bootstrap interval (20,000 resamples, analysis seed `20261013`). The seed block is the resampling unit; the 50 agents and time samples within a block are not independent replicates.

Report all arms at all five reversal schedules. Secondary outcomes are local-progress rate in each schedule, source-style forward-state occupancy, mean forward-run duration, and transition recovery lag after each gradient reversal. Do not average across reversal schedules or replace the primary endpoint.

Simulation seed blocks are `20261014–20261113` (100 blocks); 50 agents per block; 1,500 steps per trajectory. Use one shared standard-normal noise matrix, heading-reset matrix, and initial headings per seed block.

## Interpretation rules

- A positive primary contrast supports only a source-derived simulated placement difference at this particular reversal interval and set of model parameters.
- If sensory-site feedback performs better in stationary/slowly changing gradients but worse under rapid reversal, report a persistence/adaptation tradeoff and its tested boundary.
- A difference from `OUTPUT_SITE_FB` does not isolate feedback placement if forward-state duration or occupancy differs; report these as model-dynamic differences, not a matched-persistence causal result.
- Neither positive nor negative outcomes validate the biological mechanism or establish AI benefit. The model has no learned controller or capacity-matched generic AI baseline.
- Retain every environment, arm, and adverse outcome. Any alternative gradient schedule or model is a new experiment ID.

## Provenance

The source file and prior corrected implementation are hashed in the run manifest. The new runner, contract, environment, Python/NumPy versions, seed plan, outputs, and SHA-256 checksums are archived. Independent verification checks row coverage, deterministic recomputation of the primary contrast, provenance hashes, and finite numerical outputs.
