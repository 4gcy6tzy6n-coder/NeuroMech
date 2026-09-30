# M2 full motor-state trajectory replay V1 — results

**Classification:** retrospective, exploratory source-model analysis. Earlier M2/V1-yoke outcomes were known. No new biological evidence or AI-transfer result is produced.

## Primary result

Across the three imposed noise scales, the equal-weighted sensory-site minus full-trajectory-replay warm-direction-index difference was **+0.44742** (95% seed-block bootstrap interval **[+0.43988, +0.45497]**; **200/200** blocks positive). The scalar motor-only comparator difference was **+0.13781** (95% interval `[+0.13454, +0.14112]`; 200/200 blocks positive). The replay arms had warm-direction index close to zero at all three scales; sensory-site means were about `0.59`, `0.43`, and `0.33`.

The replay selected complete forward/reverse mode sequences from independent development sensory-site simulations. It therefore preserves each selected 200-second mode trace, including serial structure and record-boundary censoring, while disconnecting it from the held-out path's current position and heading.

## Held-out persistence differences

| Noise | Direction contrast (95% interval) | Mean forward-duration difference | Forward P90 difference | Forward occupancy difference | Reverse mean-duration difference | Reverse P90 difference |
|---:|---:|---:|---:|---:|---:|---:|
| 0.75 | +0.58361 [+0.56614, +0.60085] | +0.09094 s | −0.10673 s | +0.00041 | +0.78427 s | +3.51293 s |
| 1.00 | +0.43022 [+0.42070, +0.43981] | −0.01522 s | −0.10500 s | −0.00077 | +0.03827 s | +0.02033 s |
| 1.25 | +0.32841 [+0.32121, +0.33552] | +0.00461 s | +0.08000 s | −0.00114 | +0.07277 s | +0.03947 s |

Differences are sensory-site minus replay. Forward mode summaries are close across the three scales; reverse summaries also remain close at 1.00 and 1.25. At 0.75 the replay has a residual reverse-duration tail difference. No equivalence bounds were frozen, so these are descriptive adequacy checks, not a match pass.

## Interpretation

In this corrected Python source-model implementation, replaying complete motor-state traces without their held-out sensory/environmental context does not recover warm-direction behavior, even though most held-out persistence summaries are close. This supports a bounded model-level claim: marginal motor-state timing alone is insufficient; the relation between state timing and sensory/environmental context matters in this simulation.

It does not establish that feedback at the sensory-processing site is the only explanation. A context-aware motor controller, other state variables, or remaining implementation differences could also explain the contrast. The reverse-tail mismatch at low noise remains. The experiment does not estimate an animal-level effect or show AI benefit, and MATLAB/Octave end-to-end parity remains unverified.

## Verification

Independent verification passed for 120 outcome-blind development summary rows, 2,000 packed mode traces per noise scale, 2,400 complete held-out seed × scale × arm rows, provenance and output hashes, regeneration of all 600 replay summaries from the archived mode libraries, held-out persistence contrasts, and both bootstrap estimates. See [`POSTRUN_VERIFICATION.json`](../../data/results/M2_STATE_TRAJECTORY_REPLAY_V1/POSTRUN_VERIFICATION.json).

**Disposition:** `FULL_REPLAY_DIRECTION_CONTRAST_PERSISTS; LOW_NOISE_REVERSE_TAIL_DIFFERENCE_REMAINS; EXPLORATORY_SOURCE_MODEL_EVIDENCE`.
