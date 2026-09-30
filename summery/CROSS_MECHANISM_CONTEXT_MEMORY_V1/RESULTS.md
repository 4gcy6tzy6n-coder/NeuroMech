# CROSS_MECHANISM_CONTEXT_MEMORY_V1 — results

**Status:** exploratory, post-result cross-mechanism benchmark. The biological literature and earlier artificial results were already known. This does not independently validate either organismal mechanism.

## M2: contextual sensory gain

The 3-parameter context-gain filter was fitted on aligned context/noise trajectories and evaluated on separate trajectories. The equally parameterized additive recurrent control was trained on the same aligned trajectories. Across 32 task-seed blocks:

| Context–reliability mapping | Context-gain MSE | Additive-control MSE | Control − gain, 95% seed-bootstrap interval | Positive blocks |
|---|---:|---:|---:|---:|
| Aligned (`κ=+1`) | 0.1713 | 0.2300 | +0.05871 [+0.05770, +0.05973] | 32/32 |
| Independent (`κ=0`) | 0.3597 | 0.2297 | −0.13000 [−0.13301, −0.12694] | 0/32 |
| Reversed (`κ=−1`) | 0.5493 | 0.2294 | −0.31992 [−0.32570, −0.31410] | 0/32 |

This supports a narrow simulator result: context-conditioned gain is useful only when context predicts observation quality; it is harmful when that mapping is absent or reversed. The mapping is a synthetic assumption, not established as the corresponding biological relation in the worm.

## M5: delayed teaching trace

The 16-parameter eligibility learner was compared with an equal-parameter control that applies the teaching label to an unrelated current distractor, plus a persistent-cue reference that retains the correct cue. At 32 task-seed blocks per delay, eligibility accuracy was 0.888, 0.897, 0.899, and 0.897 at delays 1, 4, 16, and 64. Eligibility-minus-misassignment contrasts were +0.4070 [+0.3762, +0.4370], +0.3998 [+0.3730, +0.4266], +0.3914 [+0.3666, +0.4177], and +0.4052 [+0.3676, +0.4411].

Eligibility and the persistent-cue reference had identical held-out accuracy in every seed and delay. Both use 16 learned weights and 16 internal state dimensions. The artificial trace therefore did **not** outperform the capacity-matched direct-cue memory. The large contrast against misassignment is not evidence that biological-style decay is superior to ordinary cue retention.

## Joint interpretation

The outcomes remain separate because the M2 endpoint is state-estimation MSE and the M5 endpoint is classification accuracy. M2 shows an alignment-dependent result; M5 shows that a delayed local trace can retain the relevant cue but no advantage over an equally sized direct cue buffer. This benchmark does not establish a shared positive principle, general AI transfer, or NMI readiness.

## Reproducibility

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and verifier: [`model/CROSS_MECHANISM_CONTEXT_MEMORY_V1`](../../../model/CROSS_MECHANISM_CONTEXT_MEMORY_V1/)
- Canonical seed-level outcomes: [`data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V1/canonical`](../../../data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V1/canonical/)
- Independent verifier: `PASS` for row counts, seed-block contrasts, bootstrap summaries, equal trace/replay state, and artifact hashes.
