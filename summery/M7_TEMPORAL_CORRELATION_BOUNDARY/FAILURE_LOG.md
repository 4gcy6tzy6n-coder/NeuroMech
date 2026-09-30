# M7 analysis and implementation lessons

- The first aggregation pooled accuracy differences and regression MSE differences. They have different units. The resulting pooled `+0.1124` interaction is invalid and is retained only for audit; do not cite it.
- Report classification and regression separately. Within each objective, paired seed resampling gives interpretable intervals.
- Delay stratification matters: the correlation interaction reverses at long delays in both objectives. A single average conceals that structure.
- Exact replay beats the local trace in all 48 objective × correlation × delay cells; this remains a constrained comparison against the current-input update, not an overall algorithm win.
- The task objective is still synthetic random-feature supervised learning. Do not call the correlation sweep general task-family transfer or biological validation.
