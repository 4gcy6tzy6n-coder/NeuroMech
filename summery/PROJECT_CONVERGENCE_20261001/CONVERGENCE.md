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

This historical phase decision does not change any registered experiment, result, or model contract. The current evidence and novelty assessment is in [`NMI_CLAIM_AND_NOVELTY_AUDIT_20261001.md`](../NMI_CLAIM_AND_NOVELTY_AUDIT_20261001.md).

## 2026-10-01 Owner direction update — experimental work resumed

The owner subsequently directed the project to stop treating prior gate and phase recommendations as blockers and to continue toward a publishable biological-computation-to-AI result. The `NEW_SCATTERED_EXPERIMENTS = PAUSED` line above records the earlier decision only; it is superseded as an active work restriction. Biological evidence and artificial outcomes remain separately labeled, and unfavorable results remain part of the evidence base.

The first resumed experiment is [`M2_LOW_DATA_GATING_V1`](../M2_LOW_DATA_GATING_V1/RESULTS.md): an equal-parameter, equal-sample-token comparison across four training-set sizes. The state-conditioned update improved MSE over an additive scalar RNN in the aligned synthetic mapping, while the result reversed under independent and reversed mappings. It did not demonstrate a low-data dose-response or biological validation. This advances the AI-side comparison but does not complete the cross-mechanism benchmark or the project-level claim.

The subsequent [`M2_LOW_DATA_GATING_V2`](../M2_LOW_DATA_GATING_V2/RESULTS.md) replaced the additive comparator with a parameter-matched bilinear tanh recurrent model on disjoint seeds. The mode-gain update had lower MSE in all three mapping conditions, including reversed context. Its absolute error nonetheless rose under reversal, and the persistent relative advantage does not isolate aligned context as the causal source of its performance. Across V1 and V2, the result is sensitive to comparator dynamics and does not yet establish the central biological-to-AI claim. The next benchmark must include a context-free state-space estimator, a linear bilinear update, and a task-aware reference.

[`M2_LOW_DATA_GATING_V3`](../M2_LOW_DATA_GATING_V3/RESULTS.md) then ran those controls on new seeds. The state-conditioned filter improved over the context-free filter in ALIGNED (`+0.00899` MSE difference, 95% CI `[+0.00847,+0.00946]`) but was worse in INDEPENDENT and REVERSED mappings; a known-parameter Kalman oracle was best in all conditions. This sharpens the artificial result to an alignment-dependent benefit and mismatch cost. The biological mapping remains untested, and the next AI transfer step should use a task family defined independently of this synthetic observation equation.

[`M2_SEQUENTIAL_DECISION_V1`](../M2_SEQUENTIAL_DECISION_V1/RESULTS.md) tested the same operation on a different objective: terminal binary decisions from sequential noisy evidence. In ALIGNED, mode-gain accuracy exceeded constant gain by `+0.06448` (95% CI `[+0.05703,+0.07232]`); under INDEPENDENT and REVERSED mappings, it fell behind by `−0.02678` and `−0.11765`. The Bayes posterior remained stronger. This extends the artificial operation across task objectives but still uses a synthetic context/evidence relation, so it does not validate a biological transfer claim. It is not an independent mechanism or biological replication.

The later [`M2_CONTEXT_INFORMATION_DOSE_V1`](../M2_CONTEXT_INFORMATION_DOSE_V1/RESULTS.md) measured the continuous-estimation operating boundary across 11 context doses. A filter trained under full alignment beat the context-free update only above an estimated κ crossover of `0.285` (crossed-bootstrap 95% interval `[0.251,0.318]`); at κ `0.20` it remained worse, and κ `0.30` was unresolved. The [`M2_DECISION_CONTEXT_DOSE_V1`](../M2_DECISION_CONTEXT_DOSE_V1/RESULTS.md) then carried the same dose relation into terminal decisions. Its estimated crossover was `0.134` (95% interval `[0.072,0.200]`), with advantage first clear at the tested κ `0.20`. The cross-objective shift is an artificial-model result, not a measured biological threshold. Together these experiments sharpen the current AI-side proposition: context-gated updates can help under sufficiently strong context/task alignment, but the operating boundary depends on the task objective and training shift, and a task-aware Bayesian reference remains stronger. Neither experiment closes the biological-to-AI transfer gap.

