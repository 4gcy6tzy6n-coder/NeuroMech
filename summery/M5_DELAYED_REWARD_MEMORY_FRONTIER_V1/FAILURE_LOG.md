# Failure and limitation log — M5 delayed-reward bandit memory frontier V1

## Result boundary

- The primary equal-state contrast does not favor the trace: trace minus one-vector FIFO is −0.002484 expected reward (95% paired task-seed bootstrap interval [−0.003243, −0.001717]).
- At delay 1, exact one-vector retention beats trace because the trace also contains newer, unrelated decision scores when the previous decision's reward arrives.
- At longer delays, the trace exceeds the one-vector FIFO, but that FIFO applies only one of 6,000 rewards during final flush (0.0167% coverage). It is a weak learning comparator there.
- A capacity-sufficient FIFO is exactly equivalent to exact replay and substantially outperforms the trace. Any claim of general eligibility-trace superiority would contradict these data.
- The trace still beats current-score assignment in this bandit, but the observed gain is modest and task-specific; the exact replay gap remains about 0.039 expected reward averaged over delays.

## Verification correction

The first independent-verifier pass failed because the verifier expected the `NO_TRACE_CURRENT_32` arm to apply all 6,000 rewards. The frozen contract explicitly sets the current score to zero during post-stream reward flush, so the correct expected update count is `6,000 − D`; the runner recorded that behavior. The verifier was corrected to check this declared invariant and then passed. No outcome file, canonical runner, frozen contract, or primary calculation changed. The original pre-run verifier hash and corrected verifier hash are recorded in the post-run audit. This is a verification-script repair, not outcome-driven model tuning.

## Implementation and scope limits

- The current-score control receives no update for the last D rewards during flush, as stated in the frozen contract. Its coverage is therefore `(6,000−D)/6,000`.
- FIFO capacity below D preserves the most recent `capacity` decision-score vectors. With FIFO updates delivered before the current score is inserted, coverage is exactly `capacity/6,000`; a capacity of at least D yields full coverage.
- Exact replay is a higher-state reference. The experiment does not compare against compression methods that use all rewards with an approximate representation of every pending score.
- The shared reward schedule is action-dependent. Common random numbers aid pairing, but policies diverge and observe different realized rewards.
- Active scalar count is a modeling convention; this study did not measure actual process memory, computation, latency, or energy.
- Prior M5 results informed this design. New task seeds provide fresh task draws but do not make the experiment confirmatory or independent of the researcher's accumulated knowledge.
