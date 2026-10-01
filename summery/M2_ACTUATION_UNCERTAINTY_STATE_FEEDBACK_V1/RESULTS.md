# M2 actuation-uncertainty state-feedback dose test V1 — results

## Classification

Outcome-informed exploratory artificial experiment. Six disjoint preflight seed blocks were inspected before the 32-block run, and earlier M2 results informed the question. The preflight is disclosed in `data/results/M2_ACTUATION_UNCERTAINTY_STATE_FEEDBACK_V1/PREPILOT.json`; this is not confirmatory evidence or biological validation.

## Primary result

The preregistered dose interaction, `(ACTION_STATE − SELF_STATE) MSE at p_reverse=.40 − the same contrast at p_reverse=0`, was **+0.11051 MSE** (95% paired training-seed-block bootstrap interval **[+0.05341, +0.16633]**, 32 blocks). Positive values favor realized movement-state input more at the high reversal dose than at zero reversal.

The contrast favored `SELF_STATE` at each dose: `ACTION_STATE − SELF_STATE` was +0.06238 at 0, +0.09884 at .10, +0.27120 at .25, and +0.17288 at .40. Thus the dose response was not monotonic: the contrast peaked at .25 and fell at .40, while remaining positive. The positive interaction supports a bounded dose-dependent difference, not a claim that state feedback only helps under uncertainty.

At p_reverse=.40, `SELF_STATE` also beat `ZERO_STATE` by 0.16543 MSE (95% interval [0.10856, 0.22267]) and `YOKED_STATE` by 0.18261 (95% interval [0.12344, 0.24169]); these are sign-reversed from the stored `SELF_STATE − control` contrasts. The reactive reference's comparison is descriptive and is not capacity matched. The full canonical outputs contain arm-level means and all seed-block contrasts.

## Interpretation

In this simulator, the realized sign of movement velocity carries information that improves a trained GRU's tracking performance relative to its preceding action sign, and that advantage changes with the imposed actuator-reversal dose. The positive advantage at zero reversal, nonmonotonic dose pattern, and synthetic task limit mechanistic interpretation. The experiment does not establish the biological implementation of RIM→AIY feedback, worm-to-AI transfer, general AI benefit, or a unique biological computation.

## Reproducibility

The full 32-block run and an independent full rerun both passed the verifier, including row completeness, parameter/update accounting, recomputed summaries and interaction, exact yoke distribution checks, and output/source hashes. Episode outcomes, seed summaries, yoke checks, and summary JSON were byte-identical. Fit records were identical after excluding the nondeterministic runtime field `training_seconds`. See `data/results/M2_ACTUATION_UNCERTAINTY_STATE_FEEDBACK_V1/canonical/RERUN_VERIFICATION.json` and the figure QA record in `figures/FIGURE_QA.json`.
