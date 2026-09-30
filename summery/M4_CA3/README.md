# M4 — CA3-inspired partial-cue retrieval

**Status:** exploratory, post-result synthetic benchmark; not a biological experiment or confirmatory AI-transfer test.

## What was tested

Classic dense Hebbian recurrent retrieval against exact nearest-exemplar/MAP decoding on the same synthetic memories and corrupted partial cues. The MAP comparator is a task-optimal diagnostic under the benchmark's uniform prior and independent symmetric bit-flip process; it is not capacity/resource matched.

## Positive result

The benchmark is fully specified and reproducible across a frozen grid. The recurrent model reached fixed points quickly (mean 3.97 sweeps). At low memory load, it performed well on partial cues.

## Main negative result

On the frozen aggregate grid, recurrent exact recall was 0.5592 versus 0.9919 for exact MAP; mean bit accuracy was 0.8927 versus 0.9961. The recurrent model often converged to a state that was not one of the stored patterns (43.79% of queries).

## Failures and corrections retained

- The first attempted run used random hidden-state initialization despite the v1 contract specifying zero initialization. Retained as `results_v0_random_initialization_deviation/`.
- The contract-conforming follow-up clamped observed bits. That prevents correction of flipped observed cues; retained separately.
- The unclamped v2 correction was made after examining earlier outputs, so it is post-result exploratory evidence.
- Resource costs differ substantially; no compression or compute advantage was established.

## Interpretation boundary

This rejects only the tested classic dense Hebbian implementation as an advantage over exact MAP for this synthetic task. It does not refute biological CA3 partial-cue recall or identify the unique biological substrate.

## Files

- Code: [`model/M4_CA3/run_benchmark.py`](../../../model/M4_CA3/run_benchmark.py)
- Results: [`data/results/M4_CA3/`](../../../data/results/M4_CA3/)
- Detailed results/protocol: this directory.
