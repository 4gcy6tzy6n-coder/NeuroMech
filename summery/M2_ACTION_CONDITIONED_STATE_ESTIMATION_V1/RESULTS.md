# M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1 — results

## Status

**The prespecified sensory-site mechanism criterion was not met.** This is a post-result exploratory artificial computation test, informed by earlier M2 outcomes. It is neither independent confirmation nor biological validation.

## Execution

The run completed 32 independent training-seed blocks, seven trained controllers, three evaluation couplings, and 256 fresh episodes per seed × arm × coupling: 196,608 episode records and 224 fitted model records. All models were trained on aligned action-to-state coupling `c=+1`; `c=0` and `c=−1` were held-out mismatch conditions. Each LTC model had 42 trainable parameters, `GRU_2` had 45, and `GRU_4` had 113. The signed-state oracle had access to latent gradient/state information and is a privileged reference only.

## Primary outcome: aligned coupling (`c=+1`)

The endpoint is signed displacement MSE; lower is better. Contrasts are comparator minus sensory-site LTC, so a positive difference favors the sensory-site arm. Bootstrap intervals resample paired training-seed blocks.

| Comparator | Mean paired difference | 95% seed-block bootstrap CI | Positive blocks |
|---|---:|---:|---:|
| Output-site LTC | −0.15519 | [−0.15668, −0.15367] | 0/32 |
| No-feedback LTC | +0.00249 | [+0.00166, +0.00337] | 28/32 |
| Dense-feedback LTC | −0.00104 | [−0.00258, +0.00045] | 14/32 |
| Yoked sensory feedback | +0.00229 | [+0.00144, +0.00319] | 27/32 |
| `GRU_2` | −0.40910 | [−0.56888, −0.27011] | 1/32 |
| `GRU_4` | −1.33936 | [−1.50396, −1.15245] | 1/32 |

The sensory-site LTC showed very small MSE reductions versus no-feedback and yoked feedback (about 0.1% of its own MSE), but it was decisively worse than output-site feedback and the generic recurrent references. Its absolute MSE was `1.9748`; output-site was `1.8196`, `GRU_2` was `1.5657`, and `GRU_4` was `0.6354`. The oracle reached `0.0292`. Thus the frozen requirement to beat both output-site and yoked feedback was not met. The tiny positive contrasts against no-feedback/yoked do not establish a practically useful benefit; no SESOI was specified.

The task itself was learnable in the aligned condition: `GRU_4` reduced error well below the privileged-information-free LTC arms. The failure is therefore specifically adverse to this sensory-site LTC implementation under this task and optimizer, not evidence that the task had no learnable solution. Final training loss remained high for sensory-site LTC (`1.9632`) while `GRU_4` reached `0.6977` over its last ten updates, consistent with a substantial optimization/inductive-bias disadvantage for the LTC implementation.

## Held-out coupling mismatch

At `c=0`, where motor commands do not change the hidden displacement, LTC arms had MSE near `0.75`; the sensory-site arm did not improve over no-feedback or yoked inputs. At `c=−1`, the aligned-trained sensory-site and no-feedback LTC arms were near `1.97`, while the output-site LTC was `2.20`; `GRU_4` degraded to `5.06`. These secondary results show strong dependence on the trained action-to-state mapping and do not establish robustness to coupling shifts.

## Interpretation and next implication

The experiment rejects the claim that this sensory-site LTC route has a useful advantage in this supervised state-estimation task: a direct output-site route performed better, small sensory-site gains over no-feedback/yoking were practically tiny, and generic recurrence performed substantially better. This is a negative artificial transfer result for the tested abstraction and implementation. It does not refute the published biological RIM–AIY observations. The actual biological work supports motor-state influence on sensory representation and behavioral persistence; it does not specify this exact state-estimation objective or an LTC equation.

The next research move should not be to retune this result. It should compare the biological source model's measured AIY representation and a source-derived circuit operation against generic/adaptive alternatives, or shift the AI-side focus to the cerebellar eligibility mechanism with the same strong-control discipline. Keep this run as a counterexample in the eventual synthesis.

## Reproducibility

- [Frozen contract](CONTRACT.md) and [failure/limitation record](FAILURE_LOG.md)
- [Runner, analysis, figure source, and verifier](../../model/M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1/)
- [Raw episode/model records, summary, and verification](../../data/results/M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1/)
- [Figure](../../data/results/M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1/figures/M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1.png)
