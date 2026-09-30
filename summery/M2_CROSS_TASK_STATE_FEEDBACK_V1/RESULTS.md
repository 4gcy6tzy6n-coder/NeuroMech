# Results — M2 cross-task state-feedback transfer V1

## Result

The primary contrast was `MSE(GENERIC_RNN_1D) − MSE(MODE_GAIN_FILTER)` in the aligned synthetic condition. It was **+0.1040** (crossed 95% bootstrap interval **[+0.0932, +0.1157]**; 20/20 training-seed means positive), favoring the context-conditioned gain filter over the four-parameter scalar RNN in that condition.

The advantage depended on the context-to-reliability mapping. In the independent condition, the contrast was +0.0417 (95% interval [+0.0297, +0.0547]), but the context-free constant-gain filter had lower mean MSE than the mode-conditioned filter (0.1732 vs 0.2205). Under the reversed mapping, the contrast changed sign to −0.0352 (95% interval [−0.0481, −0.0213]); the generic RNN outperformed the trained mode-gain rule. The analytic Kalman reference, which has access to task assumptions and is not capacity matched, had lower mean MSE than the mode-gain rule in the independent and reversed conditions.

## Interpretation

This is evidence that an explicit context-conditioned sensory update can help on this one synthetic latent-state estimation family when the context predicts observation reliability. Reversing that relationship reverses the relative result. The experiment therefore supports a **conditional, domain-dependent algorithmic effect**, not a broad AI benefit.

The worm literature motivates the abstraction that motor-state feedback can modulate sensory processing. It does not establish the synthetic assumption that motor state predicts sensor reliability, nor that the worm implements this fitted filter. No new biological claim follows from this run.

## Verification and artifacts

The independent verifier passed: 153,600 metric rows were complete, the primary four-parameter model comparison was recomputed, and the primary estimate and crossed interval matched. See `data/results/M2_CROSS_TASK_STATE_FEEDBACK_V1/POSTRUN_VERIFICATION.json` and the run manifest. The metric table SHA-256 is `2a84aa976b14617a07007778bc1ea54b40850df7797c033cdd4f790e6df25c12`.

- Frozen experiment contract: this directory's `CONTRACT.md`.
- Runner and independent verifier: `model/M2_CROSS_TASK_STATE_FEEDBACK_V1/`.
- Machine-readable outcomes: `data/results/M2_CROSS_TASK_STATE_FEEDBACK_V1/`.
- Known limitations: this directory's `FAILURE_LOG.md`.

The experiment was specified before its own outcome, but M2 biology and prior M2 artificial outcomes were already known. It is exploratory and outcome-informed at the project level, not confirmatory.
