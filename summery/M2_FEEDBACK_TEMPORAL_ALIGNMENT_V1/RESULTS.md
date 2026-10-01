# M2 feedback temporal-alignment experiment V1 — results

## Result

This exploratory artificial transfer experiment tested whether motor-state feedback must be contemporaneous with the controller's own motor state to help a sensory-state update reject transient contradictory observations. In the preregistered `SLOW_TRANSIENT` condition, the primary contrast was `LAG4_SENSORY − SELF_SENSORY` movement MSE across 32 paired training-seed blocks. The mean contrast was **−0.003858** (95% seed-block bootstrap interval **[−0.004294, −0.003409]**), so four-step-delayed self-feedback performed slightly better than current self-feedback. The frozen prediction that current alignment would win was not supported; the result was in the opposite direction.

Primary-condition mean movement MSE by arm:

| Arm | Mean MSE |
|---|---:|
| SELF_SENSORY | 0.366232 |
| LAG1_SENSORY | 0.362609 |
| LAG4_SENSORY | 0.362374 |
| CROSS_AGENT_YOKED_SENSORY | 0.375527 |
| SELF_OUTPUT | 0.355197 |
| NO_FEEDBACK | 0.375593 |
| GENERIC_RNN_1D | 0.340428 |
| GRU_8 | 0.302739 |

These secondary arm means are descriptive; the contract assigned inferential status only to the LAG4-versus-current primary contrast. The yoke preserved the contemporaneous population feedback distribution exactly in all 128 condition × seed-block checks. Its worse primary-condition mean than self-feedback is compatible with a recipient-contingency effect in this simulator, but neither the yoke nor that descriptive comparison establishes a distinctive biological computation. Output-site feedback, the generic recurrent controller, and GRU-8 all had lower primary-condition MSE than current sensory-site feedback. GRU-8 had the lowest mean MSE in each of the four tested conditions.

## Interpretation

The result does **not** support the hypothesis that zero-lag feedback is necessary or optimal in this task. A small advantage for lagged self-feedback is consistent with a possible smoothing or filtering role, but that is a post-result interpretation; the experiment did not isolate the responsible dynamics. The delay values are artificial perturbations and are not measurements of RIM-to-AIY conduction or synaptic latency.

This is a synthetic controller experiment based on a previously explored tracking task family. It does not test animals, establish biological causality, demonstrate an AI benefit over strong general-purpose systems, or validate transfer from the worm circuit. The result is useful as a boundary: in this implementation, temporal alignment itself did not explain a sensory-site advantage, and the biologically motivated low-dimensional controller remained behind stronger recurrent controls.

## Reproducibility

- 32 paired training-seed blocks; 8 controller arms; 4 test conditions; 128 episodes per arm × condition × block.
- 256 fitted models, 131,072 episode rows, and 1,024 seed-summary rows.
- Independent verifier passed after recomputing seed summaries and the primary contrast, checking all arm/condition coverage and parameter/update counts, confirming exact population-distribution matches for the yoke, and validating output/source hashes.
- The run completed on CPU. The machine-readable manifest records package versions, inputs, code hashes, output sizes, and output hashes.

## Evidence boundary

The primary effect is a paired simulation-seed result for this task generator and training procedure. It cannot be interpreted as an animal-level estimate or a biological delay effect. The GRU comparison is intentionally retained as a strong reference, but its 297 parameters are not capacity matched to the four-parameter placement arms. No cross-mechanism or project-level NMI claim follows.
