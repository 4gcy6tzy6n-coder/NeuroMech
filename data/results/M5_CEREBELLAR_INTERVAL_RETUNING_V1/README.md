# M5 cerebellar interval-retuning source-data reproduction

This folder contains the source-filtered, descriptive reanalysis of the Dryad v4 1-s-to-2-s GrC/CF file. The MATLAB input itself is locally available under `data/raw/cerebellar_interval_timing_dryad_v4/` and is intentionally excluded from Git because the source files total about 1.76 GB. `ACQUISITION_MANIFEST.json` records their official and local checksums.

The group summaries recover longer GrC active durations in the 2-s expert group than the 1-s expert group. The transitional group varies across sessions, and results are descriptive rather than animal-level inferential evidence. The analysis is a reimplementation of a published dataset analysis, not new biological validation or an AI transfer experiment.

See `summery/M5_CEREBELLAR_INTERVAL_RETUNING_V1/RESULTS.md` for the contract, values, limitations, and reproduction commands. Runners live in `model/M5_CEREBELLAR_INTERVAL_RETUNING_V1/`.
