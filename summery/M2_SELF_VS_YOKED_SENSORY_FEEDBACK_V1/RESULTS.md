# Results: M2 self-contingent versus yoked sensory feedback

**Experiment:** `M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1`
**Status:** completed retrospective exploratory source-model probe.
**Question:** does recipient-specific sensory-site feedback add to the effect of an identical instantaneous population distribution of feedback signals?

## Primary result

At the prespecified 20-s gradient-reversal schedule, self-contingent feedback exceeded cross-agent yoked feedback by **0.04618 model-distance units/s** (95% seed-block percentile-bootstrap interval **0.04252 to 0.04994**; 100 paired simulation blocks positive, 0 negative). Mean aligned progress was 0.08573 with self-contingent feedback, 0.03955 with yoked feedback and 0.01114 with no feedback.

The yoke used a fixed derangement of the paired self-arm agents' feedback traces. At every time step, the sorted feedback values over all 50 agents were exactly equal between self and yoke (`max_sorted_feedback_value_difference = 0` in all 500 seed-by-schedule checks). Thus the primary difference is consistent with recipient-specific temporal contingency contributing beyond the instantaneous population-level signal distribution in this model. This is a source-model result, not a biological causal estimate.

## Reversal-rate boundary

| Gradient schedule | Self mean progress | Yoked mean progress | Self − yoked (95% block-bootstrap interval) | Positive blocks |
|---|---:|---:|---:|---:|
| Stationary | 0.10629 | 0.03797 | +0.06832 (+0.06145, +0.07519) | 98/100 |
| Reverse every 40 s | 0.11051 | 0.04610 | +0.06441 (+0.05867, +0.07008) | 99/100 |
| Reverse every 20 s (primary) | 0.08573 | 0.03955 | +0.04618 (+0.04252, +0.04994) | 100/100 |
| Reverse every 10 s | 0.05081 | 0.03284 | +0.01796 (+0.01585, +0.02009) | 98/100 |
| Reverse every 5 s | 0.01713 | 0.01852 | −0.00139 (−0.00261, −0.00019) | 41/100 |

The sign reversal at the fastest schedule is small in absolute units but its bootstrap interval is below zero. This defines a model-specific boundary: very fast changes erase or slightly reverse the self-contingency advantage. The schedule-wise intervals are descriptive; they are not multiplicity-adjusted, and no broad threshold claim is made.

## Interpretation and limitations

The result strengthens the prior source-model observation by showing that replaying feedback with the same instantaneous population distribution is not sufficient to recover the self-feedback arm's progress at the 20-s schedule. It helps separate recipient-specific contingency from generic positive drive in this equation set.

The yoke reassigns signals recorded from the paired self-feedback arm after those trajectories have unfolded. This replay preserves the signal multiset at each instant but does not preserve each recipient's temporal history, its autocorrelation, or the signal's relation to that recipient's counterfactual state. Those are intentional consequences of disrupting self-contingency and also limit causal interpretation. The tested agents are simulations, not animals; the experiment does not establish a unique biological synapse or demonstrate AI-system benefit. Prior outcomes were known, so the analysis is retrospective and exploratory.

## Reproducibility

- Raw seed-block metrics: [`seed_block_metrics.csv`](../../data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical/seed_block_metrics.csv)
- Figure and source data: [`Figure_M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1.pdf`](../../data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical/Figure_M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1.pdf), [`figure_source_data.csv`](../../data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical/figure_source_data.csv)
- Run manifest and checks: [`run_manifest.json`](../../data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical/run_manifest.json), [`feedback_distribution_check.json`](../../data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical/feedback_distribution_check.json)
- Figure legend: self-minus-yoked environment-aligned displacement rate (model-distance units/s) across five warm-gradient reversal schedules. Points show paired means over 100 simulation seed blocks; bars show two-sided 95% percentile-bootstrap intervals (20,000 resamples). The horizontal dashed line marks zero. The primary 20-s schedule is highlighted. This retrospective simulation-only analysis is not biological validation or evidence of AI benefit. Source data are provided in `figure_source_data.csv`.
