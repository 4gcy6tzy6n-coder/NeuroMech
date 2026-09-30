# M2_2D_CLOSED_LOOP_PURSUIT_V1 outputs

`canonical/episode_metrics.csv` contains 76,800 unique rows (30 training seeds × 2 mappings × 256 target episodes × 5 estimators). `training_metrics.csv` records parameter counts, fitted parameters, losses, and fit time. `seed_contrasts.csv` contains seed-level paired effects. `summary.json` stores all policy means and crossed intervals; `run_manifest.json` stores runtime and hashes.

Reproduce from the repository root with the runner, analyzer, and verifier in `model/M2_2D_CLOSED_LOOP_PURSUIT_V1/`, using a fresh output directory.
