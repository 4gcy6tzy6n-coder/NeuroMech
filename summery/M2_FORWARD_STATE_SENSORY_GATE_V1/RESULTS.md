# M2 forward-state sensory gate transfer V1 — results

**Status:** exploratory synthetic benchmark; not biological validation.

The task isolates a forward-state sensory gate inspired by the explicit sensory-input gate in the published Ji et al. thermotaxis circuit model. It is a computational abstraction, not a reproduction of the biological circuit.

## Results

The primary aligned-condition contrast `MSE(GENERIC_RNN_1D) − MSE(MODE_GAIN_FILTER)` was `+0.09431` (crossed 95% bootstrap interval `[+0.08790, +0.10126]`; 20/20 training-seed means positive). This is a comparison against one narrow, trained generic RNN.

The mechanism-specific interpretation does **not** follow from that contrast: the learned mode-gain filter and the context-free constant-gain filter had virtually identical MSE in every condition (aligned `0.423327` vs `0.423336`; independent `0.237313` vs `0.237313`; reversed `0.409638` vs `0.409630`). Thus the mode-conditioned gains did not produce a measurable benefit over a simpler context-free update in this benchmark. The mode-gain filter also had higher error than the task-aware Kalman reference in every condition (aligned `0.4233` vs `0.2610`; independent `0.2373` vs `0.0864`; reversed `0.4096` vs `0.2415`).

The observed RNN contrast therefore supports only that this hand-constrained filter parameterization trains better than this particular generic RNN on the chosen task family. It does not establish a useful state-gating inductive bias, biological transfer, or general AI benefit. The collapse to constant gain is the most important result and motivates revisiting the artificial task/model interface before any follow-up.

## Boundaries

The benchmark uses synthetic latent states, a synthetic binary context and synthetic observations. It cannot establish worm circuit causality or general AI benefit. The learned generic RNN is a narrow, one-state baseline; the task-aware Kalman comparator is not capacity matched. No biological endpoint was analyzed.
