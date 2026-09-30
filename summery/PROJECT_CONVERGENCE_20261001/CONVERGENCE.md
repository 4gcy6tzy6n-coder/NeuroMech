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
| M2 / AFD–AIY–RIM feedback | Published cell-class-level intervention and activity evidence supports motor-state feedback affecting AIY representation and forward-run persistence in the studied thermotaxis context. A source-data reanalysis is descriptively consistent with shorter runs after RIM ablation. | The public event sheet lacks animal/session IDs; the reanalysis cannot support animal-level uncertainty. Existing artificial gates have not shown a robust advantage over stronger generic/adaptive controls. Synthetic mode-dependent noise is not established by the biological paper. | Retain as a biological computation case. Test the transfer claim against a generic adaptive controller under explicit, measured task contexts. Keep simulation outcomes separate from the biological evidence. |
| Cross-mechanism benchmark | The project has not yet run one shared benchmark with consistent resource accounting and matched counterfactuals. | Existing M1 and M2 outcomes use different tasks, units, estimands, and experimental status; their raw metrics cannot be pooled into one effect. | Build one benchmark harness with per-mechanism task adapters and identical comparison rules. Report within-task contrasts separately; a joint claim requires both mechanisms to meet their own frozen criterion. |

## Audit of work already completed

The “no experiments have started” premise is contradicted by the current repository. For example:

- M1 H1–H3 partial computation and M1 H4 post-result follow-up are recorded in [`RR19_STEP4_PARTIAL_RESULTS.md`](../../experiments/m1_higher_order/RR19_STEP4_PARTIAL_RESULTS.md) and [`RR19_H4_EXTERNAL_POSTRESULT_INTERPRETATION.md`](../../experiments/m1_higher_order/RR19_H4_EXTERNAL_POSTRESULT_INTERPRETATION.md).
- M2 feedback-site V2 reports a positive warm-direction-index contrast after matching mean run duration, while documenting remaining dynamical mismatches in [`M2_JI2021_FEEDBACK_SITE_CONTROL_V2_RESULTS.md`](../M2_JI2021_FEEDBACK_SITE_CONTROL_V2/M2_JI2021_FEEDBACK_SITE_CONTROL_V2_RESULTS.md).
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
2. Resolve the M1 input limitation before claiming a new M1 test: the frozen fixed-skew image substrate needed for H4 is incomplete. Existing author-precomputed outputs do not replace the required raw inputs or make a fresh confirmatory run.
3. For M2, define a genuinely new held-out simulation regime and compare feedback-site gating with residual-adaptive and capacity-matched controls. Because earlier outcomes have been inspected, label this next M2 run as outcome-informed unless it uses a genuinely independent task/data source.
4. Run both mechanism modules only after their inputs, runner, task units, and result schemas are reproducible. If M1 cannot obtain valid new inputs, report that limitation and do not let M2 alone carry a cross-mechanism claim.
5. Save code in `model/`, outcomes in `data/results/`, and this project synthesis and experiment summaries in `summery/`. Push each completed experiment as its own commit to `experiment-publication`.

## Stop conditions for claims (not for doing work)

- A successful benchmark supports only the tested computation, task, and boundary conditions; it does not establish a general AI advantage.
- A negative or mixed result is retained and narrows the mechanism's operating conditions; it is not repaired by changing metrics after inspection.
- No artificial result is described as a new biological validation.
- Publication readiness remains unestablished until the unified studies, complete provenance, independent verification, and manuscript-level novelty assessment are finished.

## Decision

The active work is now **convergence and comparative experimentation**, not candidate expansion. The current record does not yet support a positive M1+M2 cross-mechanism transfer claim. The next project deliverable is the shared benchmark implementation, with M1 input recovery and M2 held-out comparative evaluation treated as explicit work items.
