# M2 corollary-discharge placement transfer — contract

**Experiment ID:** `M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1`  
**Classification:** post-result exploratory artificial mechanism-transfer study. Related M2 source-model and AI outcomes were inspected before this contract. This is not an independent confirmation or biological validation.

## Question and biological scope

Does feeding a previous motor-state signal into a sensory-state update support state persistence differently from applying the same signal only as output-action inertia?

The biological anchor is bounded: Ji et al. report that RIM-dependent motor-state feedback is represented in AIY and supports sustained forward locomotion during *C. elegans* thermotaxis ([eLife 2021](https://elifesciences.org/articles/68848)). The source paper does not establish that motor state encodes sensory reliability. This experiment therefore tests feedback placement, not the earlier artificial reliability-mapping assumption.

## Task

Each episode is a partially observed binary state process `s_t ∈ {-1,+1}`. At each step, the state flips with hazard `h`; the observation is `x_t = s_t + ε_t`, with `ε_t ~ Normal(0, 1.25²)`. There is no action-dependent change to the latent process or the observation channel. Models emit binary decisions `a_t ∈ {-1,+1}`; after the first step, their own previous decision is the motor-state feedback input. Initial hidden state and previous action are zero.

Train on hazard `h=0.05`, using 30 training seeds (`88000..88029`), 256 independent training episodes per seed, and 256 steps per episode. Test on fresh episodes at hazards `h ∈ {0.01, 0.05, 0.20}`, with 512 episodes per training seed and hazard and 512 steps per test episode. Each seed/hazard's latent state and observation streams are shared across every policy. Training sequences are shared across learned models; each model runs its own closed-loop action state.

## Models

All three minimal placement/ablation models have three trainable scalar parameters and use the same `tanh` nonlinearity:

- **`SENSORY_SITE_CD`**: `z_t = tanh(ρ z_(t−1) + α x_t + β a_(t−1))`; `a_t = sign(z_t)`.
- **`OUTPUT_SITE_PERSISTENCE`**: `z_t = tanh(ρ z_(t−1) + α x_t)`; `a_t = sign(z_t + β a_(t−1))`.
- **`NO_FEEDBACK`**: `z_t = tanh(ρ z_(t−1) + α x_t + b)`; `a_t = sign(z_t)`.

Also report a two-unit generic tanh RNN (13 trainable parameters) receiving observation and previous action, and an exact Bayesian filter for the binary Markov state (task-aware, non-learned reference). The two placement arms have equal parameter counts and differ only in where the previous-action signal enters the computation. The no-feedback model matches parameter count with a static bias. The generic RNN and Bayes filter are stronger references, not capacity-matched comparisons.

## Training and inference

Train each learned model by sequence-level binary cross-entropy for 200 Adam updates, batch size 16, learning rate 0.01. During training and evaluation, the previous action is produced by that model's own current decision; the discrete action feedback is detached from gradient computation, while gradients propagate through the model's internal recurrent state. Use identical seed-indexed training streams, initialization seed rules, optimizer budgets, and held-out streams across models. No model-selection pilot or outcome-based tuning is allowed.

## Outcomes

Primary outcome: per-episode decision accuracy at the in-range hazard `h=0.05`. Primary contrast: `accuracy(SENSORY_SITE_CD) − accuracy(OUTPUT_SITE_PERSISTENCE)`, with positive values favoring sensory-site feedback. Estimate a paired crossed-bootstrap 95% interval over training seeds and shared test episode IDs (10,000 replicates, seed `20261022`). The training seed is the outer replicate; episodes are crossed within seed.

Secondary outcomes, reported separately by hazard: accuracy against `NO_FEEDBACK`, generic RNN and Bayes references; false-action-switch rate when the latent state does not switch; and mean number of steps after a true state switch until the policy's decision matches the new state. Do not pool hazards into a single score.

## Interpretation rules and limits

- A positive primary contrast supports only a performance difference between these two three-parameter placements in the stipulated synthetic telegraph-state task.
- A null or negative contrast means the sensory-site placement did not outperform the output-persistence control under this design; it does not refute the biological finding.
- A stable-regime benefit paired with a volatile-regime cost supports a task-persistence tradeoff, not a universal advantage.
- The two-unit RNN and Bayesian filter are important references; if they outperform the sensory-site arm, report that directly.
- The action/state process is synthetic and does not recreate thermotaxis, AIY physiology, or the Ji et al. model. No biological data are analyzed. No NMI-level novelty or general AI benefit is presumed.

## Provenance

This version is exploratory because M2 results have informed the question. Keep all outcomes, including adverse and null findings. Do not alter the architecture, hazards, primary endpoint, seeds, optimizer budget, or interpretation after this run. Later changes require a new experiment ID.
