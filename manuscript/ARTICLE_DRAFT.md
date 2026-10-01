# Biological provenance is not enough: testing when neural computations transfer to artificial systems

**Status:** Internal working draft, 1 October 2026. Not for submission. This draft is evidence-bounded and must be revised after the pending M2 discriminator and independent-owner M1 disposition are supplied.

**Article-type risk:** The current evidence can support a careful cross-case study of transfer boundaries, but it does not yet establish a general computational principle or a distinctive AI advantage. Whether this is a sufficiently substantial research Article for *Nature Machine Intelligence* remains an editorial risk, not a settled fact.

## Abstract (draft; 141 words)

Neural systems implement computations whose value depends on the information available to a circuit and the task it performs. Yet biological provenance alone does not establish that an abstraction will benefit an artificial system. We examined this distinction using two evidence lines: motor-state feedback in *Caenorhabditis elegans* and climbing-fibre-timed plasticity in cerebellar interval learning. In synthetic controllers, sensory-site motor feedback improved a stability–switching trade-off relative to a matched output-persistence control in selected conditions, but did not consistently outperform no-feedback, recurrent, or task-aware references. In cerebellar analyses, source-derived plasticity weights predicted within-session temporal structure, while a source-defined artificial transfer rule failed its frozen criterion on a task whose trial-specific timing jitter was not represented in its inputs. These cases motivate an evidence framework that separates biological support, computational abstraction and artificial utility. They do not establish a universal law of transfer.

## Introduction

Neuroscience can inform artificial intelligence at several levels. It can suggest architectures, learning rules or computational operations; it can also reveal which signals a nervous system uses and the conditions under which those signals matter. These forms of inspiration are often discussed together, although they make different empirical claims. A biologically observed signal may be real without its proposed abstraction being complete, and an abstraction may be implementable without improving an artificial task.

This distinction matters when a mechanism is translated across systems. A useful transfer claim requires more than resemblance between a biological circuit and an artificial module. The artificial task must expose the information that the proposed computation is meant to use; the implementation must preserve the relevant operation and timing; and comparisons must isolate the contribution from memory, capacity and task-specific inference. These are methodological requirements, not a claim that one universal set of conditions guarantees transfer.

Here we compare two project evidence lines that make these distinctions concrete. The first concerns motor-state feedback in *C. elegans* thermotaxis. Ji et al. reported a RIM-dependent motor-state representation in AIY and a role for this circuit in sustained forward thermotaxis. The biological signal is a premotor/corollary-discharge-like representation, not a direct measurement of post-actuator body velocity. We tested simplified artificial feedback placements under synthetic switching and tracking tasks, with controls that separate placement from persistence and generic recurrence. The second concerns cerebellar interval learning, where granule-cell temporal profiles and climbing-fibre activity motivate a source-defined, reward-timed plasticity rule. We separately examined source-data prediction and an artificial transfer task.

The goal is not to pool unlike endpoints or to claim that these simulations validate the biological circuits. Instead, we ask what the current evidence licenses at each level: source observation, computational abstraction and artificial-system result. Across both cases, positive local contrasts coexist with limitations from comparator strength, task correspondence and outcome-blindness. This motivates a disciplined way to state transfer claims while leaving the stronger hypothesis—that preserving defining information and computation predicts successful transfer—for prospective testing.

## Results

### A three-level evidence ledger separates source findings from artificial tests

We organized each case into three linked but non-interchangeable claims: (1) what the biological source supports; (2) what operation is encoded in the artificial abstraction; and (3) whether that implementation improves a specified artificial task against appropriate controls. A result at one level does not establish the next. In particular, an artificial performance difference is not new biological evidence, and a source-derived variable is not by itself evidence of artificial utility.

For the worm case, the source literature supports RIM-dependent motor-state representation in AIY and a contribution to sustained forward thermotaxis [1]. Our project reanalyses of public traces are consistent with that result, but they are retrospective and do not isolate a new causal mechanism. For the cerebellar case, published interval-learning data support anticipatory granule-cell temporal profiles and reward-timed climbing-fibre activity [2]. The source-style LTD weights used below are model-derived rather than directly measured synaptic strengths. These source boundaries were retained in all artificial comparisons.

### Sensory-site motor feedback changes a synthetic stability–switching trade-off, but does not establish an overall advantage

