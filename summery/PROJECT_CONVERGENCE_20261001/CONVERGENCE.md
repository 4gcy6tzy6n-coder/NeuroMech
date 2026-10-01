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

---

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

## 2026-10-01 shared M2/M5 context-memory benchmark

[`CROSS_MECHANISM_CONTEXT_MEMORY_V1`](../CROSS_MECHANISM_CONTEXT_MEMORY_V1/RESULTS.md) applied a common seed-block, bootstrap, split, and resource-reporting workflow to separate M2 sensory-state estimation and M5 delayed-credit tasks. M2's equal-parameter context-gain filter beat its additive control in the aligned mapping (`+0.05871` MSE; 95% interval `[+0.05770,+0.05973]`) and lost when context was independent or reversed. M5 eligibility beat a deliberately misassigned-current-feature control, but tied an equal-state persistent-cue memory arm exactly at all four delays. The M5 result therefore does not show that trace decay is better than ordinary cue retention. The outcomes retain different units and were not pooled; the benchmark does not establish a shared positive principle or general AI benefit. It is exploratory and post-result. The first numeric run emitted warnings and is archived as noncanonical; the corrected run passed the independent verifier and reproduced the seed CSVs and summary byte-for-byte in a fresh directory.

---

## 2026-10-01 CROSS_MECHANISM_CONTEXT_MEMORY_V2 — trained estimators and overlapping delayed credit

V2 extended the exploratory M2/M5 benchmark with two trained 8-unit GRUs and a continuous overlapping-input teaching stream. In M2, the context-aware GRU (297 parameters) had lower MSE than the 3-parameter context-gain filter across aligned, independent, and reversed mappings; the observation-only GRU (273 parameters) approximately tied the filter only in the aligned condition and outperformed it under mapping shifts. This comparison is not capacity matched and weakens the claim that the small context-gain operation has a unique advantage over a stronger trained estimator.

In M5, the 16-dimensional eligibility trace improved classification accuracy over an equal-state latest-input cache at delays 1–16, but its delay-64 contrast was unresolved. Exact FIFO memory outperformed the trace at all delays while retaining `16 × delay` state dimensions. The result supports only a bounded synthetic credit-assignment advantage over a weak cache, with an explicit memory/accuracy trade-off. M2 MSE and M5 accuracy remain separate and are not pooled.

## Follow-up updates: matched M2 comparison and M5 memory frontier

The subsequent `M2_ACTION_CONDITIONED_RKN_2D_PURSUIT_V1` comparison completed the previously recommended AcRKN check. Mode-gain beat the adapted 32-parameter AcRKN cell in the aligned primary contrast, but a parameter-matched 8-parameter bilinear RNN beat mode-gain in both aligned and reversed sensor mappings; the task-aware Kalman reference remained strongest. This is a counterexample to a distinctive M2 advantage on that task. The AcRKN was a task adaptation rather than a full reproduction of the published robotics model, and the experiment does not establish a biological feedback-site effect.

`M5_ELIGIBILITY_MEMORY_FRONTIER_V1` compared the 64-value eligibility trace against exact FIFO buffers from one to 64 feature vectors and unbounded exact replay, using task seeds 100–129. The trace exceeded the one-vector FIFO by `+0.14779` accuracy (hierarchical 95% interval `[+0.13757,+0.15796]`, 90/90 generator-seed blocks positive), but that constrained FIFO retained only 1/3,000 delayed cues for updates at delays 4–64. Exact replay with capacity proportional to delay was substantially more accurate; direct one-vector retention also won at delay 1. This refines the prior M5 boundary to a task-specific accuracy–state tradeoff, not general superiority of traces. State values are algorithmic counts rather than measured RAM or energy.

These follow-ups leave the project-level status unchanged: no shared positive artificial principle is established. The M2 and M5 metrics are distinct, and neither artificial comparison constitutes biological validation. Candidate mechanisms must remain tied to independently supported biological computations, while artificial claims remain conditional on their tested task and comparator set. Full contracts and outputs are linked from the [root README](../../README.md).

## 2026-10-01 M2 feedback temporal-alignment result — newest transfer boundary

