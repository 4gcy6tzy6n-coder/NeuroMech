# M2 continuous tracking motor-state transfer V1 — failure lessons

- **Transfer prediction not supported:** in the frozen long-burst condition, realized motor-state input was worse than the same GRU receiving its previous command (`+0.009096` MSE; 95% seed-block interval `[+0.001446,+0.016816]`). It was also worse than the zero-input and recipient-yoked arms.
- **The fitted controller family was weak:** a post-run, fixed reactive policy outperformed every trained GRU in all four test profiles. The privileged oracle's very low error confirms the generator is controllable, but its information advantage makes it only an upper bound. The GRU training schedule/optimization was not adequate to support a strong mechanism-transfer claim.
- **The biological variable was over-expanded:** published RIM–AIY evidence supports locomotor-state coding, whereas this transfer provided a continuous 2D actuator-velocity vector. That mismatch was not justified by a direct biological measurement.
- **No outcome repair:** the canonical runner, contract, seeds, and primary contrast were not changed after inspecting results. The reactive/oracle checks are separately labeled post-run diagnostics and excluded from the frozen inference.
- **Reproducibility:** a corrected canonical run passed the independent verifier and an independent full rerun reproduced scientific outputs. No execution incident occurred in the canonical run.

## Follow-up implication

Leave this result as an adverse boundary. Any V2 must define the motor-state variable from the biological source before coding, include a competent task-native reference and validation-based checkpoint selection before the test run, use fresh seeds, and evaluate on a distinct task. It must not start by sweeping motor-noise or observation conditions to search for a favorable cell.
