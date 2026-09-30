# V1 implementation incident — invalid training/evaluation interface

**Disposition:** `INVALID_IMPLEMENTATION`; do not use V1 model comparisons as scientific evidence.

## What was wrong

The V1 runner generated `(target, context, observation)` but called `fit(seed, target, context)`. Inside `fit`, the target state was used as both the model input and the optimization target. Evaluation instead supplied the sensory observation, which was state-gated and noisy. Training and evaluation therefore used different input semantics, and the training procedure had access to the clean target as its input.

This is a data-flow implementation error, not a failed biological hypothesis. The V1 metrics and interpretation are invalid. The archived V1 output is retained for provenance and must not be cited as evidence that state-gating does or does not help.

## Correction

V2 passes the synthetic observation as model input and latent state as supervised target, matching the evaluation interface. V1 outcomes had been inspected before the correction, so V2 is an exploratory correction run rather than confirmatory evidence. The V2 record must preserve the same candidate task and report against both generic-RNN and context-free-filter controls.
