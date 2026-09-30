# Failure log and limits — M2 cross-task state-feedback transfer V1

- **Synthetic premise not established biologically:** the context-to-sensor-reliability mapping is invented for this artificial task. Ji et al. supports bounded motor-state feedback effects on sensory processing, not reliability estimation.
- **Narrow task and model family:** this is one scalar latent-state estimation family. The generic comparator is one four-parameter, one-state RNN; it does not represent the full family of recurrent or adaptive baselines.
- **Strong task-aware reference:** the analytic Kalman reference uses known task dynamics and expected observation variance and is not parameter/capacity matched. It outperformed the mode-gain filter in independent and reversed conditions.
- **Context can mislead:** under the reversed mapping, the mode-conditioned filter was worse than the generic RNN and the context-free filter. This is a material operating boundary, not a result to average away.
- **Retrospective project context:** the biological mechanism and many prior M2 artificial results were already known. The test is exploratory at the project level even though this task's conditions and primary estimand were frozen before running it.
- **No generalization claim:** a result on this single synthetic family does not establish broad AI utility, biological implementation, or publication readiness.

No endpoint was changed after observing results, and no biological response data were analyzed in this experiment.
