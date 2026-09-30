# M2 conditional-update benchmark V3 — linear controls and Kalman reference

**Classification:** post-result exploratory artificial benchmark. V1/V2 were known; V3 uses new seeds. This is not biological validation or confirmatory evidence.

## Result

The 20-seed, four-data-size primary compared the four-parameter `MODE_GAIN_FILTER` with a five-parameter `LINEAR_BILINEAR_RNN` that has free input, context, input×context, state, and context×state terms. In ALIGNED evaluation, the equal-weighted contrast `MSE(LINEAR_BILINEAR_RNN) − MSE(MODE_GAIN_FILTER)` was **+0.00656** (95% seed-bootstrap interval **[+0.00614, +0.00695]**; positive in **20/20** seed clusters). The direct three-parameter context-free constant-gain filter was worse than mode-gain by **0.00899** (95% interval **[+0.00847, +0.00946]**, 20/20 positive).

| Mapping | Mode-gain filter | Constant-gain filter | Linear bilinear update | Kalman oracle |
|---|---:|---:|---:|---:|
| ALIGNED | 0.05693 | 0.06592 | 0.06349 | 0.05383 |
| INDEPENDENT | 0.06749 | 0.05324 | 0.07981 | 0.04183 |
| REVERSED | 0.09813 | 0.06623 | 0.11198 | 0.05426 |

Entries are mean sequence MSE, averaged equally over training sizes 16, 64, 256, and 1024. In ALIGNED, the state-conditioned filter beat both the no-context ablation and the more expressive bilinear update, but remained behind the task-aware Kalman reference. The result changed under mapping shift: the context-free filter was better than mode-gain in INDEPENDENT and REVERSED conditions. At size 256, constant-minus-mode was `−0.01428` (95% CI `[−0.01477, −0.01385]`) for INDEPENDENT and `−0.03169` (95% CI `[−0.03244, −0.03094]`) for REVERSED.

## Interpretation

This is the clearest result so far for a conditional inductive bias in the M2 artificial family: a fixed state-dependent gain helps when the state marks the informative observation channel, and hurts when that relation changes. The learned computation does not match the task-aware optimum, and a generic bilinear update is worse across all three mappings despite having one extra parameter; that second comparison does not show the gain relation itself is the cause, since update equations and optimization differ.

Crucially, the context-to-observation mapping was imposed by the synthetic benchmark. It is not a demonstrated biological detail of the RIM–AIY circuit. This result therefore supports a task-bounded artificial computation, not biological-to-AI transfer, a general AI advantage, or NMI publication readiness.

## Resource accounting and verification

All learned arms received the same 250 Adam updates, batch size 16, 160-step sequences, and 640,000 sequence-step tokens per fit. Parameter counts were 4 (mode-gain), 3 (constant-gain), and 5 (linear bilinear). Mean training times in this CPU execution were 0.90 s, 0.61 s, and 1.31 s per fit, respectively; these are implementation-specific diagnostics, not hardware-independent efficiency estimates. The Kalman oracle used known test-sequence dynamics and observation mapping and had no trainable parameters.

The independent verifier passed all 245,760 held-out rows and 240 learned fits, independently recomputed the Kalman oracle across every seed/condition, reproduced both paired seed-level contrasts and intervals, and checked the frozen contract, runner, and result hashes.

## Artifacts

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and independent verifier: [`model/M2_LOW_DATA_GATING_V3/`](../../model/M2_LOW_DATA_GATING_V3/)
- Episode data, fit metrics, manifest and verification: [`data/results/M2_LOW_DATA_GATING_V3/`](../../data/results/M2_LOW_DATA_GATING_V3/)
- Prior comparator sensitivity results: [V1](../M2_LOW_DATA_GATING_V1/RESULTS.md) and [V2](../M2_LOW_DATA_GATING_V2/RESULTS.md)
