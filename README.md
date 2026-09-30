# NeuroMech

**NeuroMech studies how experimentally supported computations in real nervous systems can inform artificial systems.** The project focuses on computational operations—what information is used, how internal state is updated, and under what conditions—not on copying a connectome or treating biological and artificial units as identical.

Biological findings, computational abstractions, and artificial-system results are tracked separately. A model result does not count as new biological validation.

The current evidence and novelty assessment is recorded in the [NMI claim and novelty audit](summery/NMI_CLAIM_AND_NOVELTY_AUDIT_20261001.md). It identifies the next useful work as mechanism-aligned computation and stronger comparisons, rather than another broad candidate or dataset search.

## Current research focus

The project is converging on **two mechanism-grounded studies plus one shared artificial benchmark**, rather than expanding its candidate list. The intended paper-level question is whether distinct, experimentally supported neural computations yield specific and reproducible benefits in artificial systems when compared with controls matched for capacity and task conditions. This is a research direction, not an established result.

| Line | Biological question | Current artificial evidence |
|---|---|---|
| **M1 — higher-order visual-motion correction** | What does a source-defined third-order correction contribute to fly motion estimation? | The existing RR19 natural-scene run is partial and exploratory. H1/H3 were in the predicted direction, while the phase-mismatched specificity contrast H2 was in the opposite direction. H4 and an overall four-hypothesis verdict are not established. See [partial results](experiments/m1_higher_order/RR19_STEP4_PARTIAL_RESULTS.md). |
| **M2 — motor-state feedback and sensory context** | Does the relation between motor-state timing and sensory/environmental context contribute to thermotaxis in the RIM–AIY model? | Continuous-estimation and sequential-decision studies found alignment-dependent artificial benefits. The new closed-loop sparse-sensation study found lower tracking error for sensory-site feedback than a 3-parameter one-state RNN and direct placement/ablation controls at its training condition, but the task-aware oracle remained better and slow/high-missing conditions reversed the direct-control comparison. Source-model self-contingency also weakens or reverses under rapid gradient changes. These are bounded simulation results, not animal-level validation. See [sparse-sensation tracking](summery/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/), [source-model contingency test](summery/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/), and [M2 transfer results](summery/M2_LOW_DATA_GATING_V3/). |
| **M3 — Fish1.5 structure–function constrained integration** | Can same-specimen functional and EM evidence identify the frozen visual-motion integration computation? | Same-specimen functional-ID↔EM-ID crosswalks are documented for explicit rows, but the inspected release lacks switch-event/timebase, graded evidence, and choice/behavior fields required by the frozen mechanism. Functional class-label provenance and the pinned synapse materialization are also unresolved. Acquisition is **PARTIAL**; E3 and AI modeling remain closed. See the [mechanism evidence registry](summery/MECHANISM_EVIDENCE_REGISTRY.md). |
| **Cross-mechanism benchmark** | Do mechanism-specific computations outperform capacity-matched generic controls under the task conditions that make those computations relevant? | V2 extends M2 to trained GRUs and M5 to overlapping delayed-credit streams. The context-aware GRU beats the small context-gain filter across mappings; eligibility beats latest-input memory through delay 16 but is unresolved at delay 64, while exact FIFO is better throughout. Outcomes remain separate and exploratory; no shared positive effect is established. See the [V2 result and failure record](summery/CROSS_MECHANISM_CONTEXT_MEMORY_V2/) and [project convergence record](summery/PROJECT_CONVERGENCE_20261001/CONVERGENCE.md). |

## Convergent experiment plan

The project is organized around one testable proposition: **a biologically grounded computation may provide an artificial inductive bias when its defining signal is informative for the task, and any benefit must survive mechanism-targeted and capacity-matched comparisons.** This is a hypothesis for testing, not a result established by the experiments below.

| Study | Next experiment must establish | Current evidence and limitation | Admission to the shared claim |
|---|---|---|---|
| **M1 — higher-order visual-motion correction** | On a separately specified evaluation sample, compare the source-defined correction with a capacity-matched generic correction and a phase-mismatch control. | The existing natural-scene run is partial: H1/H3 were in the predicted direction, H2 reversed, and H4 is not established. The current result is not a successful specificity demonstration. | Count only if the fresh, frozen comparison supports the source-specific computation; preserve the existing mixed result as historical evidence. |
| **M2 — feedback-site and state-timing specificity** | Compare sensory-state feedback with output persistence, a generic adaptive controller, and a no-feedback control under informative, absent, and reversed signal-task relations; match training data and model resources. | Source-model simulations show a self-contingency effect under some gradient-reversal schedules, but the effect narrows or reverses at faster schedules. Existing abstract-task transfers are mixed and do not establish biological-to-AI transfer. | Count only within tested task conditions and if the result survives the frozen matched controls; do not generalize from a source-model result alone. |
| **Shared benchmark harness** | Apply the same preregistered seed, data-split, compute/parameter accounting, uncertainty, and control rules to both studies. Keep each study's primary outcome native to its task. | Not yet a completed experiment. M1 and M2 outcomes have different units and estimands. | A project-level claim is conjunctive: each mechanism must meet its own frozen criterion. Never pool raw task scores into a single effect. |

