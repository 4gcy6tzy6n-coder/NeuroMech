# M2 feedback-site specificity V5 — results

**Classification:** completed retrospective source-model stress test, informed by prior M2/V3/V4 outcomes. This is neither biological validation nor an artificial-system transfer result.

## Source-index correction

Inspection of the pinned Figure 7 MATLAB script showed that its one-based `lagi=max(1,ti-delti)` lookup maps to Python `max(0,t-delti)` before the current update. V3/V4 used `max(0,t-1-delti)`, an extra one-step delay. V5 corrected this in a separate versioned runner and preserved the older scripts/results. One sample is `0.1333 s` at the model's 1,500 steps over 200 seconds. This was established by source-code indexing, not by executing MATLAB/Octave; full numerical parity remains unverified.

## Primary result

Across three imposed noise multipliers, the equal-weighted within-seed sensory-site minus motor-only warm-direction-index difference was **+0.13936** (95% seed-block bootstrap interval **[+0.13572, +0.14295]**; **200/200** blocks positive). The estimate is close to V4's `+0.14128`, but the versions use distinct source indexing and held-out seeds; this is a descriptive sensitivity comparison, not an inferential test that the estimates are equivalent.

| Noise | Motor-only coefficient | Direction contrast (95% interval) | Mean run difference | Median difference | P90 difference | ≥30 s fraction difference |
|---:|---:|---:|---:|---:|---:|---:|
| 0.75 | 0.760 | +0.18863 [+0.18046, +0.19653] | +0.7978 s | −0.9790 s | +4.1110 s | +0.02361 |
| 1.00 | 0.665 | +0.14127 [+0.13656, +0.14594] | +0.5914 s | −0.3953 s | +2.5876 s | +0.00596 |
| 1.25 | 0.610 | +0.08818 [+0.08482, +0.09159] | +0.3123 s | −0.2893 s | +1.6301 s | +0.00144 |

Differences are sensory-site minus motor-only. Development-only multi-summary selection still did not match persistence: motor-only runs had shorter mean and P90 durations, longer median durations, and fewer long runs at all three noise scales. The scalar control is the least-bad grid point, not an equivalence match.

## Interpretation

The positive source-model direction contrast survives correcting the delayed-position index. This makes the qualitative contrast less likely to be an artifact of that one-step implementation offset. It does **not** establish feedback-site specificity independently of run-persistence differences, because the multi-summary control remains mismatched. It also does not establish that this Python translation reproduces all MATLAB details, that the same causal effect occurs in animals, or that this computation improves AI.

The decisive next artificial comparison should use a control that can reproduce the sensory-site arm's relevant persistence process without receiving sensory-site feedback, with match adequacy assessed before testing direction. Repeating scalar coefficient selection is unlikely to resolve the confound.

## Verification and provenance

The independent verifier returned `PASS` for 1,800 complete held-out seed × noise × arm rows, coefficient selection recomputed from the generated development table, author-to-Python delay-index mapping, source/contract/output hashes, and primary bootstrap recomputation. Full machine-readable output is in [`data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5/`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5/).

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Source-index audit: [`SOURCE_INDEX_AUDIT.md`](SOURCE_INDEX_AUDIT.md)
- Corrected source model: [`source_model.py`](../../model/M2_FEEDBACK_SITE_SPECIFICITY_V5/source_model.py)
- Runner and verifier: [`model/M2_FEEDBACK_SITE_SPECIFICITY_V5/`](../../model/M2_FEEDBACK_SITE_SPECIFICITY_V5/)
- Author source checksum: `e2a9d5be4be436e30dfce7d59c4c95110cda189fbd54dc423128d0fc991b21c7`

**Disposition:** `CORRECTED_SOURCE_INDEX_CONTRAST_PERSISTS; PERSISTENCE_MATCH_STILL_FAILED`.
