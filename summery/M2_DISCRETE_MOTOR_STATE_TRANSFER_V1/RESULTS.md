# M2 discrete motor-state feedback transfer V1 — results

**Classification:** outcome-informed exploratory artificial experiment. A six-seed feasibility preflight was inspected before the full run. This is not confirmatory evidence or biological validation.

## Primary result

The primary test used 32 fresh seed blocks and 128 shared held-out episodes per block and arm in the `LONG_BURST` profile. All four learned GRUs had 321 parameters and the same 160-update budget. The primary paired contrast, `SELF_STATE − ACTION_STATE`, was **−0.01429 tracking MSE** (95% seed-block bootstrap interval **[−0.02462, −0.00442]**), favoring categorical realized motor state over the sign of the previous command.

This did not isolate a self-contingent motor-state effect. `SELF_STATE − ZERO_STATE` was `+0.00044` (95% interval `[−0.01161, +0.01320]`), unresolved. `SELF_STATE − YOKED_STATE` was `−0.00985` (`[−0.02376, +0.00408]`), also unresolved. The fixed reactive controller scored `0.79545` MSE against `0.75321` for `SELF_STATE`; this is a nonlearned reference, not a capacity-matched model. In the `FAST_TARGET` profile, the fixed reactive policy was better than every learned arm, so cross-profile competence is not uniform.

## Interpretation

The result advances the previous continuous-velocity test in one useful respect: the model now receives a binary sign of realized movement, closer in granularity to the forward/reversal state discussed in the worm source. In the primary long-gap condition, that channel helped relative to intended action sign. However, zero-input and recipient-yoked controls prevent attributing the result uniquely to self-contingent movement feedback. The effect is thus a bounded input-representation result within one synthetic tracking task, not evidence that the RIM–AIY mechanism transfers to AI.

The six-seed feasibility preflight found mixed rankings among learned controls, and is preserved in `data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/PREPILOT.json`. The full-run seeds are disjoint. Because the preflight and earlier M2 results were observed, neither the full run nor its primary interval should be described as independent confirmation.

## Verification and artifacts

The independent verifier passed 128 fit rows, 81,920 episode rows, 640 seed summaries, and 128 exact per-time yoke-distribution checks. It independently recomputed primary and secondary seed-block contrasts, checked parameter/update counts, and verified source/output hashes. A second full run and byte comparison are recorded in `data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/RERUN_VERIFICATION.json`.

- Contract and limitations: [`CONTRACT.md`](CONTRACT.md)
- Figure contract and QA limitation: [`FIGURE_CONTRACT.md`](FIGURE_CONTRACT.md) · [`FIGURE_QA.md`](FIGURE_QA.md)
- Figure: [editable SVG](../../data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/figures/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1.svg) · [PDF](../../data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/figures/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1.pdf) · [600-dpi TIFF](../../data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/figures/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1.tiff)
- Runner, verifier, and disclosed preflight runner: [`model/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/`](../../model/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/)
- Canonical outcomes and rerun record: [`data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/`](../../data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/)