Fish1.5 is retained as supporting structure–function evidence, not a fourth artificial mechanism study: its inspected public release does not currently expose all fields required by the frozen computation. See the [convergence record](summery/PROJECT_CONVERGENCE_20261001/CONVERGENCE.md) for detailed blockers and historical decisions. Experiment-specific protocols, raw outcomes, and failure records remain in their linked `summery/`, `data/`, and `model/` folders.

### Latest cross-mechanism experiment: context and delayed credit V2

V2 extended the earlier exploratory benchmark with trained recurrent estimators for M2 and an overlapping-input delayed-teaching task for M5. In M2, an 8-unit context-aware GRU (297 parameters) had lower latent-state MSE than the 3-parameter context-gain filter in aligned, independent, and reversed mappings; the aligned mean contrast `GRU − filter` was `−0.02473` (95% seed-bootstrap interval `[−0.02640, −0.02293]`). The observation-only GRU (273 parameters) was approximately tied with the filter when aligned (`−0.00008`, interval `[−0.00279, +0.00265]`) and better in the other mappings. This does not support a unique context-gain advantage against the stronger learned estimators, and parameter counts are not matched.

In M5, the 16-dimensional eligibility trace exceeded an equal-state latest-input memory at delays 1, 4, and 16 (`+0.42798`, `+0.39426`, and `+0.29788` accuracy; each 95% interval excluded zero), but the contrast was unresolved at delay 64 (`+0.02817`, interval `[−0.00205, +0.05936]`). An exact FIFO reference outperformed eligibility at every delay; FIFO memory grows with delay and is not state matched. Thus the trace offers bounded artificial credit-assignment benefit over a weak latest-input control at short/medium delays, not a general advantage over explicit memory. M2 MSE and M5 accuracy remain separate; the study is post-result exploratory and establishes neither biological validation nor general AI benefit. The first run's parameter/state-accounting issue was retained as noncanonical; corrected outputs are the canonical record.

- [Contract, results, and implementation-correction record](summery/CROSS_MECHANISM_CONTEXT_MEMORY_V2/)
- [Runner and verifier](model/CROSS_MECHANISM_CONTEXT_MEMORY_V2/)
- [Corrected canonical outcomes](data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/canonical_corrected/)

### Previous cross-mechanism experiment: context and delayed credit V1

The shared-workflow benchmark compared M2 context-conditioned sensory gain with a three-parameter additive recurrent filter and M5 eligibility-trace learning with delayed labels. M2's aligned-context MSE advantage was `+0.05871` (95% task-seed interval `[+0.05770,+0.05973]`), but the contrast reversed when context was independent (`−0.13000`) or anti-aligned (`−0.31992`). M5 eligibility beat an unrelated-feature misassignment control, yet matched an equal-state persistent-cue buffer exactly at all four delays. The result therefore shows an M2 task-alignment boundary and no distinct trace advantage over direct cue retention; it does not establish a shared positive principle, biological validation, or general AI benefit. Both modules are post-result exploratory and retain separate outcome units. The corrected run was independently repeated with byte-identical seed-level CSVs and summary.

- [Contract, results, and failure record](summery/CROSS_MECHANISM_CONTEXT_MEMORY_V1/)
- [Runner and verifier](model/CROSS_MECHANISM_CONTEXT_MEMORY_V1/)
- [Canonical outcomes and reproducibility record](data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V1/)

### M2 artificial transfer result: sparse-sensation tracking

In a closed-loop target-tracking simulation, the three-parameter sensory-state feedback policy achieved mean squared tracking error `0.2581` at the training condition (target-switch hazard `1/120`, 50% missing sensory samples), compared with `0.3020` for a three-parameter one-state generic RNN. The paired difference `MSE(generic) − MSE(sensory feedback)` was `+0.04386` (crossed 95% bootstrap interval `[+0.04247,+0.04526]`; 32/32 training-seed clusters positive). It also exceeded equal-parameter output-site persistence and no-feedback controls by `+0.00403` and `+0.00416`. The task-aware oracle remained better (`0.2283`). The advantage reversed under slower target switching with 75% missing observations, where output persistence and no feedback had lower error. An independent run reproduced all 368,640 episode rows byte-for-byte. This is an artificial task-specific result; missing observations were exact-zero encoded, the generic model had only one hidden state, and no biological-to-AI or general-AI claim follows. See the [protocol, results and limitations](summery/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/), [model and verifier](model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/), and [raw outcomes and figure bundle](data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/).

### M2 source-model feedback-site control

A retrospective Figure 7 source-model follow-up replayed complete ordered movement-state and latent motor-state sequences from independent development trajectories, using the source model's two-step heading-transition timing. Sensory-site feedback exceeded this full-trajectory yoke by `+0.4516` warm-direction index (95% paired seed-block interval `[+0.4443, +0.4589]`; 200/200 held-out blocks positive). The reported marginal persistence summaries were close, but no equivalence margins were frozen. This indicates that replaying an independent motor trajectory was insufficient in this source-model implementation; it does not establish a unique biological synapse, biological validation, or AI transfer. See the [contract, results, and failure record](summery/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/), [runner](model/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/), and [archived outputs](data/results/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/).

### M2 context-information operating boundary