The next M2 step left the scalar context/evidence generator for [`M2_2D_CLOSED_LOOP_PURSUIT_V1`](../M2_2D_CLOSED_LOOP_PURSUIT_V1/RESULTS.md), a new 2D closed-loop target-pursuit task with 8-parameter additive and bilinear recurrent baselines. This did not support the transfer claim: in the aligned environment, mode gain had higher final distance than the bilinear baseline by `0.02088` (95% crossed interval for bilinear minus mode `[-0.03244,-0.01055]`), and its direct context-free ablation was similar. Under the reversed mapping, mode-gain success fell to 30.2%, while the constant-gain control reached 86.0%. Notably, mode-gain had the best teacher-forced residual-estimation loss, yet lost on the closed-loop objective, indicating an estimator-training/deployment mismatch in this artificial task. This is retained as adverse evidence and narrows the mechanism's current AI-side operating claim. The mapping remains invented and does not validate the biological circuit.

This closed-loop result advances the cross-task audit but does not complete the M2-to-AI case. Any follow-up should first distinguish whether the loss arose from the chosen supervised training distribution or from the mechanism-shaped update itself; report the present V1 as the primary tested result and identify any on-policy training comparison as a separate, outcome-informed study. Preserve source-model, dose-response, and closed-loop outcomes separately; do not pool their unlike metrics.

## 2026-10-01 M2 V2 training-distribution diagnostic

The post-result [`M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC`](../M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/RESULTS.md) compared random-action training with shared Bayes-teacher trajectories mixed with 25% random exploration. With fresh training seeds and paired targets/noise, the aligned bilinear-minus-mode final-distance contrast shifted from `−0.01885` (95% crossed interval `[−0.02791,−0.01059]`) to `+0.00394` (`[+0.00051,+0.00750]`); the predeclared training-regime interaction was `+0.02279` (`[+0.01341,+0.03318]`). This shows that the training trajectory policy materially changes this pairwise ranking and is consistent with distribution mismatch contributing to V1. It does not isolate the only cause: teacher-generated occupancy may favor some estimators and disadvantage others. Under teacher-mixed training, the additive matched control still had lower final distance, and MODE_GAIN remained mapping-sensitive. V2 is post-result and exploratory, not independent confirmation or biological-to-AI validation. The full 153,600 rows, verifier output, and independent rerun are documented in the experiment record.

## 2026-10-01 M2 corollary-discharge placement transfer

The post-result [`M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1`](../M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/RESULTS.md) directly compared motor-state feedback at a sensory-state update with equal-parameter output-action persistence. At the training hazard 0.05, sensory-site feedback exceeded output persistence by `+0.06799` accuracy (crossed 95% interval `[+0.06475,+0.07120]`). It did not beat no feedback (88.94% vs 89.05%), the two-unit generic RNN (90.21%), or the Bayes reference (90.30%). Its switch-recovery lag was shorter than the output-persistence control (1.30 vs 3.56 steps). At the low hazard, output persistence was more accurate; at the high hazard, sensory-site feedback remained below no-feedback, generic and Bayes accuracy. This supports a bounded effect of feedback placement on stability/switching behavior relative to an output-inertia yoke, not a general AI advantage. The synthetic task does not reproduce *C. elegans* thermotaxis and is not biological validation.

## 2026-10-01 M2 source-model gradient-reversal stress test

[`M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1`](../M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/RESULTS.md) applied direction reversals to the corrected Ji et al. Figure 7 source equations. At a 20-second reversal interval, sensory-site feedback exceeded the no-feedback ablation by `+0.07379` environment-aligned progress units per second (95% paired interval `[+0.07061,+0.07694]`; 100/100 simulated seed blocks positive). The effect weakened as reversals accelerated. The same feedback coefficient placed in the motor equation saturated the output arm at 100% forward occupancy and 200-second runs, making the nominal placement contrast uninterpretable as a matched-dynamics effect. This is a source-model simulation result and a control-design failure, not animal-level inference or AI transfer. The follow-up cross-agent yoke is recorded in the section below.

---

## 2026-10-01 M2 source-model self-contingency probe

[`M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1`](../M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/RESULTS.md) followed that discriminator: each self-feedback trajectory was compared with a cross-agent replay that exactly preserved the feedback-value distribution over agents at every time step. At 20-s reversals, the self-contingent arm exceeded the yoke by `+0.04618` aligned-progress units/s (95% paired seed-block bootstrap interval `[+0.04252,+0.04994]`; 100/100 blocks positive). The advantage narrowed to `+0.01796` at 10-s reversals and slightly reversed at 5 s (`−0.00139`, interval `[−0.00261,−0.00019]`). This improves discrimination inside the source-model equations by showing that the instantaneous population signal distribution alone is insufficient to recover self-arm progress. It does not rule out differences in recipient-specific signal history or feedback/state coupling, is not animal-level causal evidence, and does not demonstrate AI-system benefit. This retrospective simulation result is a bounded M2 finding, not biological clearance.
