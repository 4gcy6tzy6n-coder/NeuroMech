# M6 failure and correction record

1. The initial evaluation code used `abs(estimate)` instead of `abs(estimate - target)`. Two output attempts used that invalid metric. Both are retained under the experiment archive's `results_v0_invalid_metric/` and `results_v1_invalid_metric/` folders, explicitly marked invalid, and excluded from inference.
2. The metric correction did not change fitted parameters because training already minimized target-relative MAE. It did change the evaluation result: the state-gated model was worse than the innovation-adaptive comparator, reversing the invalid pilot's apparent direction.
3. The state-gated filter still beat a global-gain filter on the designed high-reversal-noise regime, but lost to an equally parameterized generic residual-adaptive filter. Under equal or reversed context/noise mappings, the state gate degraded further.
4. The oracle HMM is nearly perfect, revealing that this telegraph-target task is simple for a model that knows the generator. This benchmark cannot by itself support a broad AI contribution.

Operational lesson: inspect metric code at the exact accumulation expression and independently recompute outcome summaries from episode-level CSVs before interpreting any result.