A new 30-seed artificial dose-response study trained the state-conditioned gain filter under full context/sensor alignment, then tested 11 progressively weakened or reversed mappings using paired latent paths and noise. The mode-gain update was worse than the context-free filter through `κ=+0.20`, unresolved at `+0.30`, and better at `+0.40` and `+0.50`; the estimated crossover was `κ=0.285` (crossed-bootstrap 95% interval `[0.251, 0.318]`). At full alignment, it also beat the learned generic recurrent controls, while a task-aware Kalman reference remained better. This quantifies a sharp task-specific operating boundary; it does not establish the same numerical relation in the worm or broad AI benefit. See the [contract, results, and failure log](summery/M2_CONTEXT_INFORMATION_DOSE_V1/), [runner and verifier](model/M2_CONTEXT_INFORMATION_DOSE_V1/), and [raw outputs](data/results/M2_CONTEXT_INFORMATION_DOSE_V1/).

### M2 2D closed-loop pursuit V1 boundary

A new sensorimotor task paired the M2-inspired state-gated estimator against 8-parameter additive and bilinear recurrent controls. In the aligned 2D pursuit environment, the mode-gain system reached 84.2% success; the parameter-matched bilinear baseline reached 90.5% and had lower final distance by `0.0209` (crossed-bootstrap 95% interval for bilinear minus mode `[-0.0324,-0.0105]`). The no-context ablation was similar to mode-gain, while reversing the mapping reduced mode-gain success to 30.2%. Although mode-gain had lower supervised training loss, that advantage did not carry into closed-loop control. This adverse result raised a training/deployment distribution mismatch as one candidate explanation; it did not isolate the cause. The mapping is artificial and does not test biological equivalence. See the [contract, results, and failure log](summery/M2_2D_CLOSED_LOOP_PURSUIT_V1/), [runner and verifier](model/M2_2D_CLOSED_LOOP_PURSUIT_V1/), and [episode outcomes](data/results/M2_2D_CLOSED_LOOP_PURSUIT_V1/).

### M2 2D closed-loop pursuit V2: training-distribution diagnostic

A post-result paired diagnostic trained all learned models on either random-action trajectories or shared trajectories generated by a task-aware Kalman teacher with 25% random exploration. The aligned bilinear-minus-mode final-distance contrast shifted from `−0.01885` (95% crossed interval `[−0.02791,−0.01059]`) under random-action training to `+0.00394` (`[+0.00051,+0.00750]`) under teacher-mixed training; the regime interaction was `+0.02279` (`[+0.01341,+0.03318]`). This supports training distribution as a material contributor to the V1 ranking in this task, not as its unique cause. MODE_GAIN still did not beat every control: the additive model had the best aligned final distance, and the no-context ablation remained comparable. The reversed mapping remained harmful. The study is exploratory and makes no biological-transfer or general-AI claim. See the [contract, results, and limitations](summery/M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/), [runner and verifier](model/M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/), and [canonical outputs](data/results/M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/).

### M2 corollary-discharge placement: sensory state vs output persistence

A mechanism-aligned synthetic test compared the same previous-action signal entering either the sensory-state update or the output decision, with a parameter-matched no-feedback model, generic two-unit RNN and Bayes reference. At the trained state-switch hazard (`0.05`), sensory-site feedback exceeded output persistence by `+6.80` percentage points in accuracy (crossed 95% interval `[+6.48,+7.12]`). However, it did not beat no feedback (88.94% vs 89.05%), the generic RNN (90.21%) or Bayes (90.30%). The sensory-site model recovered from state changes faster than output persistence, suggesting a feedback-placement effect on stability versus switching rather than a general performance gain. The task is synthetic and does not validate the worm mechanism. See the [contract, results and failure log](summery/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/), [runner and verifier](model/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/), and [canonical outputs](data/results/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/).

### M2 source-model stress test: changing thermal-gradient direction

The corrected Ji et al. Figure 7 model was evaluated with a spatial warm-gradient direction that either stayed fixed or reversed every 40, 20, 10 or 5 seconds. At the 20-second schedule, the source model's sensory-site feedback arm exceeded its no-feedback ablation by `+0.07379` local-progress units per second (95% seed-block interval `[+0.07061,+0.07694]`; 100/100 simulated blocks positive). Progress declined as reversals became more frequent. The nominal output-site comparator saturated at 100% forward-state occupancy and 200-second runs, so its primary contrast cannot isolate feedback placement. This is an exploratory simulation-derived boundary, not animal-level evidence or AI benefit. See the [contract, results and failure log](summery/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/), [runner and verifier](model/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/), and [canonical results](data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/).

### M2 source-model self-contingency test: cross-agent yoked feedback

A follow-up kept the source-model feedback signal's instantaneous distribution across agents exactly fixed while permuting each agent's signal to another agent. At the primary 20-second gradient reversal, self-contingent feedback exceeded the cross-agent yoke by `+0.04618` aligned-progress units per second (95% seed-block bootstrap interval `[+0.04252,+0.04994]`; 100/100 simulation blocks positive). The advantage narrowed as reversals accelerated and slightly reversed at 5 seconds (`−0.00139`, interval `[−0.00261,−0.00019]`). This separates recipient-specific contingency from a generic population-level positive signal within this model, but does not establish biological causality or artificial-system benefit. The yoke replays signals from paired self-feedback trajectories, so the result remains a retrospective source-model probe. See the [contract, results and limitations](summery/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/), [runner and verifier](model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/), and [raw results and figure](data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical/).

### Converged experimental package

