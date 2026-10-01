# M5 interval-retuning source-data reproduction — results

**Classification:** exploratory reanalysis of an already published dataset and analysis. This is not independent biological validation and does not test an AI benefit.

## Acquisition

The Dryad v4 files were retrieved through their public individual-file links. Local SHA-256 values for `learning_1s_to_2s_GrC_CF.mat`, `learning_1s_to_2s_licking.mat`, and `README.md` exactly match the published values in the acquisition manifest. The MAT files are MATLAB v7.3/HDF5. No other files from the 16.64 GB release were downloaded.

## Reanalysis

The analysis follows the source script's three group labels, movement-aligned GrC activity, reward-delay definition, and eligible-reward filters. It uses every eligible reward trial instead of the original display subsampling. Each session contributes equally to the plotted group profile. The source-defined active-duration measure compares average activity during `[0, 2]` s after movement midpoint with the cell's baseline average during `[-1, 0]` s. The analysis does not treat cells as independent experimental units.

| Source group | Mean session-level median GrC active duration (s) | Mean session-level median activity centroid (s) | Mean reward delay (s) |
|---|---:|---:|---:|
| 1-s expert | 0.604 | 0.559 | 1.064 |
| 2-s novice / 1-s expert | 0.783 | 0.646 | 2.057 |
| 2-s expert | 1.335 | 0.950 | 2.057 |

These are descriptive averages of within-session cell medians, not estimates with cell-level confidence intervals. The intermediate 2-s novice group is variable across its ordered sessions: session medians of active duration were 0.167, 0.834, 0.951, 1.702, and 0.263 s. The last session also has a coarser imaging sampling step in the data, so the apparent non-monotonicity should not be interpreted as a clean learning trajectory. The 1-s expert and 2-s expert conditions are separate source groups; their contrast alone cannot establish within-animal causal retiming.

The descriptive direction is consistent with longer GrC activation in the 2-s expert group than the 1-s expert group. This recovers the broad published pattern but does not establish that the observed activity changes cause behavior, nor that the modeled CF-dependent LTD rule is the unique explanation. The author's synaptic weights are simulated from CF timing and GrC activity, not directly measured.

## Interpretation and next experiment

This source-data reproduction establishes the actual fields, time bases, and interval-related profiles needed to build a more biologically grounded AI test. The next AI study should use measured temporal profiles as an explicit candidate representation and compare them with matched generic temporal bases, shuffled profiles/events, a trained recurrent model, and exact replay/memory references on held-out timing tasks. The data reanalysis itself does not count as that AI test.

## Artifacts

- Source-data inventory: [`DATA_SCHEMA.md`](DATA_SCHEMA.md)
- Analysis contract: [`REPRODUCTION_CONTRACT.md`](REPRODUCTION_CONTRACT.md)
- Runner: [`reproduce_profiles.py`](../../model/M5_CEREBELLAR_INTERVAL_RETUNING_V1/reproduce_profiles.py)
- Figure generator: [`plot_profiles.py`](../../model/M5_CEREBELLAR_INTERVAL_RETUNING_V1/plot_profiles.py)
- Acquisition manifest: [`ACQUISITION_MANIFEST.json`](../../data/raw/cerebellar_interval_timing_dryad_v4/ACQUISITION_MANIFEST.json)
- Outputs: [`source_reproduction/`](../../data/results/M5_CEREBELLAR_INTERVAL_RETUNING_V1/source_reproduction/)
- Reproduce with Python 3.9+, NumPy, h5py, and Matplotlib: `python3 -m pip install --target /tmp/neuro-h5py h5py`; then run `PYTHONPATH=/tmp/neuro-h5py python3 model/M5_CEREBELLAR_INTERVAL_RETUNING_V1/reproduce_profiles.py` and `python3 model/M5_CEREBELLAR_INTERVAL_RETUNING_V1/plot_profiles.py` from the repository root.
