# CROSS_MECHANISM_CONTEXT_MEMORY_V1 — failure and limitation log

1. **Initial numeric run emitted NumPy matrix-operation warnings.** Although its outputs were finite, it is not canonical. Test projection was changed to an explicit elementwise reduction; the full run was repeated without warnings. A later artifact-format pass set deterministic LF line endings and the final run was verified under `data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V1/canonical/`. The first output is retained under `initial_warning_run_not_canonical/` for provenance and must not be cited.
2. **The M5 misassignment arm is an intentionally destructive negative control.** Applying a label to an unrelated distractor can corrupt weights. Its large contrast with eligibility overstates what it says about the trace. The persistent-cue reference is the relevant equal-state comparator and ties the trace exactly.
3. **The M5 task is deliberately simple.** It uses one cue per trial, a fixed linear teacher, and an isolated delayed label. It does not test overlapping eligibility traces, changing credit horizons, a trained recurrent learner, biological plasticity, or online policy utility.
4. **M2 trains and evaluates within one synthetic generator family.** The context/noise relation is set by construction. The additive control is a narrow 3-parameter baseline, not a modern recurrent model or task-aware Bayesian observer.
5. **No cross-mechanism effect was pooled.** Different task-native outcomes cannot establish a single shared effect from their signs alone. Both modules are post-result exploratory studies.

## Follow-up implication

An M5 follow-up must vary overlapping distractors and the feedback delay while comparing the trace with persistent cue memory under equal learned weights, state dimensions, data, and update count. This is a new outcome-informed experiment, not a repair or confirmation of V1. A stronger generic recurrent and Bayesian reference is also needed before making AI-performance claims for M2.
