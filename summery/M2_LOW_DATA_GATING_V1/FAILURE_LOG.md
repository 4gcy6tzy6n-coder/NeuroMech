# M2 low-data conditional-update benchmark V1 — limitations and failure notes

## What did not generalize

- The state-conditioned filter's aligned advantage did not survive an independent mapping: the generic additive RNN was better by about 0.013 MSE.
- Reversing the context mapping made the structured filter substantially worse (generic-minus-mode about −0.029 to −0.030 MSE).
- Increasing the unique training set from 16 to 1024 sequences did not materially change the aligned contrast. This run therefore does not show that the biological-inspired update has a distinctive low-data scaling curve.

## Design limits

- The observation map was created for a synthetic task and is not established as a worm-circuit measurement. Do not describe it as the experimentally demonstrated AIY computation.
- The capacity-matched generic baseline has four parameters but only an additive scalar tanh update. It cannot directly express an input-by-context interaction. This makes the benchmark informative about the value of a built-in interaction against a minimal comparator, not a broad architecture contest.
- Earlier M2 results against bilinear/recurrent and task-aware estimators remain relevant and stronger controls have been competitive or superior. This run must be read with those results, not in isolation.
- The primary is outcome-informed at the project level and explores only one synthetic family. No multiplicity adjustment was needed for the single prespecified primary, but secondary mapping contrasts are descriptive.
- Four training-set sizes share each seed's nested data pool; the primary seed bootstrap respects that clustering. The seed interval does not treat individual time points or episodes as independent training-seed replicates.
- Equal parameter count and equal optimizer token budget do not imply equal floating-point operations. Wall time is retained as an execution diagnostic, not a hardware-independent efficiency claim.

## Next experimental correction

If this mechanism is pursued further, the decisive comparator should be a generic multiplicative/bilinear model with enough parameters to express the same interaction, plus a task-aware filter reference, and the study should test an independently designed task family. The new contract must be written before any such outcomes are inspected. No current result warrants claims of biological validation, task-general transfer, or NMI readiness.
