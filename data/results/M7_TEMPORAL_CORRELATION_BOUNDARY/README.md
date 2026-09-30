# M7 result artifacts

`task_metrics.csv` is the authoritative episode/task-level output. `analysis_v1_objective_stratified.json` is the corrected inference, with classification and regression kept separate. `run_summary_v0_mixed_units_invalid.json` and `primary_seed_contrasts_v0_mixed_units_invalid.csv` preserve the initial pooled analysis; the pooled interaction mixes accuracy and MSE units and is invalid.

Rebuild the objective-stratified analysis with `python model/M7_TEMPORAL_CORRELATION_BOUNDARY/analyze_results.py`. The runnable experiment and analysis code are both stored under `model/M7_TEMPORAL_CORRELATION_BOUNDARY/`.
