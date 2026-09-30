# Model and analysis code

`run_experiment.py` trains three parameter-matched feedback-placement/ablation models and a two-unit generic RNN on shared sequences, then evaluates them alongside an exact Bayes filter at three state-switch hazards. `analyze_results.py` computes the primary paired crossed-bootstrap contrast and supporting summaries. `verify_results.py` independently validates row coverage, source/output hashes, and the primary interval.

From the repository root:

```sh
python3 model/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/run_experiment.py
python3 model/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/analyze_results.py
python3 model/M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1/verify_results.py
```

The runner refuses to overwrite a non-empty output directory. Pass `--output-dir` to keep reruns separately. See the contract for task, model, and inference definitions.
