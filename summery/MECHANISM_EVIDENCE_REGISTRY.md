# Mechanism Evidence Registry

Machine-readable source of record: [MECHANISM_EVIDENCE_REGISTRY.json](MECHANISM_EVIDENCE_REGISTRY.json). Each row specifies functional and structural observables, neuron-ID mapping, provenance class, whether the evidence is independent of connectivity, allowed aggregation, and whether a single-neuron claim is permitted. `VERIFIED` describes provenance/artifact facts, not a positive biological or AI outcome. `PARTIAL` is not failure. The registry uses only `VERIFIED`, `PARTIAL`, `EXTERNALLY_UNDERDETERMINED`, `NOT_AVAILABLE`, and `NOT_APPLICABLE` for evidence states.

| ID | Source system | Evidence status | Identity granularity | Artificial abstraction | Implementation status |
|---|---|---|---|---|---|
| **M0_TOPOLOGY_TRANSFER_NEGATIVE_BASELINE** | Historical FRSP/CATD/F1a connectome-transfer lines | `VERIFIED` historical record; scoped negative under tested conditions. F1b was not tested. | Experiment-specific graph nodes; no cross-dataset composition | Historical topology-constrained variants as baselines | `HISTORICAL_ONLY` |
| **M1_HIGHER_ORDER_CORRECTION** | Drosophila visual motion; Chen et al. 2019; Bielefeld panoramic HDR set and Dryad v3 kernel | `PARTIAL`; frozen implementation, no Step-4 outcome | Computation/estimator level; no neuron identity bridge asserted | Fixed source-correspondent higher-order estimator | `OUTSIDE_CURRENT_WORKSTREAM_MANAGEMENT` |
| **M2_STATE_DEPENDENT_FEEDBACK** | C. elegans AFD–AIY–RIM; eLife v3 source workbooks and Cook corrected July 2020 SI 5 | `PARTIAL`; biological E3 identifiable at cell-class level, strong E4 amendment externally underdetermined | Cell class; exact L/R pairing unresolved | Tested synthetic feedback/gating, placement, and source-model stress abstractions; no biological reconstruction claim | `SOURCE_MODEL_SENSORY_FB_BEATS_NO_FB_IN_SIMULATION; OUTPUT_SITE_CONTROL_SATURATED; NO_AI_TRANSFER_BENEFIT_ESTABLISHED` |
| **M3_STRUCTURE_FUNCTION_CONSTRAINED_INTEGRATION** | 7 dpf larval zebrafish Fish1.5; Zenodo 16893093 and 19231045 v1 | `PARTIAL`; acquisition gate partial; frozen switch-event observable unavailable in the inspected release | Same-specimen neuron ID for explicit crosswalk rows; class provenance unresolved | Candidate structure-conditioned routing/evidence integration | `REGISTERED_BOUNDARY_ONLY_NO_E3_NO_MODEL` |
| **M4_CA3_PARTIAL_CUE_RECALL** | Rodent hippocampal CA3; Nakazawa et al. 2002, Neunuebel & Knierim 2014, Mei et al. 2011 | `PARTIAL`; some paradigms support CA3 involvement, while NMDA-receptor necessity is disputed across protocols | CA3 subregion/population | Classic Hebbian Hopfield vs exact exemplar/MAP; synthetic and post-result | `EXPLORATORY_V2_COMPLETED; NO_TRANSFER_ADVANTAGE` |
| **M5_CEREBELLAR_INSTRUCTIVE_EVENT** | Mouse delay eyeblink conditioning; Kimpo et al. 2014 and Silva et al. 2024 | `PARTIAL`; timed CF/complex-spike teaching role causally supported in this task; exact synaptic rule is inferred | Climbing-fiber/Purkinje cell-type circuit signal | Local decaying eligibility trace vs no-trace, exact replay, batch logistic; synthetic post-result | `M5_CROSSINPUT_PLUS_M7_CORRELATION_DELAY; TRACE_EFFECT_CONDITIONAL; EXACT_REPLAY_SUPERIOR` |

## M0 — topology-transfer negative baseline

- **Definition:** transfer raw connectome-derived topology as an artificial structural constraint.
- **Record:** historical FRSP, CATD, and F1a outcomes remain in their original scope; F1b is `NOT TESTED`.
- **Allowed claim:** no supported attributable topology-transfer advantage was established in the tested settings; this motivates computation-level transfer.
- **Forbidden claim:** topology never matters, or biological mechanisms do not matter.
- **Controls:** only the matched nulls and interventions frozen in each historical branch.