In a synthetic telegraph-state task, a sensory-state update receiving the previous action signal reached 88.94% accuracy at the primary switch hazard, compared with 82.14% for an equal-parameter output-persistence control (difference, 6.80 percentage points; crossed-bootstrap 95% interval, 6.48–7.12; 30/30 seed means positive). However, the sensory-site arm did not exceed the no-feedback arm (89.05%), a two-unit generic recurrent model (90.21%) or a Bayes filter (90.30%). Its shorter recovery lag than output persistence was accompanied by a higher false action-switch rate. Thus, the experiment identifies a placement-dependent stability–switching trade-off relative to one matched control; it does not show that sensory-site feedback is the most accurate solution.

A separate bursty-observation tracking study found lower mean squared error for sensory-site feedback than for an equal-parameter output-site control and a small generic recurrent control at the long-burst condition. Its contrast against an eight-unit GRU remained unresolved (95% interval included zero), and the prespecified joint criterion was not met. These outcomes are conditional on synthetic tasks and cannot be treated as replications of one common biological computation: the tasks, outputs and controls differ. Together they show why a favorable contrast against a single ablation is insufficient to establish an overall artificial benefit.

The biological variable also limits interpretation. The worm evidence concerns a premotor motor-program/state representation. Some earlier artificial experiments supplied realized post-actuator movement, which is a different observable. Those experiments are therefore retained as generic actuator-observability tests and are not counted as faithful M2 transfer. A pending action-conditioned estimator comparison is designed to distinguish direct execution measurements from inference based on action and sensory history; its result is not available for this draft.

### Source-derived cerebellar weights contain within-session temporal information, but the tested artificial transfer did not pass

An author-code implementation of climbing-fibre-timed LTD was fit on one subset of rewarded trials and evaluated on held-out trials within the same source sessions. Across 16 sessions, the resulting weight vector exceeded uniform weights in 15/16 sessions and CF-time-shuffled weights in 16/16. A fixed ridge readout exceeded the source-derived projection in 14/16 sessions and had higher group means in all three source groups. This is evidence of within-session predictive temporal structure in the modeled weight ordering, not direct measurement of synaptic weights, animal-level generalization, or causal plasticity.

The source-defined rule was then evaluated in an eight-arm synthetic interval task. Mean held-out absolute error was 0.1252 s for CF-timed LTD, 0.1097 s for the no-trace update, 0.1252 s for CF-time-shuffled teaching and 0.1030 s for a generic radial-basis representation; a training-label empirical timer reached 0.0753 s. The frozen transfer criterion was not met. A design audit found that episodes shared the same deterministic temporal profiles while reward-time jitter was sampled independently. The input therefore did not contain trial-specific information about that jitter. This limits what the negative result can say: it rejects utility of this implementation on this task, while leaving untested whether the rule can exploit a better-matched trial-specific signal.

### The cases motivate correspondence checks, not a universal transfer law

Across the cases, biological evidence and artificial outcomes answer different questions. Motor feedback yielded task-local trade-offs that depended on comparator and endpoint. The cerebellar source reanalysis found predictive structure, whereas the artificial task failed to supply the variable needed to test event-specific timing credit. These observations motivate three checks for future transfer studies: identify the source-supported variable at the right biological granularity; encode the same information and temporal relation in the artificial task; and test the claimed operation against capacity-aware, task-aware and mechanism-targeted alternatives.

The present evidence does not establish that these checks are sufficient for transfer, that correspondence predicts success, or that the two cases instantiate one shared algorithm. The framework is a synthesis and a prospective hypothesis. A confirmatory test would need to freeze the source-to-model mapping and the task information structure before outcomes are examined, then evaluate generalization on independent tasks or data.

## Discussion

These analyses show why biological inspiration and artificial utility should be reported as separate empirical steps. In the worm-inspired controllers, the most favorable result was a local placement contrast against output persistence, not a consistent advantage over no feedback, generic recurrence or a task-aware filter. In the cerebellar case, the modeled source rule carried within-session temporal information, but its artificial implementation failed against no-trace and generic-feature controls on a task whose inputs could not encode the episode-specific timing jitter. Neither case supports the claim that biological mechanisms, simply by being biologically grounded, improve AI. The computational operations considered here also sit within established prior art on eligibility traces and action-conditioned recurrent state estimation [3,4]; they are not presented as newly invented algorithms.

The useful conclusion is narrower. Transfer experiments should specify which information the biological computation uses, what operation is being preserved, and whether the artificial task makes that information available. Controls should distinguish an operation-specific effect from added memory, privileged observation, generic recurrence or task-aware inference. Negative or unresolved outcomes should remain tied to the tested implementation and task, rather than being generalized into claims that a biological mechanism is ineffective.

