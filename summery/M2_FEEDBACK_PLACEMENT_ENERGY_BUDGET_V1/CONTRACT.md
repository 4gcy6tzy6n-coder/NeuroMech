# M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1 — validation-selected control under an energy budget

**Classification:** post-result exploratory artificial mechanism-transfer follow-up. The design was motivated by prior M2 outcomes, including `M2_SENSORIMOTOR_TRANSIENT_FILTER_V1`; it is not an independent project-level confirmation or biological validation.

## Biological motivation and claim boundary

Ji et al. report that motor-circuit feedback contributes to AIY motor-state representation and sustained forward behavior during thermotaxis. This motivates asking whether the *placement* of actual motor-state information changes a controller's held-out accuracy when command effort is constrained. The source does not report an energy budget, command-energy penalty, or any of the artificial model equations used here. This is a source-inspired engineering test, not a reconstruction of the C. elegans circuit.

## Question and primary hypothesis

On a fresh synthetic tracking sample, can a scalar sensory-site feedback controller achieve lower held-out movement MAE than an equal-parameter output-site feedback controller after each controller's energy-penalty coefficient is selected on disjoint validation episodes to meet a fixed mean command-energy budget?

The budget is **mean command energy ≤ 0.50**. It was set after inspecting the previous experiment, where the sensory-site and output-site mean command energies were approximately 0.46 and 0.58 in the transient-pulse condition. Therefore all inferences remain post-result exploratory. The primary outcome is the seed-block paired difference `SENSORY_SITE_1D − OUTPUT_SITE_1D` in held-out `TRANSIENT_PULSE` movement MAE. Negative values favor sensory-site placement. A placement comparison at the specified budget is interpretable only if both selected policies also meet the budget on the held-out primary episodes; otherwise report budget generalization failure.

## Task and data separation

The task uses the same documented 1D motor plant and target/sensory generator as V1, with new training, validation, and test random streams. Test episodes are never used to choose the penalty coefficient. Sixteen paired seed blocks are used. Each block trains every architecture/penalty arm on identical generated training streams. Validation and test have distinct seed ranges and use common episode seeds across candidate arms within a condition.

Evaluation conditions are `TRANSIENT_PULSE`, `SUSTAINED_SWITCH`, and `COMBINED_STRESS`, using the hazard, pulse-rate, and duration definitions in V1. Each candidate is scored on 32 validation episodes per condition; the validation-selected policies are evaluated on 64 fresh test episodes per condition.

## Model arms and optimization

Fitted arms are `SENSORY_SITE_1D` (4 parameters), `OUTPUT_SITE_1D` (4), `NO_FEEDBACK_1D` (3), `GENERIC_RNN_1D` (6), and `GRU_8` (297). The first two are the primary placement comparison. All receive the same 100 Adam updates, batch size 32, sequence length 96, learning rate 0.01, and gradient clipping at 5. Training loss is `movement_MSE + λ × mean(u²)`. The penalty grid is fixed at `λ ∈ {0, 0.1, 0.3, 0.6}` for every model.

For each seed block and fitted arm, choose a single λ using validation data pooled with equal weight across the three conditions: among candidates with mean validation command energy ≤0.50, select the candidate with lowest mean validation movement MAE. Break ties by smaller λ. If no candidate meets the validation budget, mark that arm/seed block `NO_VALIDATION_POLICY_WITHIN_BUDGET`, and use the lowest-energy λ only for descriptive test reporting; do not count it as budget-feasible.

## Outcomes and analysis

The seed block is the unit for uncertainty (`n=16`). For the primary contrast, report the mean paired seed-block MAE difference and percentile bootstrap 95% interval (20,000 resamples). Report held-out energy for both primary arms and whether each satisfies the 0.50 budget. Budget transfer is established only if the upper endpoint of each arm's 95% seed-block bootstrap interval for held-out primary-condition energy is ≤0.50. If either arm fails that criterion, classify the budget-constrained site comparison as `NOT_ESTABLISHED`, while retaining the test metrics.

Secondary outcomes are movement MSE, sign accuracy, command energy, and switch latency. Report selected-arm test results in all three conditions and every arm's full validation selection table. Comparisons to generic recurrence and GRU are descriptive in this exploratory follow-up; parameter counts and training time must be reported, and equal update count is not described as equal compute. No post-result change to the penalty grid, energy budget, endpoint, or validation selection rule is allowed for this run.

## Interpretation limits

A positive outcome would support only a validation-selected controller comparison in this synthetic task. It would not establish that the biological mechanism minimizes energy, improves a real AI system, or transfers across task families. A negative or budget-infeasible result narrows the tested artificial translation; it does not refute the biological finding. Because the question and budget were selected after a prior outcome, the experiment cannot be described as independent confirmation.

## Reproducibility

The preflight pins the contract, runner, verifier, environment, seeds, arm counts, and test seed rules before execution. The verifier recomputes validation policy selection, row completeness, output hashes, held-out budget status, and the primary seed-block bootstrap. A separate full run must reproduce held-out episode metrics and selections before publication of this experiment round.
