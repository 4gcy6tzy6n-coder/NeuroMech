# M2 feedback-site specificity V4 — results

**Classification:** completed, retrospective, outcome-informed source-model stress test. Earlier M2 and V3 outcomes were known. This is not a confirmatory result, new biological evidence, or AI-transfer result.

## Design

V4 reused the Ji et al. Figure 7 Python source-model implementation and V3 development blocks. For each of three imposed noise multipliers, a motor-only feedback coefficient was selected on the V3 development data by minimizing standardized error across four run-duration summaries: mean, median, 90th percentile, and fraction of runs at least 30 seconds. Evaluation used 200 new seed blocks (320000–320199), 50 agents per block, and three arms. The seed block was the analysis unit.

The calibration did **not** achieve a close multi-summary match. “Multi-statistic matched” describes the coefficient-selection rule, not demonstrated equivalence of the arms.

## Primary result

The equal-weighted sensory-site minus motor-only warm-direction-index contrast across the three noise multipliers was **+0.14128** (95% seed-block bootstrap interval **[+0.13798, +0.14460]**); all **200/200** held-out blocks were positive.

| Noise multiplier | Motor-only coefficient | Warm-direction contrast (95% interval) | Mean run-duration difference | Median difference | 90th-percentile difference | Difference in ≥30 s fraction |
|---:|---:|---:|---:|---:|---:|---:|
| 0.75 | 0.760 | +0.13328 [+0.12634, +0.14023] | +2.506 s | −0.985 s | +8.810 s | +0.0411 |
| 1.00 | 0.640 | +0.17626 [+0.17146, +0.18114] | +1.535 s | −0.288 s | +5.461 s | +0.0231 |
| 1.25 | 0.600 | +0.11429 [+0.11012, +0.11841] | +0.636 s | −0.259 s | +2.539 s | +0.0066 |

Differences are sensory-site minus motor-only. The primary contrast is positive, but persistence remains mismatched in multiple dimensions. The unconstrained standardized least-squares rule did not guarantee adequate equivalence; at noise 0.75, sensory-site mean run duration was 8.868 s versus 6.362 s for motor-only.

## Interpretation and failure experience

The source model retained a sensory-site versus motor-only behavioral difference under a new development-only coefficient-selection rule. V4 does **not** isolate feedback placement from persistence dynamics because the selected motor-only controls did not match the target persistence summaries closely. The larger primary contrast than V3 cannot be interpreted as stronger evidence; the comparator changed and fit poorly at some noise scales.

The concrete lesson is that a one-parameter motor-only controller cannot be assumed to match several features of a sensory-feedback run process merely because its coefficient was selected by a multi-feature loss. Future work should either use a control that directly yokes the full persistence process from independent development data, or report the comparison as a bounded source-model difference without claiming persistence has been controlled. Any follow-up remains exploratory because prior outcomes are known.

## Verification and artifacts

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner: [`run_experiment.py`](../../model/M2_FEEDBACK_SITE_SPECIFICITY_V4/run_experiment.py)
- Independent verifier: [`verify_results.py`](../../model/M2_FEEDBACK_SITE_SPECIFICITY_V4/verify_results.py)
- Held-out rows and manifest: [`heldout_simulation_metrics.csv`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V4/heldout_simulation_metrics.csv), [`run_manifest.json`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V4/run_manifest.json)
- Verification: `PASS` for all 1,800 complete seed × noise × arm rows, development-only coefficient selection, output hashes, primary estimate, and bootstrap interval. See [`POSTRUN_VERIFICATION.json`](../../data/results/M2_FEEDBACK_SITE_SPECIFICITY_V4/POSTRUN_VERIFICATION.json).

## Disposition

`SOURCE_MODEL_DIFFERENCE_PERSISTS_BUT_PERSISTENCE_MATCH_FAILED`. Preserve the positive contrast and control-mismatch failure together. No biological or AI-transfer claim follows from this run.