`M2_FEEDBACK_TEMPORAL_ALIGNMENT_V1` directly varied whether self motor-state feedback reached the sensory-state update at the current step or after one/four steps. In the frozen SLOW_TRANSIENT primary contrast, LAG4 minus current-feedback movement MSE was `−0.003858` (95% seed-block interval `[−0.004294,−0.003409]`, 32 paired blocks), opposite the predicted direction. The 4-step lag arm was slightly better than the current arm, while GRU-8, the generic recurrent control, and output-site feedback all achieved lower primary-condition mean error. Exact instantaneous population-distribution matching passed for all 128 yoke checks; independent verification passed and the run artifacts are committed. The result is exploratory, uses the existing binary tracking task family, and does not map arbitrary simulation steps onto biological conduction delay.

This weakens the idea that contemporaneous feedback alignment explains the M2 artificial effect. Do not continue lag sweeps or count another variant of this simulator as independent task generalization. The cross-mechanism AI-benefit claim remains unsupported. The next mainline work should leave this task family and either (a) build the AI-side test directly from an independently specified computation supported by the biological source, with a distinct task and strong resource-accounted controls, or (b) advance the O3 prospective AIY state-pattern rescue through real laboratory feasibility and collaboration. The latter requires physical rig access and cannot be replaced by additional synthetic simulation. See the [root README](../../README.md) and [`M2_FEEDBACK_TEMPORAL_ALIGNMENT_V1`](../M2_FEEDBACK_TEMPORAL_ALIGNMENT_V1/RESULTS.md).

## 2026-10-01 M2 GRU motor-feedback ablation — incremental signal attribution

`M2_GRU_MOTOR_FEEDBACK_ABLATION_V1` followed the strong GRU-8 performance by testing the motor input inside the same 297-parameter GRU. In SLOW_TRANSIENT, self motor input improved MSE over an otherwise identical zero-input-channel arm by `0.006239` (95% seed-block interval `[0.005197,0.007273]`) and over a recipient-yoked arm by `0.006822` (`[0.005886,0.007770]`), across 32 fresh training-seed blocks. Parameter counts, initialization, update count, and exogenous streams were matched; 128 yoke distribution checks passed. Independent score verification and a complete byte-identical rerun of scientific outputs passed.

This supplies evidence that the explicit motor-state channel contributes to this trained controller under the slow-transient task condition; it does not imply the GRU's representation matches AIY or establish biological transfer. Effects were small or reversed under clean/fast conditions, and the task family is reused, so the result is an attribution analysis rather than independent generalization. The M2 line now has a more precise artificial statement—self-contingent motor input can add task-conditional value to a strong recurrent model, while the low-dimensional placement rule has not shown a robust advantage over strong controls. The next M2 computation test must change task family and retain this input-ablation/yoke logic. Do not claim project-level NMI readiness from this result alone; see the [results](../M2_GRU_MOTOR_FEEDBACK_ABLATION_V1/RESULTS.md) and [root README](../../README.md).

## M5 delayed-reward bandit memory frontier

`M5_DELAYED_REWARD_MEMORY_FRONTIER_V1` repeated the explicit state frontier on the distinct contextual-bandit objective using task seeds 30–59. Trace minus equal-state FIFO-32 averaged over four delays was `−0.002484` expected reward (paired seed-bootstrap 95% interval `[−0.003243,−0.001717]`; 1/30 seed averages positive). Trace beat the current-score assignment control by `+0.009480` (`[+0.007905,+0.011087]`, 30/30 positive), while exact FIFO with capacity at least equal to delay matched exact replay and achieved higher reward. The one-vector FIFO applied only 1 of 6,000 delayed rewards at delays 4–64; its lower accuracy is therefore not a strong algorithmic comparator. This cross-objective follow-up strengthens evidence for a small trace-over-current-assignment effect but also gives a clear counterexample to trace superiority over exact credit assignment. The trace uses fixed 32-value state while exact memory grows to `32×D`; this is a task-specific resource tradeoff, not general AI evidence. Outcomes are not pooled with the class-label objective.

The canonical seed-level CSVs reproduced byte-for-byte in a fresh full runner execution. The verifier initially had an incorrect expectation for current-score updates during the zero-score flush; its expected count was corrected to `6,000−D` without changing runner, contract, outcomes, or estimand. The correction and both verifier hashes are preserved in the [post-run audit](../../data/results/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/canonical/POSTRUN_VERIFICATION.json).

