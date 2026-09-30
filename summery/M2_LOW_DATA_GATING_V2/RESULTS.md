# M2 low-data conditional-update benchmark V2 — results

**Classification:** post-result exploratory artificial benchmark. The V1 and earlier M2 results were known; V2 uses disjoint seeds and a stronger parameter-matched comparator. It is not confirmatory evidence or biological validation.

## Result

Across 20 paired task seeds and four nested training-set sizes, the four-parameter mode-gain filter had lower MSE than the four-parameter bilinear tanh RNN. In the prespecified ALIGNED primary, the equal-weighted contrast `MSE(GENERIC_BILINEAR_RNN_1D) − MSE(MODE_GAIN_FILTER)` was **+0.00509** (seed-bootstrap 95% interval **[+0.00465, +0.00552]**; positive in **20/20** seeds).

| Mapping | Train size | Mode-gain MSE | Bilinear RNN MSE | Bilinear − mode (95% seed-bootstrap CI) |
|---|---:|---:|---:|---:|
| ALIGNED | 16 | 0.05634 | 0.06138 | +0.00504 `[+0.00456, +0.00553]` |
| ALIGNED | 64 | 0.05603 | 0.06088 | +0.00485 `[+0.00424, +0.00542]` |
| ALIGNED | 256 | 0.05591 | 0.06099 | +0.00507 `[+0.00457, +0.00557]` |
| ALIGNED | 1024 | 0.05554 | 0.06092 | +0.00537 `[+0.00487, +0.00587]` |
| INDEPENDENT | 256 | 0.06658 | 0.07438 | +0.00780 `[+0.00619, +0.00938]` |
| REVERSED | 256 | 0.09660 | 0.11025 | +0.01365 `[+0.01034, +0.01694]` |

The structured filter was better than the bilinear model in all three mappings, including INDEPENDENT and REVERSED. However, its absolute error increased sharply under reversal (about 0.056 aligned to 0.096 reversed). Since its relative advantage did not depend on the aligned mapping, this run does **not** show that the biological-inspired context relation itself caused the advantage. It may instead reflect the filter's recurrence parameterization, the generic model's tanh dynamics, or optimization behavior. The aligned contrast also stayed small and nearly flat across training sizes, so this is not a low-data-specific effect.

## Resource accounting and verification

Each fit used 250 Adam updates, batch size 16, sequence length 160, and 640,000 sequence-step tokens. Both arms had exactly four trainable parameters. Mean Python training time was 0.90 s per mode-gain fit and 1.43 s per bilinear fit in this run; this is an implementation-specific diagnostic, not a hardware-independent FLOP result. Independent verification passed for 122,880 episode rows, 160 fits, the paired-seed primary estimate and interval, and artifact hashes.

## Interpretation boundary

The experiment establishes only that this specific mode-gain implementation beat this four-parameter bilinear tanh comparator on the tested synthetic scalar estimation family and training budget. The context-observation relation is artificial, and the model comparison also changes the update equation and nonlinear parameterization. It does not establish the worm circuit's computation, its transfer to AI, or a broad efficiency/accuracy principle. Taken with V1 and earlier stronger adaptive references, M2 has not yet demonstrated an alignment-specific artificial advantage over a sufficiently broad set of controls.

## Artifacts

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and verifier: [`model/M2_LOW_DATA_GATING_V2/`](../../model/M2_LOW_DATA_GATING_V2/)
- Episode outcomes, fit metrics, manifest and verification: [`data/results/M2_LOW_DATA_GATING_V2/`](../../data/results/M2_LOW_DATA_GATING_V2/)
