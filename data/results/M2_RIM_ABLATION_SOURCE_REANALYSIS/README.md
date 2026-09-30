# M2 Figure 6C source-data reanalysis outputs

- `summary.json`: validated source provenance, event-weighted summaries, contrasts, and inference boundary.
- `direction_bin_descriptives.csv`: 12-bin directional medians, quartiles, event counts, and long-run fractions by group.
- `figure6c_event_level_descriptive.png`: event-level median-duration and event-count plots; no uncertainty bars because worm IDs are absent.
- `run_manifest.json`: code, runtime, and output hashes.
- Source workbook: `data/raw/celegans/ji_etal_2021_elife_68848_v3/elife-68848-fig6-data1-v3.xlsx` (Figure 6C, version 3).

Re-run with `python model/M2_RIM_ABLATION_SOURCE_REANALYSIS/analyze_fig6c.py` from the repository root. The script writes only the derived files in this directory.

The source workbook is redistributed from the eLife article's Figure 6 source data under the article's Creative Commons Attribution License. Citation: Ji et al. (2021), DOI `10.7554/eLife.68848`; source-data page: https://elifesciences.org/articles/68848v2/figures.
