# M5 eligibility trace on learnable delayed temporal XOR — V2 results

**Classification:** post-result exploratory optimization. M10 V1 and optimizer-calibration outcomes were known. This is not confirmatory evidence, biological validation, or general AI transfer.

## Result

The independent task-seed mean held-out accuracy was `0.7347` for `ELIGIBILITY_TRACE`, `0.5529` for `NO_TRACE`, and `0.9997` for `BPTT`. The primary paired contrast `ELIGIBILITY_TRACE − NO_TRACE` was **+0.1819 accuracy** (95% task-seed bootstrap interval `[+0.1141, +0.2485]`; positive in 24/30 seeds). BPTT passed the frozen viability rule: its 95% task-seed interval was `[0.9994, 1.0000]`, above binary chance.

The trace remained below BPTT by `−0.2650` accuracy (95% task-seed interval `[−0.3262, −0.2047]`). Thus the interpretable result is a benefit over the immediate local-update ablation in this four-step-delay task, alongside a large performance gap to exact backpropagation.

## Interpretation boundary

V2 changes the optimizer and narrows the task to the short-delay condition where calibration established learnability. Both changes were made after M10 V1 was inspected. The result is consequently an exploratory optimization follow-up, not an independent confirmation. It supports neither long-delay temporal binding nor a claim that the eligibility trace matches BPTT, improves general AI, or validates a cerebellar learning rule. The biological climbing-fiber evidence motivates a bounded teaching-event analogy; the trace equation itself remains an artificial abstraction.

## Reproducibility

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and independent verifier: [`model/M5_ELIGIBILITY_TEMPORAL_XOR_V2/`](../../model/M5_ELIGIBILITY_TEMPORAL_XOR_V2/)
- Machine-readable outcomes: [`data/results/M5_ELIGIBILITY_TEMPORAL_XOR_V2/`](../../data/results/M5_ELIGIBILITY_TEMPORAL_XOR_V2/)
- Verification re-computed 90 unique seed-arm cells, the primary contrast and intervals, BPTT viability, and artifact hashes.
