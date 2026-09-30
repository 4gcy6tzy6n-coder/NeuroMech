# M2 low-data conditional-update benchmark V1 — results

**Classification:** post-result exploratory artificial benchmark. The prior M2 synthetic results were known. This is not biological validation or confirmatory evidence.

## Result

Across 20 paired training seeds and four fixed data budgets (16, 64, 256, 1024 sequences), the state-conditioned gain filter had lower held-out MSE than the equal-parameter additive RNN in the ALIGNED mapping. The equal-weighted contrast `MSE(GENERIC_RNN_1D) − MSE(MODE_GAIN_FILTER)` was **+0.01149** (seed-bootstrap 95% interval **[+0.01083, +0.01219]**; positive in **20/20** seeds). The direction and size of the effect were nearly unchanged across the four training-set sizes: +0.01150, +0.01148, +0.01151, and +0.01149.

| Evaluation mapping | Training sequences | Mode-gain MSE | Additive RNN MSE | Generic − mode (95% seed bootstrap CI) |
|---|---:|---:|---:|---:|
| ALIGNED | 16 | 0.05768 | 0.06917 | +0.01150 `[+0.01085, +0.01224]` |
| ALIGNED | 64 | 0.05703 | 0.06851 | +0.01148 `[+0.01054, +0.01248]` |
| ALIGNED | 256 | 0.05669 | 0.06820 | +0.01151 `[+0.01062, +0.01249]` |
| ALIGNED | 1024 | 0.05674 | 0.06823 | +0.01149 `[+0.01064, +0.01240]` |
| INDEPENDENT | 256 | 0.06714 | 0.05369 | −0.01345 `[−0.01453, −0.01245]` |
| REVERSED | 256 | 0.09730 | 0.06771 | −0.02960 `[−0.03098, −0.02829]` |

The gain is conditional. When the context-to-observation mapping was independent or reversed, the additive RNN had lower error at every training size; the reversal penalty was largest. Thus the study supports a narrow synthetic inductive-bias result: a four-parameter context-conditioned update can exploit a known aligned context relation, while that same hard-wired relation is brittle under mapping shift. The flat aligned contrast across data sizes does not show a dose-response in sample efficiency.

## Resource accounting

Each fit used 250 Adam updates, batch size 16, sequence length 160, and therefore 640,000 sequence-step tokens; both models had four trainable parameters. Mean measured Python training time per fit was 0.90 s for the mode-gain filter and 1.16 s for the additive RNN in this run. Timing is hardware/runtime specific and secondary. Parameter and sample-token budgets were matched; exact FLOPs were not.

## Interpretation and boundary

This benchmark does not establish that the synthetic `H(q)` observation mapping is the worm's measured computation. Nor does it show superiority to the bilinear RNN, GRU, Kalman reference, or other strong adaptive models: the equal-parameter comparator here is specifically an additive scalar RNN and cannot directly represent the multiplicative input-by-context interaction. Earlier M2 benchmarks show that stronger task-aware/adaptive references can outperform structured filters. The correct claim is conditional performance over this fixed comparator family, not a general AI advantage.

## Reproduction and verification

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and independent verifier: [`model/M2_LOW_DATA_GATING_V1/`](../../model/M2_LOW_DATA_GATING_V1/)
- Episode-level outcomes, training metrics, manifest and verification: [`data/results/M2_LOW_DATA_GATING_V1/`](../../data/results/M2_LOW_DATA_GATING_V1/)
- Independent verification passed for all 122,880 episode rows, 160 model fits, paired seed estimand, bootstrap interval, parameter/sample-token accounting and recorded artifact hashes.
