# Mechanism Evidence Registry

Machine-readable source of record: [MECHANISM_EVIDENCE_REGISTRY.json](MECHANISM_EVIDENCE_REGISTRY.json). Each row specifies functional and structural observables, neuron-ID mapping, provenance class, whether the evidence is independent of connectivity, allowed aggregation, and whether a single-neuron claim is permitted. `VERIFIED` describes provenance/artifact facts, not a positive biological or AI outcome. `PARTIAL` is not failure. The registry uses only `VERIFIED`, `PARTIAL`, `EXTERNALLY_UNDERDETERMINED`, `NOT_AVAILABLE`, and `NOT_APPLICABLE` for evidence states.

| ID | Source system | Evidence status | Identity granularity | Artificial abstraction | Implementation status |
|---|---|---|---|---|---|
| **M0_TOPOLOGY_TRANSFER_NEGATIVE_BASELINE** | Historical FRSP/CATD/F1a connectome-transfer lines | `VERIFIED` historical record; scoped negative under tested conditions. F1b was not tested. | Experiment-specific graph nodes; no cross-dataset composition | Historical topology-constrained variants as baselines | `HISTORICAL_ONLY` |
| **M1_HIGHER_ORDER_CORRECTION** | Drosophila visual motion; Chen et al. 2019; Bielefeld panoramic HDR set and Dryad v3 kernel | `PARTIAL`; frozen implementation, no Step-4 outcome | Computation/estimator level; no neuron identity bridge asserted | Fixed source-correspondent higher-order estimator | `OUTSIDE_CURRENT_WORKSTREAM_MANAGEMENT` |
| **M2_STATE_DEPENDENT_FEEDBACK** | C. elegans AFD–AIY–RIM; eLife v3 source workbooks and Cook corrected July 2020 SI 5 | `PARTIAL`; biological E3 identifiable at cell-class level, strong E4 amendment externally underdetermined | Cell class; exact L/R pairing unresolved | Tested synthetic feedback/gating abstractions; no biological reconstruction claim | `M6_STATE_GATE_BELOW_RESIDUAL_ADAPTIVE; NO_GENERAL_TRANSFER_BENEFIT_ESTABLISHED` |
| **M3_STRUCTURE_FUNCTION_CONSTRAINED_INTEGRATION** | 7 dpf larval zebrafish Fish1.5; Zenodo 16893093 and 19231045 v1 | `PARTIAL`; acquisition gate partial; frozen switch-event observable unavailable in the inspected release | Same-specimen neuron ID for explicit crosswalk rows; class provenance unresolved | Candidate structure-conditioned routing/evidence integration | `REGISTERED_BOUNDARY_ONLY_NO_E3_NO_MODEL` |
| **M4_CA3_PARTIAL_CUE_RECALL** | Rodent hippocampal CA3; Nakazawa et al. 2002, Neunuebel & Knierim 2014, Mei et al. 2011 | `PARTIAL`; some paradigms support CA3 involvement, while NMDA-receptor necessity is disputed across protocols | CA3 subregion/population | Classic Hebbian Hopfield vs exact exemplar/MAP; synthetic and post-result | `EXPLORATORY_V2_COMPLETED; NO_TRANSFER_ADVANTAGE` |
| **M5_CEREBELLAR_INSTRUCTIVE_EVENT** | Mouse delay eyeblink conditioning; Kimpo et al. 2014 and Silva et al. 2024 | `PARTIAL`; timed CF/complex-spike teaching role causally supported in this task; exact synaptic rule is inferred | Climbing-fiber/Purkinje cell-type circuit signal | Local decaying eligibility trace vs no-trace, exact replay, batch logistic; synthetic post-result | `POST_RESULT_V3_AND_CROSS_INPUT_VALIDATION; TRACE_BEATS_NO_TRACE_BUT_LOSES_TO_EXACT_REPLAY_AND_BATCH` |

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

## M4 — CA3 partial-cue recall candidate

- **Bounded biological observation:** some rodent spatial-memory paradigms show retrieval of a learned representation with only a subset of cues, with causal and population-level evidence implicating CA3.
- **Counterevidence:** Mei et al. 2011 report preserved full- and partial-cue recall following NMDA-receptor disruption under their protocol, so broad NMDA-dependent necessity is disputed.
- **Mechanistic boundary:** recurrent autoassociation is a plausible explanation, but the cited interventions do not uniquely isolate recurrent collateral computation. No artificial test has been run.
- **Artificial result:** the post-result exploratory v2 benchmark found Hebbian recurrence underperformed exact exemplar/MAP retrieval on its synthetic grid; the comparison was not capacity matched and does not bear on biological validity.

## M5 — cerebellar instructive event

- **Bounded biological observation:** in mouse delay eyeblink conditioning, timed CF stimulation can substitute for the sensory US and CF inhibition during the US blocks learned conditioning; the exact synaptic learning equation remains unobserved.
- **Artificial result:** post-result v3 norm-matched eligibility traces exceeded a no-trace temporal-misassignment control, but lost to exact replay and batch logistic. This supports only a local synthetic credit-assignment effect, not general AI transfer.
- **Provenance:** three M5 experiment versions are retained because post-result reviews identified update-norm confounding and a target-feature norm access issue. See the M5 results record for version boundaries.