The intended core package is **M1 + M2 + one shared artificial benchmark**. M1 tests higher-order correction in visual-motion computation; M2 tests feedback-site and state-timing specificity in the RIM–AIY thermotaxis circuit; the shared benchmark asks whether the extracted computations provide benefits over capacity-matched generic controls on their respective tasks. These are linked by a common claim about transferring evidence-grounded computations, not by pooling unlike biological or task outcomes.

### Fish1.5 structure–function evidence and current boundary

Fish1.5 remains a supporting biological evidence line, not a fourth full artificial-mechanism study. The official release provides same-specimen imaging/EM registration and an explicit functional-ID-to-EM-ID crosswalk for listed neurons. That registration alone does not identify the frozen iMI/cMI/MON→SMI direction-switch/evidence-update computation: the inspected functional release does not expose switch-event timing, a graded evidence sequence, or choice/behavior linkage. Functional class-label provenance is unresolved, and the archived synapse materialization is not version-pinned. The current status is therefore **acquisition PARTIAL, E3 CLOSED, no Fish1.5 AI model**. These are limits of the inspected public substrate, not evidence against the biological mechanism. See the [mechanism evidence registry](summery/MECHANISM_EVIDENCE_REGISTRY.md) for the frozen scope and claim boundaries.

The intended core package remains **M1 + M2 + one shared artificial benchmark**. The M1 and M2 studies use different biological systems and task-specific outcomes; a common benchmark must preserve those separate estimands and compare each mechanism with its own capacity-matched controls. Current exploratory outcomes do not establish the paper-level transfer claim.

The M2 state-gated sensory-update and active-sensing studies are supporting algorithmic probes, not substitutes for the feedback-site-specificity study or direct biological validation. Their benefits are conditional on the task's state/observation mapping, and stronger generic or task-aware references remain competitive. See [M2 transfer evidence](summery/M2_FORWARD_STATE_SENSORY_GATE_V3/RESULTS.md) and [closed-loop active-sensing results](summery/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/RESULTS.md).

## Earlier artificial benchmark: M2 low-data conditional update V1

Twenty paired task seeds compared a four-parameter state-conditioned gain filter with a four-parameter additive scalar RNN at four training-set sizes (16, 64, 256, 1024), using the same 250 optimizer updates and 640,000 sequence-step tokens per fit. In the ALIGNED synthetic mapping, `MSE(GENERIC_RNN_1D) − MSE(MODE_GAIN_FILTER)` averaged `+0.01149` (seed-bootstrap 95% interval `[+0.01083, +0.01219]`; 20/20 seeds positive). The effect was nearly constant across data sizes. In INDEPENDENT and REVERSED mappings, the additive RNN was better at every size; the reversed mapping produced the largest penalty for the structured update.

This tests a narrow artificial inductive-bias claim. The context-to-observation mapping is not a demonstrated biological detail, the generic control cannot express a multiplicative input-by-context interaction, and prior stronger adaptive references remain relevant. It does not establish biological validation or broad AI benefit. The independent verifier checked all 122,880 held-out episode rows and the paired-seed result.

- [Contract, results and failure record](summery/M2_LOW_DATA_GATING_V1/)
- [Runner and independent verifier](model/M2_LOW_DATA_GATING_V1/)
- [Episode-level outcomes and manifest](data/results/M2_LOW_DATA_GATING_V1/)

## Follow-up: M2 low-data benchmark V2 with bilinear control

V2 replaced the additive comparator with a four-parameter bilinear tanh recurrent model that includes an explicit input×context term. On disjoint seeds, the mode-gain filter still had lower MSE in the ALIGNED primary (`bilinear − mode = +0.00509`, 95% seed-bootstrap interval `[+0.00465, +0.00552]`, 20/20 positive). It also scored lower than the bilinear model in INDEPENDENT and REVERSED mappings, while its own absolute MSE rose from about `0.056` aligned to `0.097` reversed. Because the relative advantage persists when the context mapping is wrong, this result does not isolate an alignment-specific biological computation. Comparator equation and nonlinear dynamics remain confounded; stronger filtering and task-aware references remain necessary.

- [Contract, results and failure analysis](summery/M2_LOW_DATA_GATING_V2/)
- [Runner and independent verifier](model/M2_LOW_DATA_GATING_V2/)
- [Episode-level outcomes and manifest](data/results/M2_LOW_DATA_GATING_V2/)

## Follow-up: M2 conditional-update benchmark V3

V3 added a no-context constant-gain filter, a five-parameter free linear bilinear update, and a Kalman oracle using each test sequence's known dynamics. Across four data sizes, the state-conditioned filter beat the constant-gain ablation by `0.00899` MSE in ALIGNED evaluation (95% seed-bootstrap interval `[0.00847, 0.00946]`, 20/20 positive) and beat the bilinear update by `0.00656` (`[0.00614, 0.00695]`). Under mapping shifts, the context-free filter was better: mean MSE `0.0532` vs `0.0675` in INDEPENDENT and `0.0662` vs `0.0981` in REVERSED. The Kalman oracle remained best in all three conditions.

This supports a task-bounded synthetic result: context-dependent gain helps when context marks the informative channel and harms when that relation changes. The mapping was imposed in the artificial task and is not established as the worm's measured computation. It therefore does not close the biological-to-AI transfer claim.

- [Contract, results and failure analysis](summery/M2_LOW_DATA_GATING_V3/)
- [Runner and independent verifier](model/M2_LOW_DATA_GATING_V3/)
- [Episode outcomes and manifest](data/results/M2_LOW_DATA_GATING_V3/)

