# M2 context-information dose response runner

`run_experiment.py` trains the four small recurrent estimators on aligned (`κ=0.5`) data and evaluates them over the frozen context-information dose curve. `analyze_results.py` computes paired dose contrasts and crossed bootstrap intervals. `verify_results.py` independently checks row completeness, uniqueness, hashes, and all primary intervals.

Run from the repository root:

```bash
python3 model/M2_CONTEXT_INFORMATION_DOSE_V1/run_experiment.py
python3 model/M2_CONTEXT_INFORMATION_DOSE_V1/analyze_results.py
python3 model/M2_CONTEXT_INFORMATION_DOSE_V1/verify_results.py
```

The runner refuses to overwrite a nonempty output directory; use `--output-dir` for a fresh reproduction.
