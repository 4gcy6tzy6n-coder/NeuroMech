# M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1 — results

## Classification

This is a post-result exploratory artificial follow-up motivated by earlier M2 simulations. It tests the defined controllers in one synthetic motor-control task; it is not biological validation, independent confirmation, or evidence of broad AI benefit.

## Frozen question and execution

Sixteen paired training seed blocks compared a sensory-state feedback controller and an output-site feedback controller after each arm's energy-penalty coefficient was selected on separate validation episodes. The validation rule selected the lowest-MAE candidate across three equally weighted conditions among those with mean command energy at or below 0.50. The primary endpoint was held-out `TRANSIENT_PULSE` movement MAE, with sensory-site minus output-site as the contrast. Negative values favor sensory-site. The budget was chosen after inspecting the preceding M2 study, so the follow-up is outcome-informed.

The corrected canonical run has 320 fitted candidates, 30,720 validation episodes, 80 selected policies, 15,360 test episodes, and 240 seed-block/arm/condition summaries. All 16 blocks had validation-budget-feasible policies for both primary arms.

## Primary result

The mean paired contrast was `+0.01428` movement MAE (95% percentile seed-block bootstrap interval `[-0.00106, +0.02960]`, 16 blocks). The point estimate favors output-site feedback, while the interval includes zero. The result does not establish a sensory-site advantage or a reliable output-site advantage under this budget and task.

Held-out transient-pulse command energy was `0.4401` for sensory-site feedback (95% interval `[0.4100, 0.4656]`) and `0.4558` for output-site feedback (`[0.4300, 0.4825]`). Both upper interval endpoints were below the frozen `0.50` budget; the budget-transfer criterion was met for these arms and this condition.

## Descriptive controls

Transient-pulse test mean movement MAE / command energy were: sensory-site `0.4836 / 0.4401`, output-site `0.4693 / 0.4558`, no feedback `0.5166 / 0.4296`, generic scalar RNN `0.5011 / 0.4291`, and GRU-8 `0.5915 / 0.3204`. These are descriptive comparisons; the primary inferential contrast was only between the two validation-selected placement arms. The three-condition results and validation-selected penalties are in the canonical CSVs.

## Interpretation

Under this task and the chosen energy budget, both feedback-placement controllers transferred their selected policies to test episodes within the stated budget. The sensory-site controller did not outperform output-site feedback on the primary accuracy endpoint. Lower error and lower command energy did not coincide in the primary means, but this experiment did not freeze or test a Pareto-optimality claim. The GRU's high energy-penalty selection and lower command energy do not make it a better controller; its movement MAE was higher in this condition.

This result narrows the tested artificial translation. It does not show that RIM feedback is biologically energy-efficient, does not refute the biological mechanism, and does not establish an AI inductive-bias benefit. Because the budget was selected after a previous outcome, it is not an independent confirmation.

## Verification and reproducibility

`verify_results.py` passed row coverage, unique validation/test keys, parameter counts, validation-only penalty selection, seed-level aggregation, the primary bootstrap, output hashes, and held-out budget status. An independent full rerun reproduced `validation_episodes.csv`, `selection_manifest.csv`, `test_episodes.csv`, `test_seed_summary.csv`, and `summary.json` byte-for-byte; all fit-manifest fields except wall-clock timing also matched. See `data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/canonical/REPRODUCIBILITY.json`.

The first execution was invalid because an evaluator loop duplicated all 16 evaluation blocks for each fitted seed block. The structural verifier caught the incorrect row count before the first run was interpreted. That run is preserved in compressed form under `data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/invalid_initial_execution/` and is excluded from all reported estimates. The code-only correction and initial-run disposition are recorded in [execution incident 01](EXECUTION_INCIDENT_01.md).

## Artifacts

- Frozen design: [CONTRACT.md](CONTRACT.md)
- Corrected preflight: [`PREFLIGHT_CORRECTED_01.json`](../../data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/PREFLIGHT_CORRECTED_01.json)
- Runner and verifier: [`model/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/`](../../model/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/)
- Canonical outputs: [`data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/canonical/`](../../data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/canonical/)
- Invalid initial execution and hashes: [`data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/invalid_initial_execution/`](../../data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/invalid_initial_execution/)
