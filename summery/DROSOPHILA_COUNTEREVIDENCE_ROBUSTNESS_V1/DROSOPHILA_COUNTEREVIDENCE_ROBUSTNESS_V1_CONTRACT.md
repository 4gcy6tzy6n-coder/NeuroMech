# DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1 — frozen simulation contract

**Classification:** exploratory AI-side transfer stress test. This is not a biological experiment, a reanalysis of fly outcomes, or a replication of Tanaka et al.'s ANN results.

## Biological computation being abstracted

In Drosophila yaw stabilization, stationary textured patterns provide negative evidence against self-rotation and selectively suppress optomotor turning. The proposed artificial operation is to keep positive motion evidence and stationary-pattern counterevidence as separate inputs to a self-rotation estimate. This test abstracts the cue-integration computation only; it does not reconstruct Mi4 or any other fly circuit. The constructed sensor-feature task deliberately isolates whether that cue is sufficient; it is a diagnostic sanity test, not a natural-vision benchmark.

Primary source: Tanaka et al., *Current Biology* 2023, DOI 10.1016/j.cub.2023.10.011. The authors already trained ANNs to distinguish observer rotation from object motion and reported learned stationary-pattern evidence. The present test is therefore a narrow distribution-shift stress test, not a novelty claim for that result.

## Synthetic task

Each example is a 72-bin panoramic local-motion population. The label is `SELF_ROTATION` or `OBJECT_MOTION`. Both classes have the same fraction of moving bins and the same motion-direction statistics. In self-rotation examples, the remaining bins are uniform/low-contrast; in object-motion examples, they contain stationary high-contrast texture. Thus global flow and zero-flow counts alone are insufficient, while a contrast-qualified stationary-pattern signal can discriminate the classes. Detector errors are sampled independently per bin.

Training object/visible-texture coverage is 0.15–0.50. The held-out test coverage is 0.60, 0.75, or 0.90, with new environment seeds. A counterfactual test replaces the patterned stationary background with uniform or flickering background, removing the specific cue while retaining matched moving-bin statistics.

## Frozen models

- `MOTION_ONLY`: logistic classifier using moving-bin fraction, signed flow, and directional coherence; it does not receive a stationary-pattern feature.
- `ZERO_FLOW_CONTROL`: same motion features plus the fraction of zero-motion bins, matched for one additional scalar input.
- `COUNTEREVIDENCE`: same motion features plus the fraction of stationary, high-contrast patterned bins.
- `SHUFFLED_COUNTEREVIDENCE`: same architecture and feature count, and the stationary-pattern feature is independently permuted in both training and test examples within coverage/profile strata.

All models use the same training examples, L2 logistic objective, and fixed regularization. No test data are used for fitting or threshold choice. The trained counterevidence model is also evaluated after setting its stationary-pattern input to zero.

## Outcomes and inference

Primary: paired difference in balanced accuracy, `COUNTEREVIDENCE − MOTION_ONLY`, averaged equally across held-out coverage values under the patterned-stationary profile. Secondary outcomes are sensitivity, object-motion false-positive rate, ROC AUC, and the same contrasts under uniform/flickering counterfactual profiles. Independent unit: environment seed block; examples are clustered within blocks. Report percentile bootstrap intervals over 100 held-out seed blocks.

A positive result supports only the sufficiency/usefulness of this explicit cue in this constructed reduced-order task. It cannot establish a general AI advantage, correspondence to a particular neural cell type, or biological efficacy. The task intentionally creates a feature-identification problem and is a diagnostic pilot; it is not a benchmark of natural vision.
