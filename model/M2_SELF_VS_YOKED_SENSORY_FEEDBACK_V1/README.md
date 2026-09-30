# M2 self-contingent versus yoked sensory feedback V1

Run from the repository root:

```bash
python3 model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/run_experiment.py
python3 model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/analyze_results.py
python3 model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/verify_results.py
python3 model/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/plot_results.py
```

The runner refuses to overwrite a non-empty output directory. Pass `--output-dir` to use a new destination. The experiment contract is in [`summery/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/CONTRACT.md`](../../summery/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/CONTRACT.md). Analysis, yoke marginal checks, canonical outputs, and limitations are documented in the corresponding `summery/` and `data/results/` folders.

This is a retrospective exploratory simulation of the corrected Ji et al. source-derived equations. It is not biological validation or an AI transfer experiment.
