# NeuroMech project convergence — 2026-10-01

## Purpose of this record

This is a project-level synthesis, not a new experiment and not an experiment result. It records the current evidence base and narrows the next experimental phase to a small number of studies that can address one shared scientific question. It does not replace or revise any experiment contract or archived result.

## Current project status

The repository contains completed model runs and source-data analyses across M1, M2, M4–M10. The project has started experiments; the current problem is that their outcomes are distributed across mechanism-specific folders and do not yet establish one shared positive claim. Several results are null, adverse, inconclusive, or explicitly exploratory. They must remain visible in any manuscript synthesis.

## Candidate central proposition

> A biologically grounded computation is useful as an artificial inductive bias only when its defining contextual signal carries information relevant to the task, and its benefit must survive mechanism-targeted and capacity-matched comparisons.

This is a testable working proposition, not a conclusion established by the current results. The mechanisms remain biologically distinct. No shared neuron identity, circuit, or raw outcome is implied across modules.

## Evidence-to-claim table

| Line | What the current record supports | What it does not establish | Role in a converged study |
|---|---|---|---|
| M1 / RR19 higher-order correction | The partial natural-scene run found the predicted direction for H1 and H3. | H2, the phase-mismatched specificity control, went strongly in the opposite direction; H4's available follow-up did not establish the frozen monotonicity claim. No complete four-hypothesis verdict exists. | Preserve as an important boundary/counterexample. Do not report as a successful mechanism-specific transfer result. Any new test must be separately identified and use a valid new input/evaluation sample. |
| M2 / AFD–AIY–RIM feedback | Published cell-class-level intervention and activity evidence supports motor-state feedback affecting AIY representation and forward-run persistence in the studied thermotaxis context. A source-data reanalysis is descriptively consistent with shorter runs after RIM ablation. V3 now finds a model-specific sensory-site advantage over a mean-run-duration-calibrated motor-only control across three imposed noise scales. | The public event sheet lacks animal/session IDs; the reanalysis cannot support animal-level uncertainty. V3 is an outcome-informed source-model simulation, and its control matches only mean run duration; full distributions and internal dynamics differ. Synthetic noise scales are not measured biological boundary conditions. | Retain as a biological computation case. V3 strengthens the feedback-site distinction inside the source model, but does not establish animal-level inference or AI transfer. A generic/adaptive capacity-matched comparison is still needed. |
| Cross-mechanism benchmark | The project has not yet run one shared benchmark with consistent resource accounting and matched counterfactuals. | Existing M1 and M2 outcomes use different tasks, units, estimands, and experimental status; their raw metrics cannot be pooled into one effect. | Build one benchmark harness with per-mechanism task adapters and identical comparison rules. Report within-task contrasts separately; a joint claim requires both mechanisms to meet their own frozen criterion. |

## Audit of work already completed

The “no experiments have started” premise is contradicted by the current repository. For example:

- M1 H1–H3 partial computation and M1 H4 post-result follow-up are recorded in [`RR19_STEP4_PARTIAL_RESULTS.md`](../../experiments/m1_higher_order/RR19_STEP4_PARTIAL_RESULTS.md) and [`RR19_H4_EXTERNAL_POSTRESULT_INTERPRETATION.md`](../../experiments/m1_higher_order/RR19_H4_EXTERNAL_POSTRESULT_INTERPRETATION.md).
- M2 feedback-site V2 reports a positive warm-direction-index contrast after matching mean run duration, while documenting remaining dynamical mismatches in [`M2_JI2021_FEEDBACK_SITE_CONTROL_V2_RESULTS.md`](../M2_JI2021_FEEDBACK_SITE_CONTROL_V2/M2_JI2021_FEEDBACK_SITE_CONTROL_V2_RESULTS.md).
- M2 feedback-site V3 extended that source-model comparison to three imposed noise scales and 200 new held-out seed blocks. The equal-weighted warm-direction-index difference was `+0.08057` (95% CI `[+0.07752,+0.08357]`, 200/200 positive blocks); run-duration distributions remained unmatched. Full result: [`M2_FEEDBACK_SITE_SPECIFICITY_V3/RESULTS.md`](../M2_FEEDBACK_SITE_SPECIFICITY_V3/RESULTS.md).
- M2 V4 used V3 development data to select a motor-only coefficient by a standardized loss over four run-duration summaries, then evaluated 200 new blocks. The warm-direction contrast was `+0.14128` (95% CI `[+0.13798,+0.14460]`, 200/200 positive), but the control still failed to match persistence (for noise 0.75, mean duration differed by `2.506 s` and p90 by `8.810 s`). This is a failed control-matching attempt, not stronger feedback-site evidence. See [`M2_FEEDBACK_SITE_SPECIFICITY_V4/RESULTS.md`](../M2_FEEDBACK_SITE_SPECIFICITY_V4/RESULTS.md).
- M2 closed-loop, learned-gain, and state-gated inference runs are retained with negative or inconclusive comparisons against generic/adaptive controllers.
- Other mechanism experiments M4–M10 are also present. Their outcomes do not automatically become evidence for the M1/M2 proposition.

These records show that the project needs synthesis and stronger comparative experiments, not another broad search for candidate datasets.

## Converged experimental package

### Study 1 — M1 higher-order correction boundary

