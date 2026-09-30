# Results — DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1

## Classification

Completed exploratory, post-result artificial-transfer benchmark. It follows the reduced-order feature pilot and is outcome-informed at the project level. It is not a confirmatory test, biological replication, real-video evaluation, or an NMI-level result.

## Data and execution

Acquired 201/201 CC0 HDRIHaven panoramic JPEG previews from Zenodo record `10.5281/zenodo.1285800` v1.0.1 (154,737,391 bytes); each download matched Zenodo's per-file MD5 and has a recorded local SHA-256. Deterministic filename-family grouping produced 141 training, 30 validation, and 30 test scene groups with no overlap. The held-out test contains 2,400 rendered clips across four motion-coverage levels. Each input is a 30-frame sequence sampled at 72 positions from one horizontal line in a natural panoramic image; local-object motion was rendered over a stationary row from the same panorama.

Three seeds each were used for an author-style spatially invariant CNN, the same CNN with an explicit inhibitory stationary-pattern feature, and a parameter-matched shuffled-cue control. The CNNs have 374 parameters; the two cue-channel arms have 375. A local-flow-coherence baseline was also evaluated. Thresholds were chosen on validation for at least 90% self-rotation sensitivity.

## Primary results

At 75%/90% moving-object coverage, the counterevidence model's object-motion false-positive rate differed from the author-style CNN by `0.0000`; the scene-group bootstrap 95% interval was `[-0.0100, +0.0100]` over 30 held-out groups. Versus the shuffled-cue CNN, the difference was `-0.0067` (lower is better), with interval `[-0.0217, +0.0067]`. Both intervals include zero, so the frozen `TRANSFER_SIGNAL` criterion was not met.

The author-style CNN's object-motion false-positive rate rose from 0.020 at 25% coverage to 0.157, 0.527, and 0.813 at 50%, 75%, and 90%. The counterevidence model was nearly identical: 0.020, 0.150, 0.523, and 0.817. At 90% coverage, its global-rotation sensitivity remained 0.960, but it incorrectly called 81.7% of local-object-motion clips global rotation. Removing the explicit cue raised that FPR only from 0.817 to 0.837 at 90% coverage. The constrained inhibitory gain was negative for all three seeds (approximately -0.32), but its benefit was small and inconsistent across coverage levels.

The local-flow-coherence baseline performed poorly at the chosen validation sensitivity threshold: its object-motion false-positive rate was 0.937–1.000 across test coverage. It is a deliberately small 1D local-correlation baseline, not a state-of-the-art dense optical-flow system. Its result is retained as a weak baseline and cannot support superiority claims.

## Interpretation

This experiment did not show a measurable transfer advantage for explicitly adding a stationary-pattern counterevidence channel over the author-style CNN or the parameter-matched shuffled-cue arm. The CNN likely already learned enough temporal/spatial evidence to approximate the explicit cue; alternatively, the one-dimensional renderer and chosen stationary detector may not capture the source computation well. The ablation result is small, and the sham interval spans zero.

The dominant finding is a coverage-shift failure: all learned arms trained at 25%/50% object coverage produced many false self-rotation calls when the moving object covered 75%/90% of the sampled field. This identifies a concrete boundary condition for any later transfer claim. The experiment used real natural-scene pixel values but synthetic one-dimensional motion rendering. It did not use full 2D video, real camera/observer trajectories, biological measurements, or the authors' trained CNN weights. Tanaka et al. already include an ANN analysis, limiting novelty. This result is an engineering stress test, not evidence that the biological computation improves general AI.

## Decision

`NO_TRANSFER_ADVANTAGE_OBSERVED` in this rendered benchmark; `HIGH_COVERAGE_OOD_FAILURE` for all learned arms. This is not an equivalence claim, because a smallest effect of interest was not set for the exploratory follow-up. No biological hypothesis is refuted.

## Reproduction

- Protocol: [`CONTRACT.md`](CONTRACT.md)
- Acquisition and local SHA-256 manifest: `data/raw/drosophila_counterevidence_natural_scenes/source_manifest.json`
- Model and acquisition scripts: `model/DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1/`
- Predictions, split ledger, metrics, figure, and run manifest: `data/results/DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1/`
