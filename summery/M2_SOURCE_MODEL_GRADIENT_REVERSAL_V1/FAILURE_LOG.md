# Failure and limitation log

## Prespecified interpretation limits

- The source model's positive feedback may increase persistence and delay adjustment after an environmental reversal.
- The output-site arm uses the same coefficient magnitude and sigmoid input, but it is not calibrated to match the sensory-site arm's run-duration distribution or occupancy. A navigation contrast therefore cannot be attributed uniquely to feedback site.
- The gradient schedule and its reversal periods are artificial stress conditions, not measured thermal ecology.
- The 50 simulated agents within a seed block share exogenous random streams and are not independent inferential units; uncertainty is computed across the 100 simulation seed blocks only.
- This is a source-model simulation, not new biological evidence, a learned AI system, or a general AI benchmark.

## Observed control failure

- **Output-site saturation:** the direct transfer of coefficient `1` from the source sensory-state update to the motor-state update produced 100% forward occupancy and 200-second forward runs in every reversal schedule. It is therefore a poor dynamic comparator. The primary sensory-minus-output contrast is retained as specified, but cannot support a placement-specific causal interpretation.
- **No implementation failure detected:** the final runner, analyzer, independent full rerun, and verifier completed successfully. The two CSVs matched byte-for-byte and all 1,500 seed/interval/arm keys were present.

## Follow-up direction

Test self-specific feedback against a cross-agent yoked feedback signal that preserves the feedback input's per-time marginal distribution. Register that as a new experiment; do not retrofit it into this experiment or erase the failed output-control result.
