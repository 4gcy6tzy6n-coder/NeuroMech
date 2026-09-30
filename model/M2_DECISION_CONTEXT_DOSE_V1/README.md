# M2 decision context-dose runner

`run_experiment.py` trains state-gated, context-free, and bilinear recurrent estimators under full context/evidence alignment, then evaluates a frozen κ dose curve on terminal decisions. `analyze_results.py` computes paired accuracy effects and crossed-bootstrap intervals; `verify_results.py` checks output completeness, hashes, and primary estimates.

```bash
python3 model/M2_DECISION_CONTEXT_DOSE_V1/run_experiment.py
python3 model/M2_DECISION_CONTEXT_DOSE_V1/analyze_results.py
python3 model/M2_DECISION_CONTEXT_DOSE_V1/verify_results.py
```

Use a fresh `--output-dir` for reproduction; the runner refuses to overwrite nonempty results.