Several limitations constrain the synthesis. The two mechanisms and tasks are heterogeneous, and their metrics cannot be pooled into a common effect size. Much of the artificial portfolio is exploratory or informed by prior project outcomes; it should not be presented as a prospectively independent confirmation. The source-derived cerebellar weights are computational estimates, and the interval-transfer task had an identified information mismatch. The M2 source-aligned action-conditioned comparison remains pending. A separate M1 line is owned and adjudicated outside this manuscript workstream and is not represented here as a completed result. Finally, our framework has not yet been tested prospectively across independent biological mechanisms and task families.

Accordingly, the strongest current manuscript claim is methodological: biological support, computational correspondence and artificial benefit require separate evidence, and local improvements should be interpreted against the controls and information structure actually tested. Whether a correspondence-first design produces more reliable transfer is an open hypothesis. The next study should test that hypothesis prospectively rather than infer it from this heterogeneous portfolio.

## Methods (draft outline; details to be completed from frozen records)

### Evidence selection and claim classification

Report the project-level inclusion rule for the two case studies, source-paper provenance, and the rule used to classify evidence as biological observation, source-data reanalysis, computational abstraction or artificial task result. Provide experiment identifiers and state whether each protocol was preregistered before any outcomes in that experiment, whether it was informed by earlier project results, and the status of independent reruns.

### Worm source evidence and artificial feedback-placement tasks

Describe the source study and the precise premotor-state construct. For each artificial task, provide state dynamics, observation process, controller equations, arm definitions, parameter/training budgets, seed blocks, primary endpoints, bootstrap unit and task-aware references from the corresponding frozen contract. Do not combine telegraph-state accuracy with tracking MSE.

### Cerebellar source-data analysis and artificial transfer task

Describe Dryad acquisition/version, author-code revision, source-session inclusion, trial split, modeled LTD rule, readout and controls. Clarify that weights are source-code-derived estimates. For the artificial transfer task, report the frozen episode generator, arms, paired task-seed analysis and the post-run audit that reward jitter was independent of the episode input profiles.

### Reproducibility and data availability

Link the exact source manifests, hashes, runner versions, contracts, canonical results and independent verifiers for every reported result. Distinguish raw data availability from derived outputs. Record the code commit corresponding to the final submitted analyses.

## Figure legends (provisional)

**Figure 1 | Evidence levels and transfer claims.** Biological observation, source-derived computation, artificial implementation and task result are shown as separate evidence layers. Arrows mark hypotheses requiring tests; no arrow is treated as automatic validation.

**Figure 2 | Worm-inspired feedback placement yields a local trade-off.** Primary telegraph-state placement contrast with no-feedback, generic recurrent and Bayes references; secondary switching and false-switch outcomes. Panel B presents the separate bursty-tracking study without pooling its endpoint with accuracy.

**Figure 3 | Cerebellar source-derived temporal readout and artificial transfer boundary.** Held-out within-session source-data comparisons and the synthetic transfer arm results. Clearly label modeled weights, session-level unit, the negative frozen criterion and the task's independent timing jitter.

**Figure 4 | Correspondence checklist and prospective test.** Source variable, information available to the artificial system, operation, task-native outcome and mechanism-targeted controls. This is a proposed framework, not a validated transfer law.

**Figure 5 (conditional) | Pending M2 discriminator.** Include only after the canonical run, independent verification and full limitations review. Until then, do not show predicted or fabricated outcomes.

## References (working list; verify metadata and citation placement before submission)

1. Ji, N. et al. Corollary discharge promotes a sustained motor state in a neural circuit for navigation. *eLife* **10**, e68848 (2021). https://doi.org/10.7554/eLife.68848.
2. Garcia-Garcia, M. G. et al. A cerebellar granule cell–climbing fiber computation to learn to track long time intervals. *Neuron* **112**, 2749–2764.e7 (2024). https://doi.org/10.1016/j.neuron.2024.05.019.
3. Bellec, G. et al. A solution to the learning dilemma for recurrent networks of spiking neurons. *Nature Communications* **11**, 3625 (2020). https://doi.org/10.1038/s41467-020-17236-y.
4. Shaj, V. et al. Action-conditional recurrent Kalman networks for forward and inverse dynamics learning. In *Proceedings of the 4th Conference on Robot Learning*, PMLR **155** (2021). https://proceedings.mlr.press/v155/shaj21a.html.
