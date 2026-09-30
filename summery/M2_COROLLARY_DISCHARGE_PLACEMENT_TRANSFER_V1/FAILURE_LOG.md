# Failure and limitation log

## Adverse outcomes retained

- Sensory-site feedback did not beat the no-feedback model in the primary `h=0.05` condition (88.94% vs 89.05%).
- The generic two-unit RNN (90.21%) and task-aware Bayes filter (90.30%) also exceeded the sensory-site model in the primary condition.
- At low hazard `h=0.01`, output persistence was more accurate than sensory-site feedback and made fewer false action switches.
- At high hazard `h=0.20`, sensory-site feedback did not match no-feedback, the generic RNN, or Bayes accuracy.

## Interpretation boundaries

- The positive primary result is a relative comparison to an output-inertia yoke. It does not establish that adding the biological abstraction improves performance over a no-feedback learner.
- Switch hazards and observation noise are synthetic; their values are not estimated from the worm's natural environment.
- The generic RNN has more parameters than the three-parameter site-placement models. The decisive placement comparison is parameter matched; the generic RNN and Bayes filter are stronger references.
- All M2 findings are outcome-informed at the project level. This is exploratory, not an independent confirmatory validation.
- No implementation incident was observed; the full run and independent verifier completed. Runtime fields are environment dependent.