Use the existing partial result as historical evidence. The reported H2 reversal and incomplete H4 analysis stay attached to the result. Do not relabel it as a pass, retroactively repair the original run, or reuse it as independent confirmation. If M1 remains a principal case, its next study must use a separately specified dataset/evaluation sample and compare source-specific correction against a capacity-matched generic correction and a mismatch control.

### Study 2 — M2 feedback-site specificity

Retain the real biological source evidence at cell-class granularity. The artificial comparison must distinguish feedback at the sensory-processing site from action persistence and generic residual-based adaptation, with equal training data, parameter count, compute budget, and held-out task conditions. Evaluate the boundary where the feedback state is informative and where its relationship to sensory reliability is absent or reversed. Existing outcomes are exploratory and do not count as a fresh confirmatory run.

### Study 3 — unified benchmark harness

Implement the same preregistered accounting and analysis interface for Studies 1 and 2: shared seed discipline, train/validation/test separation, resource reporting, paired uncertainty, and a mechanism-targeted control. Preserve each task's native primary outcome. Do **not** pool raw Q, navigation error, or behavior measures; make the project-level claim conjunctive across the two task-specific outcomes.

## Immediate execution work

1. Create the benchmark specification and runner under `experiments/cross_mechanism/` and `model/CROSS_MECHANISM_BENCHMARK_V1/`.
2. M2 V3–V4 show a source-model difference, but V4's broader summary calibration still did not match persistence. The next M2 comparison needs an independently calibrated full-process persistence yoke or an explicit adequacy check before outcomes; a new AI-transfer claim also requires a separate abstract-task benchmark against a capacity-matched generic controller.
3. Resolve the M1 input limitation before claiming a new fixed-skewness test: the frozen raw image substrate needed for H4 is incomplete. Existing author-precomputed outputs do not replace raw inputs. A separate synthetic stress test can proceed only if it is clearly labeled as a new artificial experiment and does not claim to complete the original H4 analysis.
4. Implement the unified benchmark with per-mechanism task adapters and common resource accounting. Preserve task-native outcomes; require each mechanism's own matched-control result before making a joint claim. If M1 cannot obtain valid new inputs, report that limitation and do not let M2 alone carry a cross-mechanism claim.
5. Save code in `model/`, outcomes in `data/results/`, and the experiment contract, interpretation and failure experience in `summery/`. Push each completed experiment as its own commit to `experiment-publication`.

## Stop conditions for claims (not for doing work)

- A successful benchmark supports only the tested computation, task, and boundary conditions; it does not establish a general AI advantage.
- A negative or mixed result is retained and narrows the mechanism's operating conditions; it is not repaired by changing metrics after inspection.
- No artificial result is described as a new biological validation.
- Publication readiness remains unestablished until the unified studies, complete provenance, independent verification, and manuscript-level novelty assessment are finished.

## Decision

The active work is **convergence and comparative experimentation**, not candidate expansion. M2 V3–V4 supply positive source-model feedback-placement contrasts, but V4 does not remove persistence mismatch and neither run establishes AI transfer. The next project deliverable is the shared benchmark implementation with mechanism-specific capacity controls; M1's incomplete frozen H4 inputs and M2's unresolved control adequacy remain explicit limitations.

## 2026-10-01 Phase 2 concept-admission update — current active pointer

The earlier “Immediate execution work” and “Converged experimental package” sections are historical plans and are superseded as current next actions by the owner's request to stop adding scattered experiments until the target NeuroMotif class is defined. The seven-term concept review found no concept presently admissible for cross-system computation. Feedback accessibility remains only a definition-check candidate: a current role audit found a named RIM-to-AIY class-level pair in the worm, but no outcome-independent source/target role map in Fish1.5 and no synapse-resolved return path in R20-01. Therefore no graph reachability computation, new biological analysis, or model run is opened from this review.

```text
PHASE2_CONCEPT_GLOSSARY = SEVEN_PROVISIONAL_TERMS
CROSS_SPECIES_CONCEPT_ADMITTED = NONE
NEW_SCATTERED_EXPERIMENTS = PAUSED
CURRENT_NEXT_WORK_PACKAGE = CLAIM_AND_CONTRIBUTION_REPLAN_FROM_COMPLETED_EVIDENCE
```

See [`PHASE2_CONCEPT_ADMISSION_REVIEW.md`](PHASE2_CONCEPT_ADMISSION_REVIEW.md) and [`PHASE2_MAINLINE_RESOLUTION.md`](PHASE2_MAINLINE_RESOLUTION.md). This update does not change any registered experiment, result, or model contract.

## 2026-10-01 Owner direction update — experimental work resumed

The owner subsequently directed the project to stop treating prior gate and phase recommendations as blockers and to continue toward a publishable biological-computation-to-AI result. The `NEW_SCATTERED_EXPERIMENTS = PAUSED` line above records the earlier decision only; it is superseded as an active work restriction. Biological evidence and artificial outcomes remain separately labeled, and unfavorable results remain part of the evidence base.

The first resumed experiment is [`M2_LOW_DATA_GATING_V1`](../M2_LOW_DATA_GATING_V1/RESULTS.md): an equal-parameter, equal-sample-token comparison across four training-set sizes. The state-conditioned update improved MSE over an additive scalar RNN in the aligned synthetic mapping, while the result reversed under independent and reversed mappings. It did not demonstrate a low-data dose-response or biological validation. This advances the AI-side comparison but does not complete the cross-mechanism benchmark or the project-level claim.
