# CROSS_MECHANISM_CONTEXT_MEMORY_V1 — exploratory contract

## Purpose and status

This experiment asks whether two distinct, experimentally motivated computations show task-specific effects under one shared seed, split, resource-reporting, and uncertainty workflow:

1. M2: use a contextual motor-state cue to alter sensory evidence gain.
2. M5: use a decaying eligibility state to assign delayed teaching feedback to the earlier feature.

The mechanisms are biologically distinct and their outcomes will remain task-native. No cross-species circuit, shared biological mechanism, or pooled effect is implied. Prior M2 and M5 outcomes are known; this is an exploratory, outcome-informed extension, not a confirmatory preregistration.

## Frozen M2 experiment

- Latent binary state switches with hazard 0.04. Context is associated with either lower or higher observation noise according to mapping strength `κ ∈ {+1, 0, -1}` (aligned, independent, reversed).
- Train 3-parameter context-gain filter and 3-parameter additive one-state recurrent control on aligned contexts only. No test outcomes are used for fitting.
- Primary native endpoint: held-out latent-state mean squared error. Primary contrast at `κ=+1`: additive control MSE minus context-gain MSE. Also report `κ=0,-1` as operating-boundary conditions.
- 32 independent task-seed blocks; each block contains separate train and test trajectories. Fit is performed per block.
- No biological parameter, source-paper effect size, or animal-level outcome is used.

## Frozen M5 experiment

- Each task seed defines a fixed 16-dimensional linear teacher. On each learning trial, a feature vector appears, followed after delay `D ∈ {1,4,16,64}` by its binary teaching label; unrelated distractor features occur during the delay.
- Compare a local eligibility update (`e = 0.95^D x`), an equal-dimension misassignment control updated on a distractor feature, and a replay reference that retains the original cue. All use the same 16 learned weights and number of trial updates. Replay has an additional 16-dimensional stored cue and is explicitly not capacity matched.
- Primary native endpoint: held-out classification accuracy after 256 online updates. Primary contrast: eligibility minus misassignment-control accuracy, separately for each delay. Replay is a reference, not the primary comparator.
- 32 independent task-seed blocks; each block has separate training and held-out examples.

## Shared analysis and limits

- Bootstrap task-seed blocks, not timesteps or episodes; 10,000 percentile resamples, seed `20261001`.
- Report per-mechanism point estimates and 95% intervals. Do not combine MSE and accuracy, average across mechanisms, or claim one shared effect size.
- The project-level pattern is descriptive and conjunctive: M2 should favor context-gain only under aligned context; M5 should favor eligibility over misassignment at delays where the trace retains useful signal. Failure in either module is retained.
- This benchmark does not validate either biological mechanism, establish a general AI benefit, or constitute an independent confirmation. It cannot support NMI readiness by itself.

## Post-run resource-accounting clarification (2026-10-01)

The persistent-cue reference and eligibility arm each contain 16 learned weights plus 16 internal state dimensions. They are state matched to each other; the persistent cue differs from eligibility by retaining the un-decayed cue. The cue reference is not state matched to the misassignment arm, which has no persistent model state. This clarifies the original resource sentence without changing the predeclared endpoints; the clarification was made after results were inspected and is part of the exploratory record.

## Execution

Runner: `model/CROSS_MECHANISM_CONTEXT_MEMORY_V1/run_experiment.py`
Verifier: `model/CROSS_MECHANISM_CONTEXT_MEMORY_V1/verify_results.py`
Outputs: `data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V1/`
