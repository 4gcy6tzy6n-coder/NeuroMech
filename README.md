# NeuroMech

**NeuroMech studies how experimentally supported computations in real nervous systems can inform artificial systems.** The project focuses on computational operations—what information is used, how internal state is updated, and under what conditions—not on copying a connectome or treating biological and artificial units as identical.

Biological findings, computational abstractions, and artificial-system results are tracked separately. A model result does not count as new biological validation.

## Current research focus

The project is converging on a small set of mechanism-grounded studies rather than expanding its candidate list.

| Line | Biological question | Current artificial evidence |
|---|---|---|
| **M1 — higher-order visual-motion correction** | What does a source-defined third-order correction contribute to fly motion estimation? | The existing RR19 natural-scene run is partial and exploratory. H1/H3 were in the predicted direction, while the phase-mismatched specificity contrast H2 was in the opposite direction. H4 and an overall four-hypothesis verdict are not established. See [partial results](experiments/m1_higher_order/RR19_STEP4_PARTIAL_RESULTS.md). |
| **M2 — motor-state feedback** | How does RIM-dependent motor-state feedback shape AIY sensory representation and persistence in *C. elegans* thermotaxis? | A synthetic transfer test finds context-conditioned sensory updating helps when context predicts observation reliability, but its advantage reverses when that mapping is reversed. This is conditional algorithmic evidence, not biological validation or broad AI evidence. See [M2 transfer results](summery/M2_CROSS_TASK_STATE_FEEDBACK_V1/RESULTS.md). |
| **Cross-mechanism benchmark** | Do mechanism-specific computations outperform capacity-matched generic controls under the task conditions that make those computations relevant? | A shared benchmark is in development. M1 and M2 use distinct tasks and native outcome measures; raw scores will not be pooled. See the [project convergence record](summery/PROJECT_CONVERGENCE_20261001/CONVERGENCE.md). |

## Latest experiment: M2 context-conditioned update transfer V1

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
python3 model/M2_FEEDBACK_SITE_SPECIFICITY_V4/verify_results.py \
  --results-dir data/results/M2_FEEDBACK_SITE_SPECIFICITY_V4_RERUN
```

The runner refuses to overwrite an existing output directory. The exact executed script is preserved as `run_experiment_executed.py` beside the current runner. Omitting `--results-dir` verifies the archived result.

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
