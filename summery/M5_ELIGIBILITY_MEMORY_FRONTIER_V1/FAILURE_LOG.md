# Failure and limitation log — M5 eligibility trace memory frontier V1

## Canonical run status

The canonical run completed with 2,520 task-metric rows, 2,520 update-coverage rows, and 72 paired-contrast rows. The independent verifier recomputed the primary mean from seed-level outcomes and checked row uniqueness, allowed seeds/generators/delays/arms, finite outcomes, state accounting, update-coverage invariants, and manifest SHA-256 values.

## Implementation issue caught before canonical run

Pilot checks exposed an off-by-one/history-order issue in the FIFO update path: for a delay of `D`, the buffer must still contain the cue from exactly `D` steps earlier when its label arrives. The runner was corrected so delayed updates are applied before adding the current cue, initial cues are retained during warm-up, and the final pending cues receive updates during flush. Eligibility state also decays through the flush. The canonical outputs were produced only after this correction. The FIFO coverage invariant is full when capacity is at least the delay and otherwise equals capacity/3,000 because evicted cues are skipped.

This correction changed implementation timing to match the declared delay semantics; it was not chosen from outcome comparisons. The explicit coverage output is retained because small FIFO capacities skip most updates at longer delays.

## Limits and risks

- The positive aggregate contrast is dominated by delays at which `EXACT_FIFO_64` cannot retain the labeled cue and skips almost every update. It must not be described as a clean algorithmic win over a functioning exact-memory baseline.
- Delay 1 is a counterexample: direct exact cue retention beats the decaying trace.
- Exact replay reaches substantially higher accuracy when allowed memory proportional to delay; the trace does not beat the adequate-capacity reference.
- The task family, generators, decay, and optimizer settings are fixed. Three input generators are not three independent task domains.
- Active feature values are a declared algorithmic state count, not process memory, compute, or energy measurements. Shared queues and fixed dataset storage are excluded.
- This is post-result exploratory work in an already studied M5 family. No biological outcome, biological mechanism test, or general AI conclusion follows.

## Next experiment implication

Do not repeat the trace-versus-one-vector-FIFO contrast as evidence of general benefit. A useful follow-up would carry an explicit memory/accuracy frontier into a distinct delayed-reward objective and include adequate-capacity exact replay plus a stronger compressed/adaptive-memory baseline. Keep task-native outcomes separate.
