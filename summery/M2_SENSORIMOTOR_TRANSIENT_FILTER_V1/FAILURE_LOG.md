# M2_SENSORIMOTOR_TRANSIENT_FILTER_V1 — failure analysis and lessons

## Decision

The frozen primary prediction failed in the specified direction. Sensory-site feedback did not reduce pulse-window error relative to output-site feedback; the paired `OUTPUT_SITE_1D − SENSORY_SITE_1D` contrast was −0.0921 (95% seed-block bootstrap interval [−0.1081, −0.0766]). This is an adverse result for this artificial implementation and task.

## What the result does and does not localize

The output-site model also had lower whole-episode MAE in the pulse and combined-stress conditions. The sensory-site model had lower mean command energy in the pulse condition (0.460 versus 0.576), suggesting a lower-effort / higher-error trade-off in this simulator; command energy was secondary and does not rescue the primary claim. No-feedback was worse on the primary endpoint than either feedback-placement model, which is compatible with motor feedback being useful here, but does not identify a biological computation or explain the performance difference between placements.

The task may reward direct use of actuator state at the command stage: the output-site term can adjust the next command using the current physical motor state, while the sensory-site term changes a latent estimate before a restricted scalar readout. That is a plausible explanation of this result, not an independently isolated cause. The architectures share parameter counts but differ in computation and optimization geometry; equal parameter count is not an expressivity or optimization match.

## Protocol and engineering lessons

- Freeze the endpoint's aggregation rule explicitly. Before execution, code review caught that equal-weight averaging across pulse events would not implement the contract's average over the union of eligible timesteps. The runner was corrected before the pre-run commit, and both contract and code now define the same union-based MAE.
- Evaluation-only references must be handled without assuming every arm has a trainable model. A `None` guard for fixed direct-sensor and privileged-oracle arms was added before the frozen commit; no outcome was produced by that issue.
- Keep the privileged target oracle labeled separately. Its low error comes from direct access to hidden target state and cannot be compared as a learned mechanism result.
- Report parameter count and compute separately. Matching four scalar parameters does not make the sensory-site and output-site models computationally equivalent.
- Preserve the negative result. Do not tune the pulse generator, model width, training duration, or primary endpoint after seeing this outcome and then present the modified task as confirmatory. Any follow-up must be separately versioned and explicitly exploratory or preregistered before execution.

## Scientific boundary

This task does not include AIY, RIM, biological neural recordings, RIM ablation, or the actual C. elegans thermotaxis regime. The result cannot be used to reject the source paper's biological mechanism. It says that this particular simple artificial translation did not outperform an output-site feedback placement under the frozen synthetic conditions.
