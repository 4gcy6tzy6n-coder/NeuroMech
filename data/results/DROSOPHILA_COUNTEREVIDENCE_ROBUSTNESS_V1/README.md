# DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1

Reduced-order synthetic AI-side cue-sufficiency test for stationary-pattern counterevidence in self-rotation estimation. This is not biological data or a natural-vision benchmark.

- `episode_predictions.csv`: per-example held-out predictions for four model/control arms.
- `seed_block_metrics.csv`: metrics aggregated at the independent environment-seed-block level.
- `summary.json`: primary paired contrast, profile-specific results, ablation, design, and interpretation boundary.
- `run_manifest.json`: source pins, runtime, hashes, and numerical checks.
- `counterevidence_coverage_shift.png`: held-out patterned-static profile accuracy by model and coverage.
- `SHA256SUMS.txt`: package integrity hashes.

Reproduce from repository root with:

```sh
python3 -W error model/DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1/run_experiment.py
```

The task deliberately places the class-discriminative cue in the stationary textured feature. Its near-perfect result is a manipulation check, not evidence that this architecture outperforms a general vision model.
