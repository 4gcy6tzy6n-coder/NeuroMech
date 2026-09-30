# M5 eligibility trace memory frontier V1 — results

**Classification:** post-result exploratory artificial benchmark on fresh task seeds. The task family and algorithm choices followed earlier M5/M8 outcomes. This is not confirmatory evidence, biological validation, or an NMI-level generalization result.

## Primary result

The eligibility trace exceeded the immediate-feature `HORIZON_1` update by **+0.21914** held-out accuracy averaged equally over nine autocorrelation × delay conditions (paired task-seed bootstrap 95% interval **[+0.20941, +0.22867]**; **30/30** fresh task seeds positive). The average gain was +0.18696 at delay 4, +0.28906 at delay 16, and +0.18142 at delay 64. All three rho-stratified intervals were positive, including the smallest average gain at rho=0.9 (+0.12698, interval [+0.11742, +0.13673]).

## Accuracy and active feature-history state

| Arm | Mean accuracy across 9 rho × delay cells | Active feature-history values per arm |
|---|---:|---:|
| HORIZON_1 | 0.3281 | 0 |
| HORIZON_2 | 0.3380 | 128 |
| HORIZON_4 | 0.3677 | 256 |
| HORIZON_8 | 0.4350 | 512 |
| HORIZON_16 | 0.4672 | 1,024 |
| HORIZON_32 | 0.5181 | 2,048 |
| HORIZON_64 | 0.5215 | 4,096 |
| ELIGIBILITY_TRACE | **0.5473** | **64** |
| EXACT_REPLAY | 0.7480 | 256 / 1,024 / 4,096 at D=4 / 16 / 64 (mean 1,792 across delays) |

Under this task generator and state-counting convention, the eligibility trace had higher average accuracy than every fixed-window horizon while retaining fewer active feature values than any horizon except HORIZON_1. Exact replay remained substantially more accurate and used delay-dependent history storage.

## Condition dependence

The pooled frontier hides meaningful interactions. At delay 4, horizon 8 exceeded the trace in all three rho cells (for example, at rho=0.0: 0.702 versus 0.597). At delay 16, longer finite windows often did better than the trace. At delay 64, the trace exceeded HORIZON_64 in all three rho cells (0.382 vs 0.254 at rho=0.0; 0.410 vs 0.307 at rho=0.5; 0.470 vs 0.387 at rho=0.9). Exact replay remained highest in every cell. Cell-level values are descriptive; they were not multiplicity-adjusted.

This pattern is consistent with a compact decaying state being useful when the relevant history is long, while task-specific finite windows can perform better at shorter delays. It does not establish a universal trace advantage or that `gamma=0.98` is biologically measured. The climbing-fiber teaching event is causally supported in delay eyeblink learning; the eligibility-trace equation remains a computational abstraction rather than a directly observed synaptic state. No biological data were analyzed here.

## Limits and provenance

The experiment used task seeds 30–59, disjoint from M8's seeds 0–29, but it reuses the same task generator and fixed gamma/learning rate family after prior outcomes were known. These fresh tasks make the paired comparison new at the instance level, not confirmatory at the hypothesis/design level. The state metric counts logical stored feature values, not actual RAM, runtime, compute, or energy. Model weights and per-arm delayed prediction histories are common requirements and excluded. The task is synthetic random-feature classification only.

The Python 3.9.6 / NumPy 2.0.2 run emitted matrix-operation warnings but saved finite scores. A full Python 3.12.13 / NumPy 2.4.4 rerun emitted no such warnings and reproduced the complete row-level accuracy CSV byte-for-byte (2,430 rows; maximum score difference 0). The Python 3.12 run is canonical. See `FAILURE_LOG.md` and `data/results/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/`.

## Reproduction

Run `python3.12 model/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/run_experiment.py` from the repository root. Audit results with `python3.12 model/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/verify_results.py`. The runner refuses to overwrite a nonempty output directory.
