# Results — DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1

## Classification

Exploratory, reduced-order synthetic cue-sufficiency test. This is not a natural-image benchmark, a reanalysis of fly outcomes, or evidence of general AI advantage.

## Result

Training used 30 seed blocks with moving/visible-texture coverage 0.15–0.50. Testing used 100 independent blocks at held-out coverage 0.60, 0.75, and 0.90. Under the `PATTERNED_STATIC` profile, balanced accuracy averaged across those test coverages was:

- Motion-only logistic: approximately 0.503.
- Zero-flow control: approximately 0.503.
- Contrast-qualified stationary-counterevidence logistic: approximately 0.996.
- Shuffled-counterevidence control: approximately 0.505.

The primary paired contrast, counterevidence minus motion-only, was `+0.4936` balanced-accuracy points (95% seed-block bootstrap interval `[+0.4873, +0.4997]`; positive in 100/100 seed blocks). The counterevidence model's accuracy dropped to approximately 0.50 when its stationary-pattern input was ablated.

The profile-specific result was sharply bounded. Replacing patterned stationary backgrounds with uniform or flickering backgrounds removed the cue and returned balanced accuracy to approximately 0.50. However, the fitted model then produced object-motion false-positive rates near 1.0: because training associated detectable stationary texture with object motion, the model confidently called object motion `SELF_ROTATION` when that feature disappeared. This is a clear distribution-shift failure, not robustness.

## Interpretation

The task was deliberately constructed so both classes have matched motion direction and moving-bin statistics, while a textured stationary field is the distinguishing feature in the patterned condition. The result therefore confirms that an explicit stationary-pattern channel is sufficient for this narrow feature-level problem and that removing or shuffling it destroys performance. The large effect is a manipulation check built into the generator, not a new biological or AI discovery.

A generic classifier receiving the same contrast-qualified stationarity feature can implement the same decision; this experiment does not show that the biological organization is superior to a generic learned model. It also does not test visual pixels, natural scenes, camera motion, real object boundaries, or the behavioral selectivity reported in flies. The next substantive test needs raw visual inputs and strong motion-estimation baselines under naturalistic domain shift.

## Provenance

Biological background: Tanaka et al., *Current Biology* 2023, DOI 10.1016/j.cub.2023.10.011, which reports stationary retinal patterns as negative evidence against self-rotation and also includes ANN modeling. The authors' public self-motion ANN repository was inspected at pinned commit `75a7051a0e310311b9295afe0a2b5c68f25eba9d`. The 13.80 GB Dryad archive was not downloaded or used; no biological outcome data entered this synthetic experiment.
