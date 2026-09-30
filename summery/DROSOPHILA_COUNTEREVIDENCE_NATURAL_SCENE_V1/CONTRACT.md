# DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1 — frozen exploratory transfer contract

## Status and lineage

This is a post-result exploratory artificial-transfer benchmark. It follows the reduced-order feature pilot `DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1`, whose outcomes are already known. It is not an independent biological replication, a reanalysis of fly outcomes, or a confirmatory preregistration. No result from this round may revise or overwrite the V1 record.

## Biological computation being abstracted

Tanaka et al. (2023) report that stationary retinal patterns act as negative evidence against self-rotation and can suppress yaw-stabilization behavior; their neural recordings/manipulations support a stationary-pattern-sensitive route distinct from local motion/optic-flow detectors. The transfer hypothesis is narrow: an explicit estimate of textured, stationary visual evidence may improve discrimination of global observer rotation from independently moving scene content, especially when moving content occupies much of the field.

This experiment tests an engineering analogue on rendered image sequences. The scenes and motion sequences are not biological data. Source study code also contains ANN models, so a CNN comparison is an adapted baseline, not a novel model claim by itself.

Primary source: Tanaka et al., *Current Biology* (2023), DOI `10.1016/j.cub.2023.10.011`.

## Image source and split

Use the JPEG panorama previews from HDRIHaven, Zenodo record `10.5281/zenodo.1285800` (v1.0.1). The record describes 201 full-azimuth panoramas and states that source images are CC0/public domain. Download only `.preview.jpg` files; do not download the multi-gigabyte 16K HDR files.

Before rendering or model execution, group preview files by the filename scene slug after removing the numeric image index and a trailing numbered capture suffix (so named capture variants stay together). Sort those group slugs by SHA-256 of `DCE-NATURAL-2026|<slug>`; assign the first 70% of groups to train, the next 15% to validation, and the remainder to test. No panorama group may occur in more than one split. All reported uncertainty must resample held-out scene groups, not individual rendered clips.

## Input and task

Each example is a 30-frame, 72-position panoramic grayscale sequence. Crop the equirectangular preview to the central 105° elevation band, resize to 20×72, then sample a horizontal row per clip. Render two balanced classes from each panorama:

- `GLOBAL_ROTATION`: the full panorama row moves with a smooth, signed horizontal shift sequence.
- `LOCAL_OBJECT_MOTION`: a crop from another elevation band of the same panorama is translated over a stationary background row. The moving crop spans a sampled proportion of the 72 positions.

Generate 8 clips per scene × class × training coverage; training coverages are only 0.25 and 0.50. Validation uses 8 clips per scene × class at 0.50. Test uses 10 clips per scene × class × coverage at fixed coverages 0.25, 0.50, 0.75 and 0.90, so 0.75/0.90 are coverage-shift evaluations. Use separate train/validation/test seed namespaces starting at 100,031,001 / 200,041,001 / 300,051,001 and disjoint from model seeds. Alternate direction by replicate index so each condition is exactly balanced. Object crop location, source row, and smooth speed profile are randomized with frozen seeds. Standardize each frame across horizontal positions, as in the author preprocessing. Preserve raw scene IDs and motion seeds in every output row. This is a controlled renderer benchmark, not a claim that the generated clips are natural videos.

## Frozen arms

1. `FLOW_FIELD_COHERENCE`: non-learning local displacement baseline. For every adjacent frame pair, estimate local 1D displacement by maximizing patch correlation over ±3 bins; score is the fraction of valid local estimates agreeing on the modal displacement.
2. `AUTHOR_STYLE_CNN`: source-correspondent small CNN reimplementation: 30 temporal channels, 4 circularly padded width-3 convolution filters, ReLU, 2-channel pointwise readout, and sum over horizontal position. This follows the author repository's `CNNSpaceInv` design; it is not their published trained model.
3. `COUNTEREVIDENCE_MODEL`: same CNN plus one explicit stationary-pattern input feature. A bin counts as stationary textured evidence when its mean absolute temporal difference is below 0.18 and mean absolute spatial gradient exceeds 0.10. Its scalar contribution to the self-rotation logit is constrained inhibitory (`−softplus(parameter)`).
4. `SHAM_CHANNEL_CNN`: same model and parameter count as arm 3, but its stationary-evidence values are shuffled within scene-group × coverage strata in training, validation, and test, removing episode-level alignment while preserving broad coverage dependence.

No external pretrained weights. Learned arms share training examples, Adam (`lr=0.001`, `weight_decay=0.0001`), batch size 64, maximum 15 epochs, patience 3 on validation cross-entropy, and the same three initialization seeds (`61001`, `61002`, `61003`). Select each arm's decision threshold on validation as the highest score threshold retaining at least 90% global-rotation sensitivity. `COUNTEREVIDENCE_MODEL` and `SHAM_CHANNEL_CNN` have exactly the same architecture and parameter count. Record counts and best validation epochs.

## Outcomes

Primary metric: object-motion false-positive rate at a threshold selected on validation to achieve at least 90% global-rotation sensitivity, evaluated on held-out test panoramas at 0.75 and 0.90 moving coverage. Primary paired contrasts are `COUNTEREVIDENCE_MODEL` minus each of `AUTHOR_STYLE_CNN` and `SHAM_CHANNEL_CNN`; negative values favor counterevidence. Estimate 95% intervals by bootstrap over held-out scene groups, keeping all images/clips from each group clustered.

Secondary metrics: balanced accuracy, ROC-AUC, sensitivity, false-positive rate by coverage, and results with the explicit stationary channel ablated. Do not pool test clips as independent samples. The signed inhibitory gain is not polarity-reversed because its sign is constrained by the mechanism definition.

## Interpretation and decision rules

- `TRANSFER_SIGNAL`: counterevidence has lower primary false-positive rate than both learned controls, the scene-group-clustered 95% intervals exclude zero, and global-rotation sensitivity remains at least 0.90.
- `NO_TRANSFER_ADVANTAGE`: primary contrast is zero or favors a control with sufficiently narrow image-clustered intervals.
- `INCONCLUSIVE`: uncertainty spans both meaningful benefit and harm, or scene count/training stability is inadequate.
- `INVALID`: image leakage across splits, corrupted input provenance, class/render imbalance, or non-finite/failed model output.

A `TRANSFER_SIGNAL` would support only a controlled synthetic image-rendering result on this panorama set. It would not establish biological fidelity, performance on real videos, superiority to all computer-vision systems, causal generalization, or publication readiness. The paper's own ANN analysis and synthetic rendering limit novelty and external validity.

## Reproducibility outputs

Save source manifest and image checksums; renderer/config; per-example predictions; per-scene/coverage metrics; trained model specifications and parameter counts; bootstrap contrasts; run manifest; and a failure log. Store code under `model/DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1/`, outputs under `data/results/DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1/`, and interpretation under `summery/DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1/`.