## M1 — higher-order correction

- **Definition:** source-defined second-order estimate with source-defined third-order correction; the RR19 artificial contract specifies `FULL = v2 + v3`.
- **Evidence:** RR19 Step 3 closeout records source correspondence complete, with Step 4 not started and no confirmatory outcome.
- **Frozen arms:** `FULL`, `NO_THIRD_ORDER`, `REVERSED_CORRECTION`, `MISMATCHED_THIRD_ORDER` (source phase scramble).
- **Boundary:** no claim that the third-order term improves velocity accuracy; the frozen primary concerns scene-dependent spatial variability. No separate capacity-matched arm is in the frozen RR19 protocol.
- **Allowed claim now:** a source-grounded artificial test is frozen. No artificial benefit or transfer result is known.

## M2 — state-dependent feedback

- **Definition:** RIM-dependent feedback sustaining/modulating AIY motor-state representation, bounded to cell-class-level evidence.
- **Evidence:** E3 identifiability passed; the strong E4 amendment is externally underdetermined because animal/session linkage and outcome-blind noise/SESOI are not established.
- **Open identity/mechanism boundaries:** no exact left/right functional trace pairing or unique causal RIM→AIY synaptic carrier.
- **Artificial abstraction:** previous-action feedback, mode-gated sensory gain, and a fixed closed-loop gate were explored separately. The gate lost to no-gate/occupancy-matched and memoryless controls in all nine tested cells; the on-policy GRU won on the reused post-result suite. These are synthetic results and establish no AI-transfer advantage.

### M2 M6 computation result — 2026-09-30

A new synthetic telegraph-target estimation experiment trained a state-gated sensory filter on one mode/noise mapping and evaluated independent trajectories at three hazard values. On the stipulated high-reversal-noise profile, the two-parameter state gate beat a single global gain, but it lost to a two-parameter generic filter that adapted gain from prediction residuals at every hazard. Equal-weighted `STATE_GATED_GAIN − INNOVATION_ADAPTIVE` MAE was `+0.07587`, crossed 95% interval `[+0.07314,+0.07864]` (positive means gating was worse). Equal-noise and reversed-noise stress conditions further showed dependence on the assumed mapping. The source paper does not establish that locomotor state encodes observation reliability. The study is exploratory and same-family; it does not establish AI transfer. See [`summery/M6_STATE_GATED_INFERENCE/RESULTS.md`](summery/M6_STATE_GATED_INFERENCE/RESULTS.md).

### M2 Figure 6C source-data reanalysis — 2026-09-30

The published Figure 6C workbook contains 1,008 WT and 3,910 RIM-ablated forward-run events. Event-weighted median durations were 17.0 s and 11.5 s; the RIM-ablated median was lower in all six coarse direction bins. The source sheet does not identify worms for these events, so this is a descriptive reproduction only, with no animal-level p-value or interval. It is consistent with the paper's bounded persistence result but does not establish a new causal carrier or algorithm. See [`summery/M2_RIM_ABLATION_SOURCE_REANALYSIS/RESULTS.md`](summery/M2_RIM_ABLATION_SOURCE_REANALYSIS/RESULTS.md).

### M2 constant-temperature AIY state-decoding reanalysis — 2026-10-01

In the public Ji et al. Figure 2/5 traces, AIY-only held-out motor-state AUC averaged `0.758` in five WT animals and `0.502` in five RIM-ablated animals. Controlling for the immediately previous behavior state reduced the AIY increment to `0.01554` and approximately zero, respectively. AVA showed a similar group shift, so this is consistent with RIM-dependent motor-state coding but does not localize residual coding uniquely to AIY. Time samples were not treated as independent animals. This is a retrospective public-source reanalysis, not new causal evidence. See [`summery/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/RESULTS.md`](summery/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/RESULTS.md).

### M2 AIY prospective motor-state prediction follow-up — 2026-10-01

