# Model and analysis code

`run_experiment.py` trains the four learned estimators under paired random-action and teacher-mixed closed-loop training regimes, then evaluates them on shared held-out targets under aligned and reversed mappings. `analyze_results.py` computes the preregistered crossed-bootstrap interaction and supporting contrasts. `verify_results.py` independently checks row coverage, hashes, and all reported intervals.

Run from the repository root:

```sh
python3 model/M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/run_experiment.py
python3 model/M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/analyze_results.py
python3 model/M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC/verify_results.py
```

The runner refuses to overwrite a non-empty output directory. Pass `--output-dir` to retain reruns separately. See the experiment contract for exact stream and interpretation rules.