The first execution exposed a parameter-accounting error (the observation-only GRU readout was omitted) and implicit latest-input state accounting. These were corrected and the first outputs retained as noncanonical. An independent corrected run reproduced the canonical seed-level CSVs and summary byte-for-byte; the structural/arithmetic verifier passed. Since the correction and V2 design followed inspection of earlier outcomes, this remains post-result exploratory. No biological validation, general AI benefit, or shared positive computational principle is established.

The detailed record, plot contract, model, data, and audit artifacts are linked from the [repository README](../../README.md) under the latest cross-mechanism experiment section.

## 2026-10-01 M2 bursty-observation feedback placement V1

The new `M2_BURSTY_OBSERVATION_FEEDBACK_V1` study held expected missingness at 50% while varying mean Markov dropout-run length (2, 4, 8 steps), and compared sensory-site feedback with output-site placement, no feedback, an equal-parameter generic scalar RNN, and an 8-unit GRU. At the frozen 8-step condition, `MSE(OUTPUT_SITE) − MSE(SENSORY_SITE)` was `+0.05932` (paired crossed 95% interval `[+0.05201,+0.06673]`; 24/24 training seeds positive). The generic-RNN contrast was `+0.06625` (`[+0.06000,+0.07283]`), while the GRU contrast was `+0.00756` (`[−0.00258,+0.01818]`) and unresolved. The frozen joint criterion is therefore not met: this supports a placement effect over tested small controls in this synthetic task, but does not establish superiority over stronger recurrence. Sensory-site feedback also had lower action energy but slower post-gap recovery than output persistence. The rerun reproduced episode outcomes byte-for-byte, and independent structural/statistical verification passed. This was outcome-informed, artificial-only work and does not establish biological causality or general AI benefit. See [`results`](../M2_BURSTY_OBSERVATION_FEEDBACK_V1/RESULTS.md), [`failure lessons`](../M2_BURSTY_OBSERVATION_FEEDBACK_V1/FAILURE_LOG.md), and [canonical outputs](../../data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical/).

---

## 2026-10-01 M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1 — recipient-specific motor-feedback yoke

This post-result exploratory artificial study extends the sparse-sensation closed-loop tracking family with a cross-agent yoke. At the primary condition (target-switch hazard `1/120`, 50% missingness), self-feedback beat the yoke by `+0.04143` MSE (crossed seed/episode 95% interval `[+0.03901,+0.04383]`; 32/32 seed means positive). The yoke preserves the cohort distribution of motor signals at each timestep while breaking recipient assignment. The three-parameter sensory-site controller also beat the three-parameter one-state generic RNN in this condition; a task-aware oracle remained better. Direct comparisons against output persistence and no feedback were small and reversed under some slow-switch/high-missingness conditions.

Interpretation is limited to a recipient-specific contingency effect in this simulator: donor reassignment also breaks alignment with each recipient's target and observation trajectory, so it does not isolate one biological pathway. The task family overlaps prior sparse-tracking studies, and the experiment is post-result exploratory; it is not biological validation or general AI evidence. The initial verifier miscounted the yoke as a separately fitted model; this was corrected without changing the runner or outcomes. Figure annotations initially collided with the zero line; they were repositioned and the final strict collision audit passed. Corrected outputs passed independent verification and a fresh rerun reproduced canonical outcome files. See [experiment results](../M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1/RESULTS.md), [failure log](../M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1/FAILURE_LOG.md), [model](../../model/M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1/), and [canonical data](../../data/results/M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1/).

---

## 2026-10-01 M2 transfer update — LTC reversal control and hidden-state estimation

Two new M2 artificial experiments now provide direct negative evidence for the tested sensory-site transfer. [`M2_LTC_THERMOTAXIS_REVERSAL_V1`](../M2_LTC_THERMOTAXIS_REVERSAL_V1/RESULTS.md) completed its 32-seed closed-loop thermal task, but learned policies scarcely tracked the setpoint; the sensory-site arm did not separate from feedback-placement or yoke controls. The privileged gradient-sign oracle performed much better, identifying a task-learning failure that made the learned-model ranking uninterpretable as a mechanism advantage.

