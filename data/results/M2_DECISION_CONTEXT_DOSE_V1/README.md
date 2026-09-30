# M2_DECISION_CONTEXT_DOSE_V1 outputs

`canonical/episode_metrics.csv` contains 1,013,760 terminal-trial rows (30 seeds × 3 train sizes × 11 κ values × 256 test trials × 4 arms). `training_metrics.csv` records fit budgets and learned parameters. `per_seed_contrasts.csv` contains seed-level paired accuracy effects. `summary.json` includes the complete dose curve, crossed intervals, per-size estimates, and estimated crossover. `run_manifest.json` records versions, configuration, and hashes.

Reproduce from the repository root with the runner, analyzer and verifier under `model/M2_DECISION_CONTEXT_DOSE_V1/`; use a fresh output directory.
