# M2 sequential binary-decision task V1

**Experiment ID:** `M2_SEQUENTIAL_DECISION_V1`
**Classification:** post-result exploratory artificial transfer test. Earlier M2 abstract-filter results are known; this uses a different task objective and new seeds. It is not biological validation or confirmatory evidence.

## Question

Does state-conditioned sensory integration improve terminal binary decisions over a constant-gain update when a motor-state-like context marks which observations carry target evidence? Does the effect change if that context-evidence relation is weakened or reversed?

## Task family

Each episode has a static hidden target `s ∈ {-1,+1}` and a 32-step binary context sequence `q_t ∈ {-1,+1}` that switches with probability 0.25. At each step, the scalar cue is `y_t = H(q_t) * 0.18*s + 0.7*epsilon_t`, with independent standard-normal noise. Training uses ALIGNED `H(+1)=1,H(-1)=0`; evaluation tests ALIGNED, INDEPENDENT (`H=0.5` for both states), and REVERSED (`H(+1)=0,H(-1)=1`). The task is sequential evidence accumulation and terminal left/right decision, not continuous AR(1) state tracking. The context-to-evidence relationship is imposed by this synthetic generator and is not claimed as a measured property of the biological circuit.

## Models

- `MODE_GAIN_FILTER`: four-parameter context-conditioned prediction-error update.
- `CONSTANT_GAIN_FILTER`: three-parameter context-free prediction-error update.
- `LINEAR_BILINEAR_RNN`: five-parameter bounded linear update with `y`, `q`, `y*q`, `h`, and `q*h` terms.
- `BAYES_ORACLE`: uses the known cue distribution and evaluation mapping to calculate exact posterior log-odds; it is a task-aware reference, not a learned/capacity-matched model.

Learned models train by per-step MSE to the episode's hidden target using Adam (`lr=0.02`), gradient clipping at 5, 250 updates, and minibatches of 16 sequences. Training set sizes are 16, 64, 256, and 1024 episodes, with 128,000 sequence-step tokens per fit. Twenty paired seeds `73000..73019`; 512 held-out episodes per seed and condition; the task seed is the inferential unit. Models share the same training episode pools, minibatch-index streams and held-out target/context/noise streams within a seed.

## Outcomes

Primary outcome: terminal decision accuracy. Primary contrast: `accuracy(MODE_GAIN_FILTER) − accuracy(CONSTANT_GAIN_FILTER)`, averaged equally over the four training-set sizes in ALIGNED evaluation; positive favors state-conditioned integration. Report paired seed-bootstrap 95% interval, positive-seed count, per-size outcomes, terminal MSE and Brier score. Report INDEPENDENT and REVERSED separately. The bilinear update and Bayes oracle are references; conditions are not pooled.

## Interpretation boundary

This tests whether a state-conditioned integration operation carries over from continuous estimation to a different synthetic sequential-decision task. It can support only this task, generator, training budget and comparator set. It cannot establish biological-to-AI transfer, because the context/evidence mapping is artificial; nor does it establish broad AI performance or publication readiness. Preserve null, adverse and oracle-dominant outcomes without tuning.
