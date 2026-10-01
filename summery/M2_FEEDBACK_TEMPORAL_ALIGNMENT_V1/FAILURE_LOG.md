# M2 feedback temporal-alignment experiment V1 — implementation and failure log

- **Hypothesis outcome:** the frozen primary prediction failed in the tested task. Four-step-lagged self-feedback had lower, not higher, movement MSE than current self-feedback in `SLOW_TRANSIENT` (paired mean `−0.003858`; 95% seed-block interval `[−0.004294, −0.003409]`). Preserve this as a directional counterexample; do not relabel the lagged arm as the intended mechanism after seeing the result.
- **Strong-control outcome:** the 8-unit GRU had the lowest descriptive mean MSE in all four conditions. The generic recurrent control and output-site placement also beat current sensory-site feedback in the primary condition. This limits any claim that the low-dimensional biological abstraction is useful or distinctive in this simulator.
- **Biological mapping limit:** lags 1 and 4 are arbitrary discrete simulation delays. No source cited for the RIM–AIY evidence establishes these as biological conduction delays, so they are only timing perturbations in the artificial controller.
- **Task-family dependence:** the experiment reuses the earlier binary target-tracking/transient-pulse family. It is an exploratory mechanistic perturbation, not independent task generalization.
- **Execution incidents:** no partial or failed outcome run occurred. The canonical run completed all 32 seed blocks; the independent verifier passed.
- **Inference limit:** only the predeclared LAG4-versus-current contrast is inferential. Other arm and condition means are descriptive and do not support selective post-hoc claims.

## Next useful correction

Do not search over additional lag values or tune this implementation to recover a current-alignment advantage. If temporal filtering is pursued, first derive the exact signal timing and dynamical prediction from an independent biological or computational source, then test it on a distinct task with matched recurrent baselines and an explicit resource budget. Otherwise retain this as a negative transfer boundary and shift project effort to a new, source-grounded computation with a stronger prospective AI translation.