On the same five WT and five RIM-ablated animals, current AIY activity added 2-second next-known-state prediction AUC over a 5-second motor-history baseline by `0.2098` (WT) and `0.0779` (RIM ablation). The descriptive WT-minus-RIM contrast was `0.1318`; AVA's analogous contrast was larger (`0.2229`). Only 6–18 positive samples occurred per animal, so this does not establish AIY-specificity, causal prediction, or a robust between-group effect. V1's stricter label definition was not estimable in the RIM group and remains documented as a failed target definition; V2 is a post-result exploratory follow-up, not an independent cohort. All 60 model-score rows were independently recomputed and both source workbook hashes verified. See [`summery/M2_AIY_PREMOTOR_STATE_PREDICTION_V2/RESULTS.md`](summery/M2_AIY_PREMOTOR_STATE_PREDICTION_V2/RESULTS.md) and [`summery/M2_AIY_PREMOTOR_STATE_PREDICTION_V1/FAILURE_LOG.md`](summery/M2_AIY_PREMOTOR_STATE_PREDICTION_V1/FAILURE_LOG.md).

### M2 corollary-discharge placement transfer — 2026-10-01

A post-result synthetic mechanism-transfer test compared a three-parameter previous-action feedback term placed in the sensory-state update against the same parameter count placed at the action output. At hazard `0.05`, sensory-site accuracy exceeded output persistence by `+0.06799` (crossed 95% interval `[+0.06475,+0.07120]`) and recovered from state switches faster (1.30 vs 3.56 steps). It did not beat the no-feedback ablation (88.94% vs 89.05%), generic two-unit RNN (90.21%), or Bayes filter (90.30%). This supports only a feedback-placement/stability tradeoff in the stipulated synthetic task. It does not establish that the biological circuit computes this equation or that adding the feedback signal improves AI performance. Full contract and artifacts: [`summery/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/`](summery/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/).

### M2 source-model gradient-reversal stress test — 2026-10-01

The corrected Ji et al. Figure 7 equations were simulated under stationary and sign-reversing spatial gradients. At a 20-second reversal interval, sensory-site feedback exceeded the no-feedback ablation by `+0.07379` environment-aligned progress units/s (95% seed-block interval `[+0.07061,+0.07694]`; 100/100 simulated blocks positive). Progress declined under faster reversal. The coefficient-matched output-site arm saturated at 100% forward occupancy and 200-second runs; its placement contrast is therefore not interpretable. These model outcomes are not biological or AI evidence. Full contract, results, and failure record: [`M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1`](M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/).

## M3 — structure-function constrained integration

- **Definition:** the already frozen Fish1.5 iMI/cMI/MON→SMI visual-motion mechanism; do not narrow the cell set to improve data availability.
- **Evidence:** functional-ID↔EM-ID bridge verified for explicit mapped rows; public structural archive acquired and schema audited; CAVE materialization lineage is unpinned; functional class-label provenance remains unresolved.
- **Blocking substrate:** the frozen direction-switch/evidence-update observable lacks event/time alignment in the inspected functional schema; graded evidence and choice/behavior linkage are not exposed there. Acquisition gate remains `PARTIAL`; E3 is closed.
- **Allowed claim:** same-specimen registration and explicit neuron-ID crosswalk are documented. The current released substrate does not identify the frozen switch-event computation.
- **Forbidden claim:** acquisition gate passed, class labels independently validate the same connectivity pattern, or separate left/right arrays represent within-trial switches.

### M5 cross-input-generator follow-up — 2026-09-30

A fixed-hyperparameter follow-up evaluated 30 new task seeds for each of IID Gaussian, AR(1) Gaussian, and sparse-sign inputs. The equal-generator, four-delay trace-minus-no-trace accuracy difference was `+0.2284`, hierarchical task-seed 95% interval `[+0.2213,+0.2357]`; all generator-level mean contrasts were positive. The objective and readout family remained the same across conditions, so this is robustness to three input-stream distributions, not generalization across unrelated tasks. Exact replay beat the trace in every generator-delay cell. Full artifacts and limits are in [`summery/M5_TASK_GENERATOR_GENERALIZATION/RESULTS.md`](summery/M5_TASK_GENERATOR_GENERALIZATION/RESULTS.md).

## Provenance and non-combination rules

Full publications, artifacts, evidence-layer statuses, allowed/forbidden claims, and counterfactual definitions are in the JSON. No cross-dataset neuron identity matching, cross-species equivalence, or merged biological graph is permitted. Artificial interface consistency is not biological identity equivalence.

### M5 temporal-correlation boundary follow-up — 2026-09-30