The follow-up [`M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1`](../M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1/RESULTS.md) replaced end-to-end control with supervised inference of hidden signed displacement from intermittent sensory signals and self-motion. The task was learnable by a generic GRU-4 (`0.6354` MSE in aligned coupling), but the sensory-site LTC reached `1.9748`, lost to output-site feedback (`1.8196`) and both generic recurrent references, and only showed tiny reductions relative to no-feedback/yoked controls. Its prespecified sensory-site criterion was not met. This distinguishes a failed mechanism-shaped implementation from an intrinsically unlearnable task and makes output-site routing a strong competing computation in this generator.

The biological RIM–AIY source evidence remains valid at its published scope. These artificial results do not contradict that biology; they show that the current LTC abstraction and task objective do not transfer its proposed sensory-site operation into a useful artificial state estimator. Together with prior M2 context-dose, pursuit, AcRKN, and bursty-observation comparisons, the AI-side evidence remains task- and comparator-sensitive rather than a robust positive mechanism result. Retain both new studies as boundary evidence; do not tune either in place or count either as independent confirmation.

### Project implication

M2 should remain in the synthesis as a biologically supported computation with unsuccessful or conditional artificial transfers, not carry the paper's positive AI claim on its own. The next mainline effort should return to M5 eligibility/delayed credit and test a genuinely resource-matched, strong recurrent/replay benchmark on new seeds; retain exact FIFO/replay as serious controls. A shared project claim is still absent, and the cross-mechanism benchmark remains unfinished. See the [root README](../../README.md) for the current experiment order and linked artifacts.

---

## 2026-10-01 M5 eligibility versus truncated recurrent gradients

[`M5_ELIGIBILITY_TRUNCATED_BPTT_V1`](../M5_ELIGIBILITY_TRUNCATED_BPTT_V1/RESULTS.md) compared local eligibility, no-trace local learning, TBPTT-1, TBPTT-4, and full BPTT on delayed XOR with the same 24-unit, 746-parameter RNN across 32 task-seed blocks. Eligibility averaged `0.6974` held-out accuracy: it beat no-trace by `+0.14125` (paired seed-bootstrap 95% interval `[+0.07188,+0.21288]`) but lost to TBPTT-4 by `−0.265875` (`[−0.32950,−0.20031]`; 1/32 seed blocks favored eligibility). Full BPTT reached `0.999625` with a 95% interval `[0.99925,0.999875]`, confirming task viability. This is a meaningful negative result against short recurrent-gradient controls, not task failure. It narrows M5 support to improvement over weak/current-step local updates; it does not show competitiveness with truncated/full gradients or exact memory. The local implementation ran somewhat faster, but the accuracy loss was large and wall-clock timing is implementation-specific, not a compute-equivalence claim. This remains post-result exploratory artificial evidence, not biological validation or a shared AI principle. See the [contract and lessons](../M5_ELIGIBILITY_TRUNCATED_BPTT_V1/), [canonical outcomes](../../data/results/M5_ELIGIBILITY_TRUNCATED_BPTT_V1/), and [root README](../../README.md).

---

## 2026-10-01 M2 constant-temperature source-trace decoding

[`M2_AIY_STATE_CONDITIONAL_ENCODING_V1`](../M2_AIY_STATE_CONDITIONAL_ENCODING_V1/RESULTS.md) analyzed the published Figure 2/5 constant-temperature traces at the animal level (five WT, five RIM-ablated). AIY-only forward/reversal decoding averaged AUC `0.758` in WT and `0.502` after ablation. Including the immediately prior motor state as a strong persistence baseline reduced AIY's incremental AUC to `0.01554` in WT and approximately zero after ablation; AVA showed a similar group shift. This is consistent with the published RIM-dependent representation but does not establish AIY-specific residual coding or new causality. The output clarifies an AI-transfer confound: compare neural feedback with prior-state/action persistence and report what the neural signal adds beyond that baseline. This is a retrospective source-data reanalysis and does not change the mixed/negative AI-transfer evidence. The [root README](../../README.md) links the contract, per-animal outputs, model, and independent verification.

## 2026-10-01 M2 AIY next-state prediction follow-up

