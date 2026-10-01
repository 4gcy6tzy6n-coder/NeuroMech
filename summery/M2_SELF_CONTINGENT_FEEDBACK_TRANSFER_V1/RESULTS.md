# Results — M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1

## Question and scope

This exploratory artificial-transfer experiment asked whether recipient-specific motor feedback in a sensory-state update improves synthetic target tracking relative to cross-agent-yoked feedback with the same instantaneous population distribution. It is motivated by the RIM-dependent motor-feedback account in Ji et al. (2021), but the artificial task and equations are stipulated. The result is not a biological test, causal validation, or evidence that this computation improves AI generally. The within-experiment contract was frozen before the corrected run; prior project M2 outcomes were already known.

## Primary result

The frozen primary contrast was `CROSS_AGENT_YOKED_SENSORY − SELF_SENSORY` held-out movement MSE in `SLOW_TRANSIENT`; positive values favor self-contingent feedback. Across 32 paired training seed blocks, the mean contrast was **+0.009431** (median `+0.008292`; seed-block bootstrap 95% interval `[+0.007434, +0.011676]`). The yoke's instantaneous population feedback distribution was verified to match exactly at all 128 block/condition checks. This supports a recipient-contingency effect in this particular slow-transient simulator condition.

The effect was conditional. In `FAST_TRANSIENT`, SELF_SENSORY MSE was `0.57191` versus `0.56957` for the yoked arm, so self-contingency did not help there. In clean conditions, SELF_SENSORY also had higher MSE than the yoked arm (`0.19556` vs `0.19380` in `SLOW_CLEAN`; `0.43197` vs `0.42319` in `FAST_CLEAN`). The preregistered primary was only `SLOW_TRANSIENT`; these other condition values are descriptive boundary evidence.

## Strong controls and interpretation

In the primary condition, SELF_OUTPUT MSE was `0.36819`, the six-parameter `GENERIC_RNN_1D` was `0.35484`, and the 297-parameter `GRU_8` was `0.30434`, all lower than SELF_SENSORY (`0.37930`). NO_FEEDBACK was `0.38934`. Thus the primary contrast isolates a small recipient-specific effect versus the yoked sensory arm, but it does **not** show that sensory-site feedback is the best placement, that feedback beats generic recurrence, or that the biological abstraction yields an overall AI performance advantage. Model sizes also differ substantially, so no capacity-equivalence claim is made.

The defensible conclusion is narrow: preserving self-to-recipient contingency improved MSE over a population-distribution-matched cross-agent yoke in one slow-transient synthetic setting. It did not generalize to the fast-transient condition, and stronger generic/output/recurrent controls performed better on the primary metric. This is not a shared M2/M5 principle or NMI-level AI-benefit result.

## Verification and reproducibility

The independent verifier passed: 192 fit records, 98,304 test-episode rows, 768 seed-summary rows, 128 population-distribution checks, and recomputation of all 32 primary seed-block contrasts. An independent full rerun reproduced test episode metrics, test seed summaries, feedback-distribution checks, and summary JSON byte-for-byte. All non-timing fields in the fit manifest also matched; measured `training_seconds` differed as expected. See [`REPRODUCIBILITY.json`](../../data/results/M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1/canonical/REPRODUCIBILITY.json), [`POSTRUN_VERIFICATION.json`](../../data/results/M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1/canonical/POSTRUN_VERIFICATION.json), and the canonical output manifest.

## Artifacts

- Frozen contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and verifier: [`model/M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1/`](../../model/M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1/)
- Canonical results and hashes: [`data/results/M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1/canonical/`](../../data/results/M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1/canonical/)
- First-attempt implementation incident: [`EXECUTION_INCIDENT_01.md`](EXECUTION_INCIDENT_01.md)
