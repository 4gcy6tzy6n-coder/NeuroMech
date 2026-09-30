# M2 context-information dose response V1 — failure and limitation log

## Contract correction before outcome inspection

The first contract draft requested focal estimates at `κ=±0.25`, but the frozen test grid advanced in `0.10` increments and did not contain those points. Before reading the episode-metric CSV, the focal values were corrected to the symmetric nearest points `κ=±0.20`; the runner and generated outcomes were unchanged. This correction is recorded in the contract. All results are exploratory regardless, because prior M2 outcomes informed the question.

## Scientific limits

- The context-to-observation equation is an artificial abstraction motivated by the M2 literature, not a measured RIM–AIY transfer function.
- All learners are trained at full alignment. The dose curve therefore combines context informativeness with test-time distribution shift from the training mapping; it is not a comparison of policies retrained or adapted at every κ.
- The mode-gain benefit appears only near strong alignment. It is not a broad advantage: the constant-gain filter is better through `κ=+0.20`, and the estimate at `+0.30` is unresolved.
- The test episodes form one fixed cohort shared across conditions. Crossed bootstrap uncertainty addresses training seeds and sampled test episodes but cannot substitute for broader task-generation and task-family replication.
- The Kalman oracle receives the true episode dynamics and mapping and is a reference, not a capacity-matched competitor.
- No result here validates a new biological claim, directly tests an animal, or establishes general AI benefit.
