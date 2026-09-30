# M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1 — model and verification

`run_experiment.py` translates the corrected Ji et al. Figure 7 update equations into a sign-reversing spatial gradient. It compares feedback at the sensory-processing state, feedback at the motor-output state, and no feedback. The source implementation and original MATLAB script are retained and hashed as inputs.

From the repository root:

```sh
python3 model/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/run_experiment.py
python3 model/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/analyze_results.py
python3 model/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/verify_results.py
```

Use `--output-dir` on the runner to write a separate run. The runner refuses to overwrite a non-empty directory. This is a source-model stress test; the output-only feedback arm is not calibrated to match persistence.

Regenerate the figure and figure-source data from the canonical run with:

```sh
python3 model/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/plot_results.py
```

The plotting script exports editable PDF/SVG and 600-dpi TIFF/PNG, records the two-panel alignment, and keeps the plotted aggregates in `figure_source_data.csv`.
