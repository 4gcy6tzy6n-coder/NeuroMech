# M2_CONTEXT_INFORMATION_DOSE_V1 outputs

`canonical/episode_metrics.csv` contains 422,400 held-out episode-level rows: 30 training seeds × 11 context doses × 256 shared test episodes × 5 policies. `learned_fits.csv` records all learned parameter vectors and fit endpoints. `seed_contrasts.csv` contains the paired primary contrast by training seed and dose. `summary.json` reports the dose curve and crossed-bootstrap intervals. `run_manifest.json` records runtime, configuration, and artifact hashes.

Reproduce from the repository root:

```bash
python3 model/M2_CONTEXT_INFORMATION_DOSE_V1/run_experiment.py --output-dir data/results/M2_CONTEXT_INFORMATION_DOSE_V1/reproduction
python3 model/M2_CONTEXT_INFORMATION_DOSE_V1/analyze_results.py --results-dir data/results/M2_CONTEXT_INFORMATION_DOSE_V1/reproduction
python3 model/M2_CONTEXT_INFORMATION_DOSE_V1/verify_results.py --results-dir data/results/M2_CONTEXT_INFORMATION_DOSE_V1/reproduction
```
