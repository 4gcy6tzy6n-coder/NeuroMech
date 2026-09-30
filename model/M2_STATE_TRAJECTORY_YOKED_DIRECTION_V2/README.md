# M2 state-trajectory yoke V2

Reproduce the archived run from the repository root with `python3 model/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/run_experiment.py`. The runner writes to `data/results/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/final/` and refuses to overwrite a nonempty directory. Audit the final rows, donor sequence lengths, seed-level estimate, and an independently reconstructed yoke trajectory with `python3 model/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/verify_results.py`.

This is a retrospective source-model follow-up, not a confirmatory experiment or biological validation. See the [contract, result, and failure record](../../summery/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/).
