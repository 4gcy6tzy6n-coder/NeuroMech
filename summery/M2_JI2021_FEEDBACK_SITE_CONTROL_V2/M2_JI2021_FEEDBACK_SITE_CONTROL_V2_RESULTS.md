# Results — M2_JI2021_FEEDBACK_SITE_CONTROL_V2

## Experiment

A post-result follow-up to V1 asked whether the sensory-node feedback advantage persists against motor-only persistence after calibrating the latter more precisely on development simulations. The motor-only coefficient was selected from a frozen 0.700–0.800 grid in 0.001 steps, using development seeds 204000–204029. The held-out evaluation used seeds 204100–204199. No test outcomes were used for coefficient selection.

## Result

The selected motor-only coefficient was `0.723`. On development blocks, mean forward-run duration was 4.59519 s for sensory-node feedback and 4.58903 s for calibrated motor-only feedback.

On the 100 held-out seed blocks:

- Warm-direction index: sensory-node feedback 0.56775; motor-only feedback 0.47747; no-feedback 0.15499.
- Paired sensory-minus-motor warm-direction index: `+0.090275`; 95% seed-block percentile bootstrap CI `[+0.084015, +0.096588]`; positive in 100/100 blocks.
- Mean forward-run duration: sensory-node feedback 4.59013 s; motor-only feedback 4.62507 s.
- Paired duration difference: `−0.03494 s`; 95% seed-block percentile bootstrap CI `[−0.10304, +0.03445]`, consistent with close matching of the mean duration.
- Final mean warm-axis displacement: 33.77 (sensory feedback), 30.54 (motor-only), 5.56 (no feedback).

## Analysis

Compared with V1, the fine-grid independent calibration substantially improves the mean-run-duration match, and the held-out interval for the duration difference includes zero. The warm-direction difference remains positive in this source-model implementation. This supports a model-specific distinction between feedback placement and a single matched persistence summary (mean run duration).

It does not isolate feedback placement from every other dynamical difference: run-duration distributions, switching latency, hidden-state trajectories, and intervention resource/cost were not matched. A positive simulation contrast is not evidence of a new biological effect, does not prove a unique biological computation, and does not show an AI benefit. The exercise remains post-result and computational.

## Analysis unit and uncertainty

The unit is the simulation seed block; 50 agents within each block are clustered. Confidence intervals are paired percentile bootstrap intervals over the 100 seed blocks and describe Monte Carlo variability under the chosen model and seed distribution, not biological uncertainty.

## Provenance

The underlying dynamics derive from the Figure 7 navigation model in Ji et al. (2021), DOI 10.7554/eLife.68848: https://elifesciences.org/articles/68848v2 . This round uses the locally archived author source, Python implementation, and frozen experiment contract listed in the run manifest.
