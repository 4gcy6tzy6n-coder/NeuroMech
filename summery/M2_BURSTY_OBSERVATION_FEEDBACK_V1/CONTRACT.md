# M2 bursty-observation feedback placement — contract

**Experiment ID:** `M2_BURSTY_OBSERVATION_FEEDBACK_V1`  
**Classification:** post-result exploratory artificial mechanism-transfer study. Prior M2 simulations informed the task family and comparison. This is not confirmatory evidence, biological validation, or evidence of general AI benefit.

## Question and biological scope

In a closed-loop tracking task with the same average observation availability, does placing the previous motor command in the sensory-state update improve performance when missing observations occur in long bursts, compared with placing that signal at the output and with recurrent controls?

The biological motivation is the experimentally described RIM-to-AIY motor-state feedback in *C. elegans* thermotaxis (Ji et al., 2021, eLife, https://elifesciences.org/articles/68848). The artificial task tests an information-flow abstraction only. Neither bursty visual occlusion nor target tracking is asserted to be a biological feature of that circuit.

## Task

Each episode has a hidden target `s_t ∈ {-1,+1}` that switches with probability `1/40` per step. The controller has cursor position `x_t ∈ [-1,1]`, observes noisy relative error `s_t-x_t+ε_t` when visible (`ε_t ~ Normal(0, 0.25²)`), and moves by `0.08*m_t` per step with `m_t ∈ [-1,1]`. All policies receive the same visible/missing indicator and observation stream. Missing observations are zero-filled and explicitly marked; this avoids conflating a true zero error with an outage.

Visibility is a stationary symmetric two-state Markov process with visible probability 0.5. Its state persists with probability `1-q` and switches with probability `q`, giving a mean missing-run length of `1/q`. Training uses `q=0.25` (mean missing run 4 steps). Evaluation uses `q ∈ {0.50, 0.25, 0.125}` (mean missing runs 2, 4, and 8 steps); every condition has the same expected 50% missingness. This separates burst duration from average availability.

Use 24 training seeds `830100..830123`, 160 training episodes per seed, and 160 steps per episode. Train with 60 Adam updates, batch size 16, learning rate 0.01, identical task streams within seed and equal optimizer updates/tokens across fitted arms. Evaluation uses 128 held-out episodes per seed and visibility condition, paired across policies. Target, observation-noise, and visibility streams are generated from separate deterministic seed streams. Held-out episodes are not used for fitting or model selection.

## Policies

All small policies have four trainable scalar parameters and share the action nonlinearity `tanh(1.5·)`. Let `v_t∈{0,1}` be visibility and `y_t=v_t(s_t-x_t+ε_t)`.

- `SENSORY_SITE`: `h_t=ρh_(t−1)+αy_t+γ(v_t−0.5)+βm_(t−1)`; `m_t=tanh(1.5h_t)`.
- `OUTPUT_SITE`: `h_t=ρh_(t−1)+αy_t+γ(v_t−0.5)`; `m_t=tanh(1.5h_t+βm_(t−1))`.
- `NO_FEEDBACK`: `h_t=ρh_(t−1)+αy_t+γ(v_t−0.5)+b`; `m_t=tanh(1.5h_t)`.
- `GENERIC_RNN`: `h_t=tanh(w_hh h_(t−1)+w_y y_t+w_v(v_t−0.5)+w_m m_(t−1))`; `m_t=tanh(1.5h_t)`.
- `GRU_8`: an 8-unit GRU receives `(y_t, v_t, m_(t−1))` and maps its state to one action. This intentionally stronger, higher-capacity baseline is reported separately; it is not parameter matched.

All fitted policies minimize mean squared tracking error plus `0.002*m_t²` action cost through the differentiable environment. The GRU and small policies use the same training episodes, number of updates, batch size, and sequence length. No policy receives the hidden target, cursor position, or future visibility.

## Frozen analysis

**Primary endpoint:** held-out per-episode mean squared tracking error at the long-burst condition `q=0.125` (mean missing-run length 8), with training-distribution target hazard and 50% expected missingness.  
**Primary contrast:** `MSE(OUTPUT_SITE) − MSE(SENSORY_SITE)`; positive favors sensory-site placement. Estimate a paired crossed bootstrap 95% interval by resampling training seeds and then paired episode IDs (10,000 draws; seed `20261001`).

The placement-specific claim is supported in this artificial task only if the primary interval is entirely above zero and the paired 95% intervals for `GENERIC_RNN` and `GRU_8` minus `SENSORY_SITE` are also entirely above zero at the same long-burst condition. If it beats `OUTPUT_SITE` but not either recurrent baseline, the result is placement-specific but not evidence of an advantage over generic recurrence. If it fails the primary contrast, this experiment does not support sensory-site advantage. Secondary outcomes are the same contrasts at q=0.50 and 0.25, action energy, and recovery lag after visibility returns; they do not replace the primary decision.

Report every arm and condition, training-seed consistency, parameter count, updates, sequence tokens, wall-clock fit time, bootstrap intervals, and all failures. No outcome-based threshold, model, or condition change is allowed after execution begins. The outcome is an artificial-task result and cannot establish biological causality, worm behavior, or broad AI benefit.

## Reproducibility and artifacts

Contract, interpretation, and failure lessons are stored here; runner and independent verifier in `model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/`; episode-level outcomes, fit records, summary, and hashes in `data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical/`. The run must begin only after an empty-directory preflight pins the contract and runner hashes. Preserve any implementation correction and initial outputs as noncanonical rather than silently replacing them.
