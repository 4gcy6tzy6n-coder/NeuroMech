# M2 2D closed-loop pursuit V1 — failures and limitations

## Outcome failures

- The 8-parameter state-conditioned update lost to the 8-parameter bilinear baseline in ALIGNED final distance and success. It also lost to the 8-parameter additive baseline in final distance.
- The direct context-free ablation performed approximately the same as MODE_GAIN in ALIGNED, so this experiment gives no evidence that the explicit movement-state gain helped.
- Under REVERSED sensor mapping, MODE_GAIN became severely unstable relative to all other learned policies. This reflects the trained mapping's sensitivity and is retained as a boundary result.
- MODE_GAIN achieved the lowest teacher-forced residual-estimation loss, yet was worse in the downstream closed-loop control outcome. The supervised estimator objective therefore did not select the best controller.

## Implementation incidents corrected before canonical outputs

The first full runner attempt stopped before writing result CSVs because the oracle path supplied a vector of motor states to a helper that initially accepted only one scalar state. Vectorized sensor-matrix handling fixed the exception. A training-generation indexing mismatch and the opposite per-coordinate gate initialization were also caught and corrected before the successful canonical run. The canonical run then completed all 30 seeds, passed the independent verifier, and reproduced byte-for-byte in a separate directory. No partial outcome table from the aborted attempt was included.

## Scientific limits

- The mapping between movement axis and reliable sensory coordinate is invented for this task; it is not measured in *C. elegans*.
- Training uses random movement axes; deployment makes movement-axis choices from each model's own estimate. This creates an intentional closed-loop distribution shift but also means the test contrasts estimator quality and induced action distribution together.
- Equal parameter counts and optimizer budgets do not guarantee equal compute or optimization difficulty.
- The oracle uses the exact Gaussian generative model and remains a task-aware reference.
- The experiment is one artificial 2D pursuit task, not independent evidence that the biological mechanism transfers broadly.