`M2_AIY_PREMOTOR_STATE_PREDICTION_V1` used strict complete-label forecast windows but yielded no positive 2-second examples in the five RIM-ablated animals; that primary group comparison is not estimable and remains a documented target-definition failure. In the separately versioned post-result V2, transition/unknown labels were treated as interval-censored and the next known state within 2 seconds was predicted from recent behavior, with current AIY or AVA added as a neural feature. AIY's incremental AUC averaged `0.2098` in WT and `0.0779` after RIM ablation (WT-minus-RIM `0.1318`); AVA's contrast was larger at `0.2229`. Each animal had only 6–18 positive primary samples, so this is a candidate prospective signal in the existing source cohort, not evidence for AIY specificity, causation, or RIM-mediated pathway uniqueness. The independent verifier recomputed all 60 per-animal score rows and checked both workbook hashes. This result refines the AI-transfer question toward whether recent motor/premotor timing adds useful information beyond explicit motor-history memory; it does not validate a neural-derived AI component. See [V2 results](../M2_AIY_PREMOTOR_STATE_PREDICTION_V2/RESULTS.md) and the [root README](../../README.md).

---

## 2026-10-01 M2 synthetic predictive-cue transfer V1–V2

A noisy synthetic future-state cue improved both the six-parameter forecast-fusion filter and the generic recurrent control relative to their no-cue ablations. With an aligned cue, the matched generic recurrent model scored AUC `0.8643` versus `0.7941` for the structured filter (structured-minus-generic `−0.0702`, seed-bootstrap 95% interval `[−0.0724,−0.0681]`). Under uninformative/reversed mappings, the structured filter was less brittle, yet both cue-using models performed worse than their no-cue ablations. This establishes neither a structure-specific advantage nor biological-to-AI transfer: the cue directly reports noisy future-target information, and the test is outcome-informed. The result strengthens the project's negative/conditional M2 boundary; no shared positive artificial principle is established.

---

## 2026-10-01 M5 trace-horizon sweep

`M5_DELAYED_REWARD_TRACE_HORIZON_V1` tested four fixed decay factors on 30 fresh seed blocks across reward delays 1, 4, 16, and 64. The trace-versus-current-score contrast depended on delay; longer decay was more useful in some long-delay cells. Exact replay nevertheless remained markedly better in every cell (mean held-out expected reward `0.55485`, compared with `0.50660–0.51157` for traces). This narrows M5's result to a delay-sensitive compact-state trade-off in one stationary bandit, rather than superiority in delayed credit assignment. It does not establish a biological-to-AI transfer effect or a shared M2/M5 principle. Full analysis and artifacts are linked in the [root README](../../README.md).


---

## 2026-10-01 M5 real-trial interval decoding V1

[`M5_REAL_TRIAL_INTERVAL_DECODING_V1`](../M5_REAL_TRIAL_INTERVAL_DECODING_V1/RESULTS.md) used acquired Dryad v4 GrC/CF traces to test within-session prediction of measured reward delay from a fixed pre-reward GrC window. The source-style CF-timed LTD projection had mean session-level MAE `0.00970 s` worse than the training-fold mean and improved it in only `1/16` sessions. The generic raw-GrC PCA16/ridge decoder improved the mean baseline by only `0.00265 s` across sessions (11/16 sessions), with no mean advantage in the transition group. In all source groups, generic raw PCA outperformed CF-LTD by `0.0117–0.0131 s`. Four folds in one 1-s expert session had no training-fold CF candidate; the amended zero-projection handling retained these folds. The amendment followed partial execution, so the result is exploratory, not confirmatory. Verification passed, and an independent full rerun reproduced trial predictions and fit records byte-for-byte.

This is an adjacent reward-interval dataset and task, not the delay-eyeblink conditioning intervention that defines the core biological M5 evidence. It narrows the tested source-projection/readout claim: these public traces do not show useful held-out interval information from the modeled CF-LTD projection beyond a session timer. The small, cohort-dependent raw-GrC signal is not evidence of causal plasticity, animal-level generalization, or AI transfer. The outcome strengthens the case against another loosely specified generic trace benchmark; any next artificial study should specify the biological adaptation computation and compare it against exact memory and strong recurrent baselines. See the [root README](../../README.md), [canonical outcomes](../../data/results/M5_REAL_TRIAL_INTERVAL_DECODING_V1/canonical/), and [preflight/failure record](../M5_REAL_TRIAL_INTERVAL_DECODING_V1/).

