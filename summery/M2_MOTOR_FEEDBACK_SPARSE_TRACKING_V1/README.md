# M2 motor-feedback sparse-sensation tracking V1

This exploratory study tests whether feeding a previous motor command into a sensory-state update helps a one-dimensional controller track a telegraph target when relative-position sensations are intermittently absent. The biological motivation is the reported RIM-to-AIY motor-state feedback in *C. elegans* thermotaxis; the artificial task is not a worm model.

## Outcome

In the training condition (target-switch hazard `1/120`, 50% missing samples), the sensory-site model had mean MSE `0.2581`, versus `0.3020` for a three-parameter one-state generic RNN. The primary paired difference was `+0.04386` (crossed 95% interval `[+0.04247,+0.04526]`, positive in 32/32 training-seed clusters). It also beat output-site persistence and no feedback by `+0.00403` and `+0.00416`. The oracle still performed better.

The gain did not generalize uniformly: under slower target changes with 75% missing observations, the sensory-site update was worse than both direct controls. The defensible result is a conditional benefit in this artificial closed-loop task, accompanied by an operating boundary and a stronger task-aware estimator.

## Records

- Frozen experiment setup: [`CONTRACT.md`](CONTRACT.md)
- Full results and claim boundaries: [`RESULTS.md`](RESULTS.md)
- Limitations and follow-up failures: [`FAILURE_LOG.md`](FAILURE_LOG.md)
- Runnable code and independent verifier: [`model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/`](../../model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/)
- Raw episode rows, fit records, results, figure, and hashes: [`data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/`](../../data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/)

This line does not establish biological-to-AI transfer, general AI benefit, or NMI publication readiness on its own. The next useful experiment should stress stronger generic recurrent controls, multiple initialization families, and ambiguous rather than exact-zero missing observations.
