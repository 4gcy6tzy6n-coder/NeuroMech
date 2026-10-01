# Failure and limitation log — M2 premotor predictive-signal transfer V1

- The synthetic cue directly reports the four-step-ahead hidden state with stipulated reliability. It is not a neural trace and makes the cue-value result an information-channel test, not evidence of biological transfer.
- At the aligned condition the structured filter lost to the 45-parameter GRU. V1 had no parameter-matched generic recurrent comparator, so it could not isolate an architectural advantage.
- Training/test cue-mapping mismatch reduced performance. Under reversed mapping, both cue-using models fell below their no-cue ablations; the structural filter was less damaged than the GRU but not better than removing the misleading cue.
- Seed-block resampling summarizes simulated task seeds and does not model biological uncertainty or external task distributions.
- The verifier checked artifact completeness and summary arithmetic, not an independent retraining implementation. V2 preserves paired initialization and adds a matched six-parameter recurrence.
