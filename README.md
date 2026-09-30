# NeuroMech

**NeuroMech studies how experimentally supported computations in real nervous systems can inform artificial systems.** The project focuses on computational operations—what information is used, how internal state is updated, and under what conditions—not on copying a connectome or treating biological and artificial units as identical.

Biological findings, computational abstractions, and artificial-system results are tracked separately. A model result does not count as new biological validation.

## Current research focus

The project is converging on a small set of mechanism-grounded studies rather than expanding its candidate list.

| Line | Biological question | Current artificial evidence |
|---|---|---|
| **M1 — higher-order visual-motion correction** | What does a source-defined third-order correction contribute to fly motion estimation? | The existing RR19 natural-scene run is partial and exploratory. H1/H3 were in the predicted direction, while the phase-mismatched specificity contrast H2 was in the opposite direction. H4 and an overall four-hypothesis verdict are not established. See [partial results](experiments/m1_higher_order/RR19_STEP4_PARTIAL_RESULTS.md). |
| **M2 — motor-state feedback** | How does RIM-dependent motor-state feedback shape AIY sensory representation and persistence in *C. elegans* thermotaxis? | Cross-dynamics synthetic tests find a small aligned-condition gain over direct context-free and generic controls, larger benefit under high persistence, and negative transfer when state/observation alignment changes. A Kalman oracle remains best. Exploratory algorithmic evidence only. See [V3 results](summery/M2_FORWARD_STATE_SENSORY_GATE_V3/RESULTS.md). |
| **Cross-mechanism benchmark** | Do mechanism-specific computations outperform capacity-matched generic controls under the task conditions that make those computations relevant? | A shared benchmark is in development. M1 and M2 use distinct tasks and native outcome measures; raw scores will not be pooled. See the [project convergence record](summery/PROJECT_CONVERGENCE_20261001/CONVERGENCE.md). |

## Active integrated study: O3 AIY state-pattern rescue

The next mainline study is a prospective *C. elegans* thermotaxis experiment asking whether restoring the forward-state timing of AIY activity under RIM perturbation rescues thermosensory gating and forward-run persistence. Its decisive control is the same AIY stimulation waveform delivered at yoked times, matched for total light exposure. Broad motor-state sensory gating and AIY optogenetic control are already established; the candidate contribution is the specific timing-dependent rescue in the RIM–AIY thermotaxis circuit, not the general phenomenon. The focused literature audit and executable design outline are in [O3 route plan](experiments/biological_validation/O3_AIY_STATE_RESCUE_NOVELTY_AND_EXECUTION_PLAN.md).

The current M2 AI-side experiment remains an exploratory synthetic boundary test. Its sensor-reliability mapping is not established by the worm study and will not serve as the central biological transfer claim. An artificial state-gated update benchmark can continue in parallel with experimental preparation, but its result remains conditional until the biological computation is directly tested.

## Latest experiment: M2 forward-state sensory gate transfer V3

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
