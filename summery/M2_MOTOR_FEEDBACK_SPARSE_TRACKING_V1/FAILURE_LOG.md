# M2 motor-feedback sparse-sensation tracking V1 — failure and limitation log

## What this result does and does not support

- The sensory-site feedback model improved over the tested three-parameter one-state RNN and direct placement/ablation controls in the primary synthetic condition.
- This does not show that the RIM-to-AIY circuit implements the same update rule. The task uses a hidden telegraph target, cursor motion, and artificial sensory dropout rather than worm thermotaxis.
- The task-aware oracle was better in all nine test conditions. The result is not evidence that the proposed computation is optimal.
- The generic recurrent comparator has one hidden state. Stronger recurrent or adaptive controllers were not tested; a capacity-matched win against this small comparator is not a broad AI claim.

## Boundary and design risks

- At 75% missing samples with slow or training-rate target switches, output persistence/no feedback beat the sensory-site update. High target-switch hazard produced a more consistent benefit. Do not summarize all nine conditions as one general gain.
- Missing samples are represented as exact zeros. This leaves a point-mass cue that lets a model infer missingness from its input; the experiment does not test ambiguity between absent sensation and a true zero error.
- All learned arms received the same training pool, 100 updates, batch size, and sequence-step budget. They used arm-specific fixed initial parameter values and the generic controller remained at higher training loss. Thus the result may partly reflect optimization difficulty under the small fixed budget, not only representational value.
- The 32 training seeds are simulation clusters, not biological replicates. The 256 episodes per seed quantify held-out simulation variability and cannot be interpreted as animal sample size.
- The bootstrap interval is the frozen crossed resampling interval for this artificial benchmark. It does not address model-family selection, post-result project context, or multiplicity across earlier M2 experiments.
- A second complete run reproduced episode outcomes byte-for-byte; its wall-clock timings differed, as expected.

## Follow-up needed before a stronger claim

1. Compare with stronger recurrent models and multiple initialization/optimization families under matched training data and compute.
2. Replace exact-zero dropout with an ambiguous observation process and test whether the effect survives.
3. Freeze a new task family or independent test generator before execution; do not retune this model using the current nine-condition outcomes and call the result confirmatory.
4. Keep biological evidence and artificial-system evidence separate. Any claim of biological-to-AI transfer needs a defensible mapping from the measured neural computation to the artificial update, beyond resemblance of information flow.