## New task-family test: M2 sequential binary decision V1

The state-conditioned update was transferred from continuous latent-state estimation to terminal left/right decisions after 32 steps of noisy evidence accumulation. In the ALIGNED synthetic condition, accuracy averaged `0.7029` across four training-set sizes, versus `0.6385` for constant gain; the paired difference was `+0.06448` (95% seed-bootstrap interval `[+0.05703, +0.07232]`, 20/20 positive). The context-free model was better in INDEPENDENT (`0.6413` vs `0.6145`) and REVERSED (`0.6368` vs `0.5192`). The Bayesian oracle achieved `0.760–0.838` across conditions.

This is evidence that the artificial operation generalizes across two task objectives under the imposed aligned context relation, with substantial mismatch cost and a gap to the oracle. The context/evidence relation is synthetic and has not been established as a biological property of the worm circuit. The result does not establish biological-to-AI transfer or broad AI benefit.

- [Contract, results and failure analysis](summery/M2_SEQUENTIAL_DECISION_V1/)
- [Runner and independent verifier](model/M2_SEQUENTIAL_DECISION_V1/)
- [Episode outcomes and manifest](data/results/M2_SEQUENTIAL_DECISION_V1/)

### M2 context-dose transfer to terminal decisions

A 30-seed extension measured the same 11 context-information doses on a terminal left/right decision objective. The mode-gain filter's advantage over constant gain crossed zero near `κ=0.134` (crossed-bootstrap 95% interval `[0.072, 0.200]`): it was below the constant filter at `κ=0`, unresolved at `+0.10`, and better from `+0.20` upward. The crossover differs descriptively from the continuous-estimation result (`κ≈0.285`), showing that the operating boundary changes with the task objective. At full alignment, mode-gain accuracy was `0.7111`, versus `0.6460` for constant gain, while the Bayes reference remained ahead by `13.3` percentage points. This is objective transfer within a closely related synthetic evidence model, not broad task-family or biological transfer. See the [contract, results, and failure log](summery/M2_DECISION_CONTEXT_DOSE_V1/), [runner and verifier](model/M2_DECISION_CONTEXT_DOSE_V1/), and [trial-level data](data/results/M2_DECISION_CONTEXT_DOSE_V1/).

## Active integrated study: O3 AIY state-pattern rescue

The next mainline study is a prospective *C. elegans* thermotaxis experiment asking whether restoring the forward-state timing of AIY activity under RIM perturbation rescues thermosensory gating and forward-run persistence. Its decisive control is the same AIY stimulation waveform delivered at yoked times, matched for total light exposure. Broad motor-state sensory gating and AIY optogenetic control are already established; the candidate contribution is the specific timing-dependent rescue in the RIM–AIY thermotaxis circuit, not the general phenomenon. The focused literature audit and executable design outline are in [O3 route plan](experiments/biological_validation/O3_AIY_STATE_RESCUE_NOVELTY_AND_EXECUTION_PLAN.md).

The current M2 AI-side experiment remains an exploratory synthetic boundary test. Its sensor-reliability mapping is not established by the worm study and will not serve as the central biological transfer claim. An artificial state-gated update benchmark can continue in parallel with experimental preparation, but its result remains conditional until the biological computation is directly tested.

## Previous source-model experiment: M2 full motor-state trajectory replay V1

Complete forward/reverse mode sequences from independent corrected-model development runs were replayed on held-out heading streams, preserving each 200-second mode trace while breaking its relationship to the held-out position and heading. The equal-weighted sensory-site minus replay warm-direction contrast was `+0.44742` (95% seed-block bootstrap interval `[+0.43988, +0.45497]`; 200/200 blocks positive).

Held-out forward-state summaries were close across noise scales; reverse-duration summaries were close at `1.00` and `1.25`, with a residual reverse-tail difference at `0.75`. No equivalence bounds were frozen. The exploratory source-model result suggests independent motor-state timing alone does not recover warm-direction behavior in this task, but it does not isolate a unique biological feedback site, animal-level effect, or AI benefit. MATLAB/Octave execution parity remains unverified.

- [Contract, results, and limitation log](summery/M2_STATE_TRAJECTORY_REPLAY_V1/)
- [Replay runner, corrected source model, and verifier](model/M2_STATE_TRAJECTORY_REPLAY_V1/)
- [Packed development traces, held-out data, and verification](data/results/M2_STATE_TRAJECTORY_REPLAY_V1/)

## Previous experiment: M2 marginal-persistence yoke V1

The corrected Figure 7 sensory-feedback model was compared with a motor-state yoke that resampled forward and reverse bout durations from independent development simulations without access to current position, heading, or temperature. The pooled sensory-site minus yoke warm-direction contrast was `+0.45489` (95% seed-block bootstrap interval `[+0.44770, +0.46211]`; 200/200 blocks positive); the yoke's direction index was near zero.

The yoke did not reproduce persistence adequately at noise scale `0.75` (mean forward-bout difference `+0.609 s`, P90 `+2.623 s`, and long-run fraction `+0.00878`). There were no frozen equivalence bounds, so close duration summaries at noise scales `1.00` and `1.25` are descriptive only. This exploratory result does not establish a matched-control feedback-site effect. The next control should replay complete development motor-state trajectories and pass a held-out persistence-adequacy check before interpreting direction outcomes.

