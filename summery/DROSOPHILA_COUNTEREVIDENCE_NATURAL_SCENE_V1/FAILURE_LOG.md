# Failure and limitation log — DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1

1. **No transfer advantage:** explicit stationary counterevidence did not improve the primary false-positive metric over the author-style CNN; the difference was effectively zero. Against the shuffled-cue arm, the point estimate favored the mechanism by less than one percentage point but the scene-group interval included zero.
2. **Severe coverage-shift error:** models trained only at 25%/50% moving coverage mislabeled about 81% of object-motion clips as self-rotation at 90% coverage. High self-rotation sensitivity was retained by the validation-selected thresholds, so this is not explained by the threshold trading sensitivity away.
3. **Small ablation change:** zeroing the stationary channel increased the 90%-coverage false-positive rate by about 2 percentage points. The fitted inhibitory gain was negative, but a sign-consistent weight alone is not evidence that the mechanism is useful.
4. **Weak motion baseline:** local 1D patch-correlation coherence produced near-ceiling object-motion false positives. It is not a strong computer-vision comparator and must not be described as one.
5. **Renderer scope:** the benchmark reduces panoramic scenes to a single 72-position horizontal row and creates moving-object clips synthetically. It lacks 2D optic flow, depth, camera translation, real video motion, and biological neural/behavioral outcomes.
6. **Novelty boundary:** the source study itself tested artificial neural networks that detect stationary patterns. This benchmark is a stress test of a closely related computation, not a novel neural architecture.
7. **Inference boundary:** 30 independent held-out scene groups support only a limited scene-generalization estimate. Clips within a scene are clustered; clip-level AUCs are descriptive and are not used as inferential sample sizes.

No outcome was removed or rerun. The fixed contract and all three learned arms are archived with checkpoints, predictions, split assignments, source hashes, and this failure record.