M7 swept six AR(1) input correlations, four delays, and separate classification/regression objectives with fixed M5-v3 hyperparameters. The trace-versus-current-input effect was delay-dependent: intrinsic correlation reduced trace benefit at short delays, while that relation reversed at delay 64 for classification and at delays 16/64 for regression. The objective-specific equal-delay rho-0 minus rho-0.9 interactions were positive (classification `+0.2225` accuracy, 95% CI `[+0.2075,+0.2373]`; regression `+0.00238` MSE, `[+0.00216,+0.00260]`), but those scales are not pooled. Exact replay beat the trace in all 48 cells. The first pooled statistic mixed unlike accuracy/MSE units and is explicitly invalidated. See [`summery/M7_TEMPORAL_CORRELATION_BOUNDARY/RESULTS.md`](summery/M7_TEMPORAL_CORRELATION_BOUNDARY/RESULTS.md).

### M5 delayed-reward memory frontier — 2026-10-01

On 30 new contextual-bandit task seeds, the fixed 32-value eligibility trace exceeded current-score assignment by `+0.009480` expected reward (95% paired interval `[+0.007905,+0.011087]`; 30/30 seed averages positive), but lost to equal-state one-vector exact FIFO averaged over delays (`−0.002484`, interval `[−0.003243,−0.001717]`; 1/30 positive). At delays 4–64 the one-vector FIFO applied only 1/6,000 rewards. A FIFO storing at least D score vectors exactly reproduced full replay and outperformed the trace. This is a bounded-memory tradeoff in one synthetic task, not evidence of a cerebellar rule or general AI benefit. See [`summery/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/RESULTS.md`](summery/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/RESULTS.md) and the [canonical outputs](data/results/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/canonical/).

## M4 — CA3 partial-cue recall candidate

- **Bounded biological observation:** some rodent spatial-memory paradigms show retrieval of a learned representation with only a subset of cues, with causal and population-level evidence implicating CA3.
- **Counterevidence:** Mei et al. 2011 report preserved full- and partial-cue recall following NMDA-receptor disruption under their protocol, so broad NMDA-dependent necessity is disputed.
- **Mechanistic boundary:** recurrent autoassociation is a plausible explanation, but the cited interventions do not uniquely isolate recurrent collateral computation. No artificial test has been run.
- **Artificial result:** the post-result exploratory v2 benchmark found Hebbian recurrence underperformed exact exemplar/MAP retrieval on its synthetic grid; the comparison was not capacity matched and does not bear on biological validity.

## M5 — cerebellar instructive event

- **Bounded biological observation:** in mouse delay eyeblink conditioning, timed CF stimulation can substitute for the sensory US and CF inhibition during the US blocks learned conditioning; the exact synaptic learning equation remains unobserved.
- **Artificial result:** post-result v3 norm-matched eligibility traces exceeded a no-trace temporal-misassignment control, but lost to exact replay and batch logistic. This supports only a local synthetic credit-assignment effect, not general AI transfer.
- **Provenance:** three M5 experiment versions are retained because post-result reviews identified update-norm confounding and a target-feature norm access issue. See the M5 results record for version boundaries.

### M2 burst-duration artificial transfer — 2026-10-01

With expected observation availability fixed at 50%, a post-result artificial target-tracking experiment varied mean missing-run length from 2 to 8 steps. Sensory-site motor-state feedback beat the equal-parameter output-site, no-feedback, and generic scalar-RNN controls on long-burst MSE; the 8-unit GRU contrast was unresolved. The joint criterion for a mechanism-specific advantage over strong recurrence was not met. Lower overall tracking error coincided with lower action energy but slower post-gap recovery than output persistence. This supports only an artificial placement effect against the tested small controls, not a biological equation or general AI principle. See [`M2_BURSTY_OBSERVATION_FEEDBACK_V1`](summery/M2_BURSTY_OBSERVATION_FEEDBACK_V1/RESULTS.md).

### M2 artificial predictive-cue transfer probes — 2026-10-01

A paired synthetic switching-state task tested a structured six-parameter forecast-fusion filter against a six-parameter generic recurrent control. At aligned cue reliability `q=0.72`, the structured filter improved over its no-cue ablation (`+0.1053` AUC; 95% seed-block interval `[+0.1017,+0.1087]`) but underperformed the matched generic recurrence by `0.0702` AUC (interval `[−0.0724,−0.0681]`). Both models were harmed when the synthetic cue was uninformative or reversed; the structured filter was less brittle but did not outperform its no-cue ablation. The cue directly encodes noisy future-target information and is not a biological measurement. This outcome-informed artificial probe provides no biological validation or general AI-benefit claim. See [`summery/M2_PREMOTOR_SIGNAL_AI_TRANSFER_V2/RESULTS.md`](summery/M2_PREMOTOR_SIGNAL_AI_TRANSFER_V2/RESULTS.md).