- [Contract, results, and failure log](summery/M2_PERSISTENCE_YOKED_DIRECTION_V1/)
- [Yoke runner, source model, and independent verifier](model/M2_PERSISTENCE_YOKED_DIRECTION_V1/)
- [Development libraries and held-out outputs](data/results/M2_PERSISTENCE_YOKED_DIRECTION_V1/)

## Previous experiment: M2 feedback-site specificity V5

V5 corrected a one-sample offset in the Figure 7 sensory-delay index: the author MATLAB lookup `max(1, ti−delay)` maps to Python `max(0, t−delay)`. The equal-weighted sensory-site minus motor-only warm-direction contrast remained positive at `+0.13936` (95% seed-block bootstrap interval `[+0.13572, +0.14295]`; 200/200 blocks positive).

The motor-only control still failed to match persistence: it had shorter mean and P90 run durations, longer median durations, and fewer long runs at each tested noise scale. This outcome-informed source-model comparison therefore does not isolate feedback-site specificity. The index was checked against MATLAB source code, but MATLAB/Octave execution parity, random-number behavior and smoothing boundaries remain unverified. It is not biological validation or AI-transfer evidence.

- [Contract, results, and failure log](summery/M2_FEEDBACK_SITE_SPECIFICITY_V5/)
- [Corrected runner, source model, and independent verifier](model/M2_FEEDBACK_SITE_SPECIFICITY_V5/)
- [Development and held-out outputs](data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5/)

## Previous synthetic experiment: M5 eligibility trace on learnable delayed XOR V2

The earlier M10 XOR run was inconclusive because even BPTT stayed near chance. After an outcome-informed optimizer calibration, V2 used a fixed Adam optimizer and fresh task seeds on the learnable four-step delay. Held-out accuracy was `0.7347` for the local eligibility trace, `0.5529` for the no-trace local update, and `0.9997` for BPTT. The paired trace-minus-no-trace difference was `+0.1819` (95% task-seed bootstrap interval `[+0.1141, +0.2485]`; 24/30 seeds positive). BPTT passed the task-viability check but remained much stronger than the trace.

This is a post-result synthetic optimization study. It supports a narrow short-delay improvement over the immediate local-update ablation; it does not show parity with BPTT, long-delay transfer, biological validation, or general AI benefit. Compute cost was not matched.

- [Contract, results and failure log](summery/M5_ELIGIBILITY_TEMPORAL_XOR_V2/)
- [Runner and independent verifier](model/M5_ELIGIBILITY_TEMPORAL_XOR_V2/)
- [Episode outcomes and manifest](data/results/M5_ELIGIBILITY_TEMPORAL_XOR_V2/)

## M8 secondary analysis: equal-budget replay versus truncated history

A post-result analysis of the M8 delayed-credit benchmark compared exact replay with a truncated horizon storing the same nominal number of recent feature values (`D × 64`). Exact replay exceeded the matched horizon by `0.3082` absolute held-out accuracy (30.82 percentage points; paired task-seed bootstrap 95% interval `[0.3019, 0.3142]`; 30/30 task seeds favored replay). The advantage increased with delay, from `0.2079` at D=4 to `0.4271` at D=64.

This is a boundary result for one synthetic random-feature task: the truncated-horizon arm did not use its nominal feature-history budget more effectively than exact replay. It does not directly test the eligibility-trace update rule used in M5, and it does not establish replay as universally better. The budget counts active learner feature-history values, not measured process memory; shared task arrays and delayed-prediction history are excluded. This analysis was selected after the M8 outcomes were known, reuses the same 30 task seeds, and is descriptive rather than an independent or confirmatory experiment. Biological evidence supports a timed climbing-fiber teaching event in delay eyeblink learning, while the eligibility-trace equation remains a computational hypothesis; see the [M5 biological evidence and claim boundary](summery/M5_CEREBELLAR/RESULTS.md). These artificial results provide no biological validation.

- [Analysis contract, result and limitations](summery/M8_MEMORY_MATCHED_REPLAY_ANALYSIS/)
- [Analysis script](model/M8_MEMORY_MATCHED_REPLAY_ANALYSIS/)
- [Archived source metrics and regenerated outputs](data/results/M8_MEMORY_MATCHED_REPLAY_ANALYSIS/)

## M5 fresh-seed test: eligibility trace on an accuracy–memory frontier

The M5-style eligibility trace was added to the same synthetic delayed-credit task family on task seeds 30–59, disjoint from M8's seeds. It exceeded the immediate-feature update by `+0.2191` held-out accuracy on average (paired task-seed bootstrap 95% interval `[+0.2094, +0.2287]`; 30/30 seeds positive). Mean accuracy was `0.5473` with 64 active feature-history values, compared with `0.5215` for the 4,096-value `HORIZON_64` arm and `0.7480` for exact replay. The effect varied with delay and autocorrelation; shorter-delay finite horizons won in several cells.

This is an exploratory result on one artificial task generator selected after earlier outcomes. The memory count is algorithmic state accounting, not measured RAM or energy. The trace does not beat exact replay, and the experiment does not validate a biological synaptic eligibility trace. See the [contract, results, and runtime failure record](summery/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/), [model and verifier](model/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/), and [fresh-seed outputs](data/results/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/).

