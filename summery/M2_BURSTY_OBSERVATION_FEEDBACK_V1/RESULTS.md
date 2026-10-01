# M2 bursty-observation feedback placement — results

**Experiment ID:** `M2_BURSTY_OBSERVATION_FEEDBACK_V1`  
**Classification:** post-result exploratory artificial mechanism-transfer study. This is not biological validation or evidence of general AI benefit.

## Frozen primary result

At the long-burst evaluation condition (expected 8-step missing runs, 50% mean missingness), sensory-site feedback had mean tracking MSE `0.66276`, compared with `0.72209` for the four-parameter output-site control. The frozen primary contrast `MSE(OUTPUT_SITE) − MSE(SENSORY_SITE)` was **+0.05932** (paired crossed seed/episode bootstrap 95% CI **[+0.05201, +0.06673]**; all **24/24** training-seed means positive). The equal-parameter generic RNN was also worse (`0.72901`; contrast **+0.06625**, 95% CI **[+0.06000, +0.07283]**; 24/24 seeds positive).

The 8-unit GRU scored `0.67032`; its contrast against sensory-site feedback was **+0.00756** (95% CI **[−0.00258, +0.01818]**; 13/24 seeds positive). This interval includes zero. Under the frozen joint criterion, the experiment therefore **does not establish an advantage over the strong recurrent baseline**, even though the placement-specific contrast and equal-parameter generic-RNN contrast are positive. The full mechanism-transfer decision criterion was **not met**.

## Burst-duration range and secondary outcomes

Mean tracking MSE for `SENSORY_SITE` / `OUTPUT_SITE` / `NO_FEEDBACK` / `GENERIC_RNN` / `GRU_8` was:

| Mean missing-run length | Sensory-site | Output-site | No feedback | Generic RNN | GRU-8 |
|---:|---:|---:|---:|---:|---:|
| 2 steps | 0.54235 | 0.60004 | 0.60017 | 0.62758 | 0.55191 |
| 4 steps | 0.59881 | 0.65559 | 0.65661 | 0.67338 | 0.60190 |
| 8 steps | 0.66276 | 0.72209 | 0.72499 | 0.72901 | 0.67032 |

Realized missing fractions were `0.49995`, `0.50070`, and `0.49981` for the 2-, 4-, and 8-step expected gap conditions, respectively. Each episode’s same visibility/noise/target stream was reused across all five policies.

At the long-burst condition, mean action energy was `0.290` for sensory-site versus `0.519` for output-site. Mean post-gap recovery time (time to four consecutive steps with absolute error ≤0.25, capped at 24 steps) was `9.98` steps for sensory-site and `7.66` for output-site. Thus the lower overall MSE came with less aggressive action and slower recovery under this secondary definition; the primary result should not be restated as “faster recovery.”

## Interpretation and limits

In this synthetic target-tracking environment, placing previous motor state in the sensory-state update improved long-run average error over the equally parameterized output-placement, no-feedback, and generic one-state controls across the tested burst durations. The paired contrast against the 321-parameter GRU was unresolved because its 95% interval crossed zero; the evidence therefore does not distinguish the structured policy from that stronger baseline. Parameter counts and wall-clock fit costs differ for the GRU; it is a strong baseline, not a capacity-matched comparison.

The task’s Markov target, cursor, noisy relative observation, explicit visibility flag, and Markov burst mask are artificial. The burst condition is a computational stress test, not a biological property attributed to RIM–AIY. These outputs do not demonstrate a worm mechanism, biological-to-AI transfer, a general AI advantage, or NMI-level evidence. Training used one fixed protocol and no hyperparameter search; recovery is a secondary synthetic metric.

## Reproducibility

- Frozen protocol: [`CONTRACT.md`](CONTRACT.md)
- Figure and legend: [`M2_BURSTY_OBSERVATION_FEEDBACK_V1.svg`](../../data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical/figures/M2_BURSTY_OBSERVATION_FEEDBACK_V1.svg) · [`FIGURE_LEGEND.md`](FIGURE_LEGEND.md) · [rendered QA](../../data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical/figures/FIGURE_QA.md)
- Runner, analyzer, independent verifier: [`model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/`](../../model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/)
- Canonical outcomes and verification: [`data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical/`](../../data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical/)
- The independent verifier passed the complete `24 × 3 × 128 × 5 = 46,080` episode grid and 120 fitted-policy records, then independently recomputed the primary contrasts and bootstrap intervals.
- Mean training wall time per fit was 0.842 s (sensory-site), 0.841 s (output-site), 0.814 s (no feedback), 0.662 s (generic RNN), and 1.076 s (GRU-8) on the recorded machine; these values are descriptive and are not a compute-matched comparison.
- A full rerun in a fresh temporary directory reproduced `episode_results.csv` byte-for-byte (`a360507f…205501`); all training-result fields except runtime were identical.
