# M2 2D closed-loop pursuit runner

`run_experiment.py` trains four recurrent estimators on exogenous 2D pursuit trajectories and evaluates them in aligned and reversed closed-loop sensor mappings. `analyze_results.py` computes paired policy contrasts and crossed-bootstrap intervals. `verify_results.py` checks row completeness, hashes, and all reported intervals.

```bash
python3 model/M2_2D_CLOSED_LOOP_PURSUIT_V1/run_experiment.py
python3 model/M2_2D_CLOSED_LOOP_PURSUIT_V1/analyze_results.py
python3 model/M2_2D_CLOSED_LOOP_PURSUIT_V1/verify_results.py
```

Use a fresh `--output-dir` for a reproduction. The runner refuses to overwrite nonempty results.
