# M2 motor-feedback sparse-sensation tracking V1

This folder contains the three-parameter sensory-site, output-site, no-feedback, and one-state generic recurrent policies; the closed-loop experiment runner; a result analyzer; an independent verifier; and a plotting script.

From the repository root, reproduce canonical outputs in a fresh output directory:

```bash
python3 model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/run_experiment.py \
  --preflight --output-dir /tmp/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1_RERUN
python3 model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/run_experiment.py \
  --output-dir /tmp/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1_RERUN
python3 model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/analyze_results.py \
  --results-dir /tmp/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1_RERUN
python3 model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/verify_results.py \
  --results-dir /tmp/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1_RERUN
```

The runner requires NumPy and PyTorch. The figure renderer additionally uses Matplotlib; rerunning its Nature-style alignment and PDF audits requires the corresponding local figure-audit scripts. Canonical raw episode rows and the published figure bundle are in `data/results/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/`.
