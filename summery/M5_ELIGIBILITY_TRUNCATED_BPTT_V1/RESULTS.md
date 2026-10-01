# M5_ELIGIBILITY_TRUNCATED_BPTT_V1 — results

## Finding

The eligibility trace did **not** outperform four-step TBPTT or full BPTT on this delayed XOR task. It did improve over the local no-trace update, reproducing a narrow delayed-credit benefit while losing to the stronger recurrent-gradient comparison.

| Arm | Mean held-out accuracy | Train time per seed, mean |
|---|---:|---:|
| Eligibility trace (`γ=0.98`) | 0.6974 | 0.327 s |
| No-trace local update | 0.5562 | 0.331 s |
| TBPTT-1 | 0.5562 | 0.340 s |
| TBPTT-4 | 0.9633 | 0.388 s |
| Full BPTT | 0.9996 | 0.433 s |

The primary contrast was eligibility minus TBPTT-4: **−0.26588 accuracy** (paired task-seed bootstrap 95% CI **[−0.32950, −0.20031]**; only **1/32** seeds favored eligibility). The eligibility trace beat no-trace by `+0.14125` (95% CI `[+0.07188, +0.21288]`; 20/32 seeds positive). TBPTT-1 exactly matched no-trace in this implementation (`0.5562` mean). Full BPTT's 95% seed-block interval was `[0.99925, 0.99988]`, well above chance, so the task-learnability reference passed.

All arms used the same 24-unit recurrent network and 746 trainable parameters. Eligibility was modestly faster than TBPTT-4/full BPTT on this CPU implementation, but this timing is only descriptive. It is not a hardware-independent compute estimate, and its accuracy was substantially lower.

## Interpretation

This result does not support eligibility traces as a competitive substitute for even a short four-step recurrent gradient in this task. It does preserve evidence that local eligibility improves credit over a current-step-only local update. The gap shows that the trace's advantage depends on which baseline is chosen: it is positive against no-trace and negative against TBPTT-4 and full BPTT. The contrast must therefore be reported with both local and recurrent-gradient controls.

This is a post-result exploratory synthetic test, informed by earlier M5 temporal-XOR results. It is not independent confirmation, a cerebellar simulation, biological validation, or a general AI claim. The biological evidence motivates delayed teaching with a local eligibility tag, but does not specify this artificial trace equation or XOR objective.

## Reproducibility

- [Frozen contract](CONTRACT.md) and [failure log](FAILURE_LOG.md)
- [Runner, analysis, plot source, and verifier](../../model/M5_ELIGIBILITY_TRUNCATED_BPTT_V1/)
- [Seed-level results and audit](../../data/results/M5_ELIGIBILITY_TRUNCATED_BPTT_V1/)
- [Rendered figure](../../data/results/M5_ELIGIBILITY_TRUNCATED_BPTT_V1/figures/M5_ELIGIBILITY_TRUNCATED_BPTT_V1.png)
