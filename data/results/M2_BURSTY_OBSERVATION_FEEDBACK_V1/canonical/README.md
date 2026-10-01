# Canonical data — M2_BURSTY_OBSERVATION_FEEDBACK_V1

- `PREFLIGHT.json`: frozen contract/runner hashes and technical gradient preflight; no outcomes were computed during preflight.
- `episode_results.csv`: 46,080 paired episode-level outcomes across 24 training seeds, three visibility burst regimes, 128 held-out episodes, and five policies.
- `training_results.csv`: 120 fitted policies, with parameter counts, optimizer-update/token counts, final fit summaries, parameter states, and training time.
- `summary.json`: means, energy/recovery summaries, realized missingness, and the frozen primary paired crossed-bootstrap estimates.
- `RUN_METADATA.json`: execution and source pin metadata.
- `POSTRUN_VERIFICATION.json`: independent full-grid, pairing, parameter/update, source-hash, and primary-statistic verification.
- `REPRODUCIBILITY.json`: full fresh-directory rerun comparison.
- `figures/`: editable PDF/SVG, 600-dpi TIFF, source data note, panel-alignment and collision QA.

See [`CONTRACT.md`](../../../../summery/M2_BURSTY_OBSERVATION_FEEDBACK_V1/CONTRACT.md) for the frozen protocol and [`RESULTS.md`](../../../../summery/M2_BURSTY_OBSERVATION_FEEDBACK_V1/RESULTS.md) for interpretation and limits.
