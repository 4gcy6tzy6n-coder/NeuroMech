# CROSS_MECHANISM_CONTEXT_MEMORY_V2 — results and interpretation

## Status

This is a post-result exploratory artificial benchmark. V1 outcomes informed the V2 task and comparator choices. V2 does not provide independent confirmation, biological validation, or evidence for general AI benefit. M2 and M5 estimate different task-native outcomes and are reported separately.

## M2: context-conditioned state estimation

The primary contrasts are `GRU MSE − context-gain-filter MSE`; negative values favor the GRU. Each seed trains a 3-parameter context-gain filter, a 297-parameter context-aware 8-unit GRU, and a 273-parameter observation-only 8-unit GRU on aligned-context trajectories, then evaluates on new trajectories under aligned (`κ=+1`), independent (`κ=0`), and reversed (`κ=−1`) mappings.

| Mapping | Context-aware GRU − filter, mean (95% seed-bootstrap interval) | Observation-only GRU − filter, mean (95% interval) |
|---|---:|---:|
| Aligned, κ=+1 | −0.02473 [−0.02640, −0.02293] | −0.00008 [−0.00279, +0.00265] |
| Independent, κ=0 | −0.17655 [−0.18314, −0.17007] | −0.19220 [−0.19666, −0.18753] |
| Reversed, κ=−1 | −0.32586 [−0.33728, −0.31434] | −0.38248 [−0.38866, −0.37624] |

Both trained recurrent estimators outperform the small context-gain filter under independent and reversed mappings. In the aligned condition, the context-aware GRU also outperforms the filter, while the observation-only GRU is statistically unresolved against it by the seed-bootstrap interval. Because the GRUs have roughly two orders of magnitude more trainable parameters, this comparison tests a stronger generic estimator but is not capacity matched. It does not isolate a context-specific computational advantage.

## M5: delayed teaching under overlapping inputs

The primary contrast is eligibility-trace accuracy minus equal-state latest-input accuracy; positive values favor eligibility. Each learner has 16 trainable weights. Eligibility and latest-input states each have 16 dimensions. Exact FIFO stores `16 × delay` state dimensions and is a memory-rich reference, not a capacity-matched control.

| Delay | Eligibility − latest input, mean accuracy difference (95% interval) | Eligibility − exact FIFO (95% interval) |
|---:|---:|---:|
| 1 | +0.42798 [+0.40427, +0.45136] | −0.05826 [−0.06509, −0.05157] |
| 4 | +0.39426 [+0.36529, +0.42368] | −0.07339 [−0.08069, −0.06641] |
| 16 | +0.29788 [+0.27429, +0.32236] | −0.14008 [−0.15152, −0.12817] |
| 64 | +0.02817 [−0.00205, +0.05936] | −0.43921 [−0.46756, −0.41238] |

Eligibility improves on retaining only the latest input at delays 1–16 in this synthetic task; the advantage is unresolved at delay 64. Exact FIFO performs better at all four delays, with a growing memory cost. The supported claim is therefore narrow: a decaying trace can improve delayed credit assignment over a one-vector latest-input cache over short and intermediate delays in this task. It does not show superiority to explicit memory.

## What worked

- The benchmark kept distinct M2 and M5 outcomes separate and reported task-specific paired seed-block uncertainty.
- V2 directly challenged V1's weak additive M2 comparator with trained recurrent estimators and challenged its non-overlapping M5 inputs with a continuous stream of overlapping examples.
- Parameter and state accounting exposed the M2 capacity mismatch and the FIFO memory trade-off instead of hiding them behind a shared “matched” label.
- A corrected full rerun reproduced all canonical seed-level M2 and M5 CSVs and the summary byte-for-byte. The independent verifier recomputed contrasts, bootstrap summaries, resource accounting, and hashes successfully.

## Failure and limitations

- The first run had an incorrect hand-calculated parameter count for the observation-only GRU (264 recurrent weights only; the 9 readout parameters were omitted) and did not explicitly store the 16-dimensional latest-input state. The verifier caught both accounting issues. That run is preserved as noncanonical; corrected outputs are in `data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/canonical_corrected/`. The correction followed inspection of the first run, so V2 remains explicitly post-result exploratory.
- The GRUs are not capacity matched to the 3-parameter filter and were trained only on aligned mappings. Their robustness to mapping changes is informative about this artificial task but cannot be described as a preplanned capacity-matched mechanism test.
- The M5 FIFO is intentionally memory-rich; its advantage does not establish that biological traces are inferior, since the task gives FIFO exact access to the delayed feature.
- Synthetic task construction, teacher rules, and chosen decay factor are not measurements of a biological circuit. No biological mechanism claim, causal claim, or cross-mechanism pooled effect follows.
- The benchmark does not yet establish performance under noisy labels, nonstationary teachers, alternative trace constants, broader task families, or compute-matched training budgets.

## Figure and rendered quality checks

The two-panel result figure preserves the distinct M2 and M5 scales and displays all 32 seed blocks per contrast. The source, editable PDF/SVG, 600-dpi PNG/TIFF, panel layout/alignment report, rendered text audit, and collision report are in `data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/figures/`. Final PDF dimensions are 179.8 × 84.8 mm; panel alignment passed at 1.5 pt tolerance; all 38 text runs are at least 5.2 pt; the collision audit reported zero warnings and failures. These are figure-rendering checks, not statistical or journal acceptance checks.

## Reproducibility record

An independent full rerun used the committed runner and contract. SHA-256 hashes matched byte-for-byte for `m2_seed_results.csv`, `m5_seed_results.csv`, and `summary.json`; see [REPRODUCIBILITY.json](../../data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/REPRODUCIBILITY.json). The independent structural and arithmetic check passed: 96 M2 rows and 128 M5 rows, with paired contrasts, resource accounting, bootstrap summaries, and artifact hashes verified.

## Interpretation boundary

V2 is a useful adversarial benchmark result, not evidence that the project has validated a shared computational principle. It weakens the M2 mechanism-specific advantage against trained recurrent estimators and bounds the M5 trace advantage against a weak latest-input memory. Both conclusions motivate a next experiment with frozen capacity/compute-matched controls and targeted counterfactuals; neither should be upgraded to biological-to-AI transfer without biological evidence directly specifying the computation being transferred.
