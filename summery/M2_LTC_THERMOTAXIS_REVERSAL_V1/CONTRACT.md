# M2_LTC_THERMOTAXIS_REVERSAL_V1 — exploratory mechanism-transfer contract

## Scientific question and prior-art boundary

Does routing a motor-state signal into the sensory-state update of a liquid time-constant network improve control of a thermal setpoint when the agent's own motion changes the sensory signal and the environmental gradient reverses?

The biological motivation is bounded to the published *C. elegans* thermotaxis finding that RIM-dependent motor-state information changes AIY sensory representation and affects persistence of forward motor state (Ji et al., 2021, https://elifesciences.org/articles/68848). The proposed computation is an abstraction from that evidence, not a claim that the worm estimates gradient sign with the exact equations below. The artificial plant is a thermotaxis-like task: movement through a temperature field changes the next sensory observation.

Classical efference-copy and gaze-centered spatial updating already have extensive prior art. This study does **not** claim to discover motor-to-sensory feedback or liquid neural networks. It asks whether the source-motivated placement of motor context in a sensory-state update has a task-specific advantage inside an LTC controller under explicit causal self-motion and gradient-reversal conditions. See Sommer & Wurtz (2008) for corollary discharge, the 2016 gaze-centered target-updating state-space/RBF model (doi:10.3389/fnsys.2016.00039), and Hasani et al. (AAAI 2021, https://ojs.aaai.org/index.php/AAAI/article/view/16936) for LTCs.

This is a post-result exploratory study: prior M2 source-model and artificial-task outcomes informed the mechanism, task family, and comparison arms. It cannot serve as independent confirmation or establish NMI-level novelty by itself.

## Task

An agent moves along a one-dimensional thermal field toward a preferred isotherm. The field is `T(x,t) = T_pref + s_t * (x - x_pref)`, where the slope `s_t` has a fixed magnitude and a sign that reverses stochastically. The agent receives noisy temperature error relative to `T_pref`, with Markov observation gaps. Its action changes its position; therefore its own motor command changes the next sensory input. The target is the fixed preferred isotherm `x_pref`, and the primary task outcome is mean squared distance from that isotherm.

- Horizon: 128 steps per episode; action speed and position bounds are fixed.
- Training uses 96 episodes per seed at gradient-reversal hazard `1/40` and observation-state transition probability `q=0.25`.
- Evaluation uses paired fresh episodes (128 per training-seed block × model × condition) at reversal hazards `1/80`, `1/40`, and `1/20`, with the same observation process.
- Initial position, preferred-isotherm position, slope magnitude, sensor noise, reversals, and observation gaps are independently generated per episode; all arms within a seed/condition share the same exogenous draws.
- Train with the same 120 optimizer updates, batch size 8, Adam learning rate 0.005, sequence length, and train episodes for each learned arm. Report measured training time and parameter counts; equal update count is not equal FLOPs.

## Models and causal controls

All LTC arms use the same eight-unit LTC state, parameter tensors, readout, initialization family, optimizer, training sample, and update budget. The LTC state equation is the bounded conductance-style form `dh/dt = -(1/tau + f(h, input)) h + f(h, input) A`, integrated with four fixed semi-implicit Euler unfolds per task step. It is an equation-level LTC implementation, not a claim of bitwise reproduction of `ncps`.

- `LTC_SENSORY_SITE`: previous self motor command enters the input current for four designated sensory-state LTC units.
- `LTC_OUTPUT_SITE`: previous self motor command enters only the policy readout/action equation.
- `LTC_NO_FEEDBACK`: previous motor command is not routed into the LTC state or readout.
- `LTC_DENSE_FEEDBACK`: previous self motor command enters every LTC unit's input current.
- `LTC_SENSORY_YOKED`: motor input to the four sensory-state units is cyclically reassigned across simultaneous episodes, preserving the per-step batch distribution while breaking recipient-specific contingency.
- `GRU_4`: a capacity-near-matched generic recurrent controller (trainable parameter count reported exactly).
- `GRU_8`: a higher-capacity generic recurrent reference.
- `GRADIENT_SIGN_ORACLE`: a non-trained task-aware reference given the current true gradient sign; not included in learned-model contrasts.

All models receive the same observed temperature error and visibility indicator. LTC arms share all trainable tensors; route placement is the intervention. The generic GRUs receive previous motor command as an ordinary recurrent input. The oracle's extra information is disclosed.

## Outcomes and analysis

- Primary endpoint: episode mean squared distance from the preferred isotherm, averaged first within episode and then within the independent training-seed block.
- Primary condition: evaluation gradient-reversal hazard `1/20` (faster than the training hazard).
- Primary contrasts: each comparator's position MSE minus `LTC_SENSORY_SITE` MSE. Positive favors sensory-site feedback. Report contrasts against output-site, no-feedback, dense-feedback, yoked sensory feedback, GRU-4, and GRU-8.
- Secondary endpoints: absolute distance, temperature-error MSE, action energy, fraction of steps within two position units of the preferred isotherm, and time to return to that band after a gradient reversal.
- Independent unit: training-seed block (`32` blocks); episodes are nested observations. Use paired percentile bootstrap resampling seed blocks (20,000 resamples; seed `20261003`). Report every model and reversal hazard.
- No tuning on test episodes. No biological endpoint or claim is derived from the simulated outcomes.

## Interpretation rules

The experiment supports only a bounded artificial computation result if sensory-site placement beats the output-site, no-feedback, and yoked controls on the primary task-native endpoint. Beating GRU-4 but not GRU-8 indicates a capacity-limited advantage, not broad superiority. Beating neither placement controls nor the yoked control means the proposed self-contingent sensory computation is not supported in this implementation. Metric trade-offs and failure conditions remain part of the result. No outcome alone establishes novelty or NMI readiness.

## Artifacts

- Runner: `model/M2_LTC_THERMOTAXIS_REVERSAL_V1/run_experiment.py`
- Verifier: `model/M2_LTC_THERMOTAXIS_REVERSAL_V1/verify_results.py`
- Results: `data/results/M2_LTC_THERMOTAXIS_REVERSAL_V1/`
- Interpretation and failure lessons: this directory.
