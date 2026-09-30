# M4 CA3-Inspired Partial-Cue Benchmark — Exploratory Results

**Classification:** post-result, exploratory artificial benchmark. It is not a biological result, not confirmation of CA3 recurrence, and not a confirmatory AI-transfer study.

## Main result (v2 method-correction follow-up)

The benchmark compared a Hebbian recurrent Hopfield network with exact nearest-exemplar/MAP retrieval on identical generated memories and cues: `N=120`, four memory loads (`P/N=0.05–0.20`), five visible-cue fractions (`0.2–1.0`), three bit-flip rates (`0–0.2`), 25 independent memory-set seeds, and 10 queries per seed/condition. This produced 30,000 method-level rows and 60 condition summaries.

| Measure | Hebbian recurrent | Exact exemplar/MAP |
|---|---:|---:|
| Exact target recall, pooled over frozen grid | 0.5592 | 0.9919 |
| Mean bit accuracy | 0.8927 | 0.9961 |

The paired exact-recall difference (recurrent minus MAP), aggregated within seed across the grid, was `-0.4327`; seed-cluster bootstrap 95% interval `[-0.4481, -0.4172]`. For the 60 individual condition contrasts, 51 unadjusted seed-cluster 95% intervals were below zero, nine included zero, and none were above zero. These cellwise intervals are descriptive and not corrected for multiplicity.

The largest degradation occurred as memory load increased. At the highest load (`P/N=0.20`) averaged across cue conditions, recurrent exact recall was 0.0843 versus 0.9869 for MAP. At the lowest load (`P/N=0.05`), the rates were 0.9619 versus 0.9963. When all cues were visible and uncorrupted, both methods recalled perfectly at the lowest load; the recurrent rate fell to 0.724 at load 0.15 and 0.284 at load 0.20.

The recurrent dynamics reached a fixed point in all queries, after a mean 3.97 sweeps. Its output was not one of the stored memories in 0.4379 of queries. This is a purely operational output-validity measure; it does not identify biological attractors.

## Method correction and provenance

The first attempted run used random hidden-state initialization despite the written v1 contract specifying zero initialization. Its output was retained under `results_v0_random_initialization_deviation/` and is not treated as contract-conforming evidence. A second v1 run implemented zero initialization but clamped observed bits. Inspection then showed that clamping makes correction of flipped observed cues impossible. That run is retained under `results_contract_conformance_followup/` as the original clamped-cue benchmark.

The v2 follow-up removes clamping so recurrent dynamics can update noisy and observed units. Because this method correction followed inspection of v1 outputs, v2 is explicitly post-result and exploratory. Its frozen protocol and implementation are `EXPLORATORY_BENCHMARK_CONTRACT.md` and `run_benchmark.py`; v1 is retained in `EXPLORATORY_BENCHMARK_CONTRACT_v1.md`. No v1 output was overwritten.

## Interpretation

The classic Hebbian implementation did not beat exact exemplar/MAP retrieval on this synthetic task. The MAP decoder is the optimal target selector under the stated uniform memory prior and symmetric independent bit-flip model, so it serves as a ceiling/diagnostic comparator rather than a capacity-matched engineering baseline. The resource costs were not matched: storing 6–24 explicit patterns requires 720–2,880 bits in this simplified accounting, while a dense 120×120 float32 weight matrix uses 460,800 bits. Thus these results do not establish a useful compression or compute tradeoff either.

This rejects only the tested classic dense Hebbian implementation as an AI advantage on this task and cost accounting. It does not refute the biological observation of partial-cue recall, decide between the conflicting biological studies, or establish that CA3 recurrent collaterals are the unique substrate. Follow-up architecture changes require a new explicitly post-result experiment and stronger resource-matched baselines.

## Reproducibility artifacts

- `EXPLORATORY_BENCHMARK_CONTRACT.md` — v2 follow-up protocol and post-result rationale.
- `EXPLORATORY_BENCHMARK_CONTRACT_v1.md` — original clamped-cue protocol retained as executed.
- `run_benchmark.py` — deterministic benchmark implementation.
- `results_v2_unclamped_method_correction/trial_results.csv` — all paired trial outputs.
- `results_v2_unclamped_method_correction/summary.json` — all 60 condition summaries and bootstrap intervals.
- `results_v0_random_initialization_deviation/` — first run retained with its implementation deviation.
- `results_contract_conformance_followup/` — v1 zero-initialized, clamped-cue run retained separately.
- `SHA256SUMS.txt` — digests of the v1/v2 contracts, implementation, and v2 outputs.