## Previous experiment: M2 closed-loop active-sensing transfer V1

This synthetic benchmark closes the loop between estimation and action: the agent's motor mode changes whether the next observation contains target information. In the aligned setting, the mode-gain filter beat the constant-gain ablation on mean distance (`0.28436` vs `0.32053`; constant-minus-mode `+0.03617`, crossed 95% interval `[+0.02959, +0.04258]`). However, the generic additive RNN (`0.20710`), bilinear RNN (`0.25015`), GRU (`0.26547`), and Bayesian posterior-mean observer (`0.14296`) all had lower mean distance. The Bayesian observer shares the same greedy controller and is not an optimal active-sensing policy.

The mode-gain advantage also reversed when the context-to-observation mapping changed: mean distance was worse than constant gain in INDEPENDENT (`0.38406` vs `0.33106`) and REVERSED (`0.47153` vs `0.34678`). In REVERSED, the Bayesian observer's unchanged prior left the greedy controller holding in an uninformative mode; this is an action-policy information deadlock. The result therefore narrows the claim: a small aligned advantage over the direct ablation did not establish superiority over stronger recurrent controls or robustness to mapping shift.

This is an exploratory one-dimensional synthetic control task, not biological validation or broad AI evidence. Earlier M2 outcomes were known before this study.

- [Contract, results and failure log](summery/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/)
- [Runner, finalizer and verifier](model/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/)
- [Episode outcomes, summary and manifest](data/results/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/)

## Earlier experiment: M2 forward-state sensory gate transfer V3

V3 varied latent persistence, process noise and observation noise during training, then tested in-range conditions and high/low-persistence extrapolations. It adds an unconstrained bilinear recurrent model and a wider GRU to the direct context-free ablation. In `IN_RANGE × ALIGNED`, `MSE(CONSTANT_GAIN_FILTER) − MSE(MODE_GAIN_FILTER)=+0.00929` (crossed 95% interval `[+0.00802,+0.01068]`; 20/20 training-seed means positive). The mode filter's MSE was 0.05358, versus 0.05846 for the bilinear RNN and 0.06209 for the 17-parameter GRU; the task-aware Kalman oracle remained better at 0.05125.

The result depended on the state-to-observation relation: within-range independent and reversed mappings favored the constant-gain ablation by 0.01435 and 0.03201 MSE. High-persistence aligned extrapolation increased the gate's advantage over constant gain to 0.10924, but the reversed mapping caused a 0.30669 MSE penalty. This is conditional performance on one synthetic estimation family, not broad AI benefit or biological validation. V3 is exploratory because earlier versions' outcomes were known; secondary intervals are descriptive and not multiplicity-adjusted.

- [V3 contract, results and failure log](summery/M2_FORWARD_STATE_SENSORY_GATE_V3/)
- [V3 runner, finalizer and independent verifier](model/M2_FORWARD_STATE_SENSORY_GATE_V3/)
- [V3 machine-readable outputs](data/results/M2_FORWARD_STATE_SENSORY_GATE_V3/)

### Post hoc downstream-decision probe

Frozen V3 estimates were also evaluated on sign choice, a thresholded engage/abstain choice, and persistent sign actions with switching cost. On in-range aligned episodes, the mode-gain model improved sign accuracy (`0.701` vs `0.672` for constant gain) and persistent action utility (`0.690` vs `0.656`); the Kalman oracle remained better (`0.707` and `0.699`). Under reversed mapping, mode-gain sign accuracy fell to `0.595`, below constant gain (`0.673`). This reuses the same state-estimation episodes and adds post hoc readouts; it is not a new task family, policy-learning result, or biological validation. See [decision-probe results](summery/M2_FORWARD_STATE_DECISION_TRANSFER_V1/RESULTS.md) and [analysis artifacts](data/results/M2_FORWARD_STATE_DECISION_TRANSFER_V1/).

## Earlier corrected experiment: M2 forward-state sensory gate transfer V2

V2 corrects an implementation bug in V1: V1 trained on clean latent targets as model inputs but evaluated with gated/noisy observations. V1 metrics are invalid and retained only for provenance; see the [implementation incident](summery/M2_FORWARD_STATE_SENSORY_GATE_V1/IMPLEMENTATION_INCIDENT.md).

In the corrected synthetic task, the learned mode-gain filter beat the four-parameter, one-state generic RNN in ALIGNED (`MSE(RNN) − MSE(mode-gain)=+0.15479`, crossed 95% interval `[+0.13915,+0.17098]`) and a context-free constant-gain filter (`+0.11812`, interval `[+0.10310,+0.13381]`). The learned forward/reverse gains averaged `0.626` and `0.024`; the task-aware Kalman reference was slightly better in ALIGNED (`0.26103` vs `0.26310`).

The benefit was mapping-dependent. In INDEPENDENT, mode-gain was worse than constant gain by `0.08168` (interval `[-0.09044,-0.07344]`); in REVERSED it was worse by `0.27462` (interval `[-0.29150,-0.25838]`). V2 is exploratory because V1's outcome was inspected before correction. It supports only a conditional algorithmic result on this synthetic task and does not establish biological implementation or broad AI benefit.

