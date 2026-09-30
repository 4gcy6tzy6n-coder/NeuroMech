# M5 eligibility trace memory frontier V1 contract

**Experiment ID:** `M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1`

**Classification:** post-result exploratory study on fresh task seeds. The M8 task family, earlier eligibility-trace results, and prior memory-frontier outcomes were known when this comparison was selected. Fresh seeds provide new task instances but do not make this confirmatory.

## Question

In the established synthetic delayed-credit classification family, does the M5-style decaying eligibility vector provide a useful accuracy-versus-active-history-state tradeoff compared with the immediate-feature update, bounded recent-history windows, and exact replay?

## Task and arms

The task is the M8 random-feature classification generator: 32-dimensional AR(1) input with `rho ∈ {0.0, 0.5, 0.9}`, tanh projection to 64 unit-normalized features, four classes from a fixed linear teacher, 3,000 training and 1,000 fresh test examples, and delayed labels `D ∈ {4, 16, 64}`. The master generator seed and task seeds 30–59 are fixed in code; seeds 0–29 were used in the prior M8 frontier and are not reused here.

All arms use the same 64×4 linear readout, the same within-task examples and delayed prediction error, learning rate 0.01, and `gamma=0.98`. Arms are `HORIZON_1/2/4/8/16/32/64`, `ELIGIBILITY_TRACE`, and `EXACT_REPLAY`. A horizon update is the normalized exponentially weighted sum of the most recent H feature vectors, aged to the label-arrival step. The eligibility arm updates a single vector `e_t = 0.98 e_(t−1) + φ_t` and applies the normalized vector with the delayed error. Exact replay applies that error to the stored feature for the labeled cue.

## Resource accounting

Report active feature-history values per arm: immediate `HORIZON_1` retains no past feature vector; `HORIZON_H` for H>1 retains `H×64`; `ELIGIBILITY_TRACE` retains 64; and exact replay retains up to `D×64`. Model weights and delayed prediction histories are shared functional requirements and excluded consistently. This is a logical state-size count, not measured process memory, latency, or energy. All models have equal parameter counts, but update arithmetic and wall-clock compute are not matched.

## Primary and secondary summaries

The primary contrast is `ELIGIBILITY_TRACE − HORIZON_1` held-out accuracy, averaged equally across the nine rho×delay cells within each fresh task seed and then across 30 task seeds. Report the paired task-seed bootstrap 95% percentile interval (20,000 draws; seed 20261008) and positive-seed count. Secondary summaries report the same contrast by delay and rho, the trace's mean accuracy and memory state, and descriptive paired accuracy differences from HORIZON_2, HORIZON_4, and exact replay in every rho×delay cell. Do not treat the 9 cells as independent samples or make multiplicity-adjusted claims from them.

## Interpretation

The experiment can establish only whether this fixed eligibility update occupies a useful point on this task generator's accuracy/active-state frontier. It cannot validate the biological eligibility-trace implementation, establish a general advantage over replay, support transfer to other task families, or make a biological claim. A favorable point means the measured artificial algorithm performed well under the stated state accounting; it does not establish lower deployed memory, compute, or energy.

## Provenance

Record the exact task generator, runner, contract, seed range, runtime, row-level outcomes, summary, and SHA-256 hashes. Keep this result distinct from M8's original seeds and from M5's prior task generator.
