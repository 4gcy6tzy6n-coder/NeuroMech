# Post-run trade-off audit — M2_SENSORIMOTOR_TRANSIENT_FILTER_V1

**Classification:** exploratory secondary analysis of an already inspected run. It does not alter the frozen primary endpoint or its result. Contrasts are paired by seed block and use 50,000 percentile-bootstrap resamples. Intervals are descriptive across multiple comparisons; no multiplicity correction was applied.

## Paired contrasts across the five frozen evaluation conditions

Each value is `OUTPUT_SITE_1D − SENSORY_SITE_1D`; negative values favor the output-site model. Metrics were recorded in the original experiment. Testing this pattern across every condition is post-result.

| Condition | Movement MAE difference (95% CI) | Movement MSE difference (95% CI) | Command energy difference (95% CI) | Switch-latency difference, steps (95% CI) |
|---|---:|---:|---:|---:|
| CLEAN_STABLE | −0.0967 [−0.1110, −0.0822] | −0.0273 [−0.0353, −0.0197] | +0.1747 [+0.1510, +0.1983] | +0.5407 [+0.4162, +0.6690] |
| TRANSIENT_PULSE | −0.0791 [−0.0919, −0.0660] | −0.0401 [−0.0485, −0.0317] | +0.1161 [+0.0938, +0.1381] | +0.5059 [+0.3523, +0.6581] |
| LONG_PULSE | −0.0794 [−0.0906, −0.0677] | −0.0391 [−0.0456, −0.0323] | +0.1208 [+0.0993, +0.1419] | +0.5466 [+0.4114, +0.6793] |
| SUSTAINED_SWITCH | −0.0430 [−0.0543, −0.0318] | +0.0166 [+0.0077, +0.0253] | +0.1059 [+0.0842, +0.1274] | +0.3612 [+0.2776, +0.4412] |
| COMBINED_STRESS | −0.0306 [−0.0374, −0.0237] | +0.0049 [+0.0013, +0.0088] | +0.0610 [+0.0409, +0.0814] | +0.2950 [+0.2168, +0.3745] |

## Pattern and interpretation

The output-site arm had lower mean absolute movement error in all five conditions, while it used more command energy and had longer switch latency than the sensory-site arm in all five. The squared-error contrast changed direction: output-site was lower in the three lower-switch-hazard conditions, while sensory-site was lower in the sustained-switch and combined-stress conditions. This is a metric- and condition-dependent profile, not a single overall winner.

The pattern is compatible with an accuracy/effort/flexibility trade-off, but no resource constraint or multiobjective utility was frozen in the original experiment. The disagreement between MAE and MSE may arise from differences in error distributions; tail behavior was not separately tested here. These associations do not show that biological RIM–AIY feedback implements an energy-efficient policy, nor that sensory-site feedback has a generally superior Pareto frontier.

The clearest next experiment is a separately frozen multiobjective comparison that directly manipulates energy budget or command penalty, uses independent seeds, preserves the original site-placement controls, and includes a strong action-conditioned recurrent baseline. It must treat accuracy, energy, and switch latency as separate native outcomes, with one prespecified primary utility or constrained objective. No such follow-up result is claimed here.

## Reproduction

Run `python3.12 -W error model/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/analyze_tradeoffs.py`, then `python3.12 -W error model/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/verify_tradeoffs.py`. The independent verifier recalculated all 24 reported contrasts from the 700-row seed summary and checked bootstrap intervals, direction counts, and input/output hashes. The scripts write [paired contrast estimates](../../data/results/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/POSTRUN_TRADEOFF_CONTRASTS.csv), a hash-bearing [analysis manifest](../../data/results/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/POSTRUN_TRADEOFF_ANALYSIS.json), and a [verification record](../../data/results/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/POSTRUN_TRADEOFF_VERIFICATION.json). The fitted models and original outcomes are not modified.