---

## 2026-10-01 M2 artificial feedback-placement transient-filter test

[`M2_SENSORIMOTOR_TRANSIENT_FILTER_V1`](../M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/RESULTS.md) tested whether actual motor-state feedback placed inside a scalar sensory-state update rejects brief contradictory sensor pulses better than putting the same-size term at the output. The frozen primary contrast was negative: output minus sensory-site pulse-window MAE was `−0.0921` (95% seed-block bootstrap interval `[−0.1081, −0.0766]`, 20 paired blocks), so output-site placement performed better in this synthetic task. No-feedback was worse than both placements, which is compatible with feedback helping in the simulator but does not establish biological transfer. This post-result exploratory translation neither refutes the RIM-dependent AIY result nor demonstrates an AI advantage. Episode metrics, seed summaries, and summary JSON reproduced byte-for-byte in an independent full rerun. See the [frozen contract and analysis](../M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/), [canonical outputs and rerun comparison](../../data/results/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/canonical/), and [root README](../../README.md).

### Post-run secondary trade-off profile

A separate paired audit found lower mean absolute movement error for output-site placement across all five conditions, alongside higher command energy and longer switch latency in all five. Squared-error ranking favored sensory-site placement in the sustained-switch and combined-stress conditions. This multi-metric pattern was not the frozen primary question and has no multiplicity correction; it is a follow-up hypothesis, not a finding of biological energy/accuracy Pareto structure. A fresh-seed, validation-selected energy-budget comparison has now been completed; it tested one preselected budget rather than estimating a Pareto frontier. See the [post-run audit](../M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/POSTRUN_TRADEOFF_AUDIT.md), [paired contrast table](../../data/results/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/POSTRUN_TRADEOFF_CONTRASTS.csv), [analysis script](../../model/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/analyze_tradeoffs.py), and [energy-budget follow-up](../M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/RESULTS.md).

---

## 2026-10-01 M2 feedback-placement energy-budget follow-up

[`M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1`](../M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/RESULTS.md) used separate validation episodes to select energy penalties for each model under mean command energy `≤0.50`, then compared sensory-site and output-site controllers on fresh held-out episodes. All 16 paired seed blocks supplied validation-feasible primary policies. Both arms met the held-out transient-pulse budget criterion: sensory-site energy `0.4401` (95% interval `[0.4100,0.4656]`) and output-site energy `0.4558` (`[0.4300,0.4825]`). The primary sensory-minus-output movement-MAE contrast was `+0.01428` (95% seed-block interval `[−0.00106,+0.02960]`, 16 blocks), a point estimate favoring output-site with uncertainty crossing zero. Thus neither a site advantage nor equivalence is established.

This is a post-result exploratory synthetic test because the budget was motivated by prior outcomes. A first execution duplicated all evaluation blocks and was invalidated by the frozen structural verifier; the corrected execution kept the same design and passed verification. An independent full rerun reproduced validation, selection, test, seed summaries, and summary JSON byte-for-byte. This result establishes neither biological energy efficiency nor transfer to real AI systems; it narrows only this controller/task/budget comparison. See the [incident and failure record](../M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/EXECUTION_INCIDENT_01.md), [canonical outputs and rerun record](../../data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/canonical/), and [root README](../../README.md).


### 2026-10-01 M2 recipient-contingency yoke test

`M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1` found a positive self-contingent-versus-cross-agent-yoked movement-MSE contrast in the frozen `SLOW_TRANSIENT` synthetic condition (`+0.009431`, 95% seed-block interval `[+0.007434,+0.011676]`, 32 blocks), with exact instantaneous population-distribution checks passing. The effect did not hold in fast-transient or clean conditions. On the primary condition, output-site feedback, a generic recurrent controller, and GRU-8 all had lower MSE than the self-sensory controller. This adds evidence for a narrow recipient-contingency effect in one artificial regime, while leaving the project-level AI-benefit proposition unsupported. The corrected full rerun reproduced all scientific outputs; see [`M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1` results](../M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1/RESULTS.md) and the [canonical rerun record](../../data/results/M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1/canonical/REPRODUCIBILITY.json).
