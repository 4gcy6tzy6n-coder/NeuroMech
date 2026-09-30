# Failure and limitation log

## Adverse boundary observed

- At 5-s gradient reversals, the self-contingent arm was slightly below the yoked arm: −0.00139 model-distance units/s (95% seed-block bootstrap interval −0.00261 to −0.00019). Do not hide this schedule or describe self-contingency as uniformly beneficial.
- At 10-s reversals the positive difference is much smaller than at 20–40 s or a stationary gradient (+0.01796 units/s), consistent with a rapidly shrinking advantage as the environment changes faster.

## Design limits

- The yoke is a fixed cross-agent permutation of feedback trajectories from the paired self-feedback arm. It exactly preserves the population distribution of feedback values at each time point, but it does not match recipient-specific temporal autocorrelation or the interaction between the signal and the recipient's counterfactual state.
- The source model is a compact computational abstraction. The calculation does not test whether biological RIM-to-AIY feedback has the same dynamics or establishes a synapse-specific effect.
- Simulation seeds are computational blocks, not biological independent units. Bootstrap intervals quantify variation across this simulation design only.
- Prior M2 outcomes were already known. This experiment is retrospective and exploratory, not an independent confirmation or preregistered biological test.
- No artificial-learning benchmark was run. This package provides no AI transfer result.

## Previous control failure retained in context

The preceding gradient-reversal experiment's nominal output-site control saturated at full forward-state occupancy and could not identify a feedback-site effect. This experiment does not repair that output-site comparison; it addresses a different discriminator within the sensory-site feedback model.