- [V2 contract and results](summery/M2_FORWARD_STATE_SENSORY_GATE_V2/)
- [V2 runner, finalizer, and verifier](model/M2_FORWARD_STATE_SENSORY_GATE_V2/)
- [V2 machine-readable outputs](data/results/M2_FORWARD_STATE_SENSORY_GATE_V2/)
- [V1 incident record](summery/M2_FORWARD_STATE_SENSORY_GATE_V1/IMPLEMENTATION_INCIDENT.md)

The prior reliability-context experiment below remains separate; its reliability mapping is not established by the worm study.

## Earlier synthetic experiment: M2 context-conditioned update transfer V1

The mode-conditioned gain filter was compared with a four-parameter scalar RNN on a synthetic latent-state estimation task. The primary aligned-condition contrast `MSE(RNN) − MSE(mode-gain filter)` was `+0.10401` (crossed 95% bootstrap interval `[+0.09321, +0.11569]`; 20/20 training-seed means positive). The effect was conditional: with context independent of sensor reliability, the context-free filter had lower mean MSE than the mode-conditioned filter; when the learned context/reliability mapping was reversed, the RNN outperformed the mode-conditioned filter (`−0.03516`, interval `[−0.04811, −0.02131]`).

This result tests one synthetic task family and one narrow generic RNN baseline. The reliability-context relationship is an artificial hypothesis, not established by the worm study. The task-aware Kalman reference is not capacity matched and does better in the independent and reversed conditions. The experiment is exploratory at the project level because M2 biology and earlier M2 outcomes were already known; it is not a biological replication or a general AI claim.

- [Experiment contract](summery/M2_CROSS_TASK_STATE_FEEDBACK_V1/CONTRACT.md)
- [Results and failure log](summery/M2_CROSS_TASK_STATE_FEEDBACK_V1/)
- [Runner, verifier, and plot source](model/M2_CROSS_TASK_STATE_FEEDBACK_V1/)
- [Machine-readable outputs and figure](data/results/M2_CROSS_TASK_STATE_FEEDBACK_V1/)

## Prior source-model experiment: M2 feedback-site specificity V4

V4 reused V3 development data to select a motor-only feedback coefficient by minimizing standardized error across four forward-run duration summaries, then evaluated 200 new seed blocks. The sensory-site minus motor-only warm-direction-index contrast was `+0.14128` (95% seed-block bootstrap interval `[+0.13798, +0.14460]`; 200/200 blocks positive). However, the control did not match persistence: at noise multiplier 0.75, mean run duration still differed by `2.506 s` and the 90th percentile by `8.810 s`. This outcome-informed source-model stress test cannot attribute the contrast specifically to feedback placement. It is not biological validation or evidence of AI transfer.

- [V4 experiment contract](summery/M2_FEEDBACK_SITE_SPECIFICITY_V4/CONTRACT.md)
- [V4 results and failure log](summery/M2_FEEDBACK_SITE_SPECIFICITY_V4/)
- [V4 runner and independent verifier](model/M2_FEEDBACK_SITE_SPECIFICITY_V4/)
- [V4 machine-readable outputs and verification](data/results/M2_FEEDBACK_SITE_SPECIFICITY_V4/)

V3's smaller contrast (`+0.08057`) came from matching only mean run duration; its broader run-duration distribution also differed. V3 and V4 are exploratory source-model analyses, not independent biological validation. They remain separate from the new synthetic transfer test. See [V3 results](summery/M2_FEEDBACK_SITE_SPECIFICITY_V3/RESULTS.md).

Reproduce to a fresh result directory from the repository root with:

```bash
python3 model/M2_FEEDBACK_SITE_SPECIFICITY_V4/run_experiment.py \
  --output-dir data/results/M2_FEEDBACK_SITE_SPECIFICITY_V4_RERUN
python3 model/M2_FEEDBACK_SITE_SPECIFICITY_V4/verify_results.py
```

The runner refuses to overwrite an existing output directory. The original executed code is preserved as `run_experiment_executed.py`; the current runner adds output-directory selection for reproducibility. To verify the archived result, run the verifier without arguments.

## Repository layout

| Directory | Contents |
|---|---|
| `model/` | Experiment-specific model implementations and verification scripts. |
| `data/raw/` | Acquired source data and provenance records. |
| `data/results/` | Machine-readable experiment outputs, run manifests, and figures. |
| `experiments/` | Experiment definitions, contracts, and analysis records. |
| `summery/` | Experiment summaries, interpretation, limitations, and project synthesis. |
| `src/` | Shared biological and mechanism abstractions. |

Every experiment has a unique ID, its own contract and result summary, and a separate GitHub commit. Negative, null, and inconclusive results are retained alongside positive results.

## Evidence and claim boundaries

- The M1 result is partial; it does not establish mechanism specificity or an overall RR19 verdict.
- M2 biological evidence is bounded to the published thermotaxis conditions and cell-class granularity. The Figure 6C public source sheet lacks animal/session linkage, so the project reanalysis is descriptive.
- M2 source-model simulations test artificial counterfactuals. They do not establish a unique causal synapse or general AI benefit.
- A cross-mechanism claim requires each mechanism to beat its own mechanism-targeted, capacity-matched controls. Task-specific metrics remain separate.
- **Publication readiness has not been established.** The current work is moving toward a focused comparative benchmark and a manuscript-level novelty assessment.

## Citation and data provenance

Each experiment's summary links to its source article, acquired files, checksums, contract, runner, and result manifest where available. Consult those experiment records before reusing a result or making a broader claim.
