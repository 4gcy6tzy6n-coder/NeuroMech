# Strengths and failure lessons

## Strengths

- Matches replay and `HORIZON_D` by the contract's active feature-history accounting, rather than comparing trace state to a higher-memory replay without qualification.
- Resamples task seeds as the independent units; all within-seed conditions remain paired.
- Reports correlation × delay cells and does not pool across different tasks as independent samples.
- Uses a deterministic analysis script and pins the exact M8 source CSV hash.

## Limits and failure risks

- The comparison was chosen after seeing M8 outcomes, so it is outcome-informed and descriptive.
- Float-buffer counts are an algorithmic state estimate, not process-level memory measurements. Shared source arrays and stored prediction history are excluded; those are common harness costs, but a production implementation could have different overhead.
- Only one synthetic random-feature classification family is included. Do not generalize to trained recurrent networks, other objective families, biological transfer, or all memory budgets.
