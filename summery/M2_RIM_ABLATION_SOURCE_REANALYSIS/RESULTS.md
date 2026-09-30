# M2 Figure 6C source-data reanalysis

## Result

The released Figure 6C sheet contains 1,008 WT run events and 3,910 RIM-ablated run events with complete direction/duration pairs. The event-weighted median forward-run duration is 17.0 s for WT and 11.5 s after RIM ablation (difference −5.5 s); the means are 24.49 s and 16.63 s. The share of events lasting at least 30 s is 27.5% in WT and 11.9% after RIM ablation. These are descriptive, event-weighted values, not animal-level estimates.

In six equal-width direction bins spanning the source's radian range, the RIM-ablated event median was lower in all six bins. This descriptive consistency suggests that the pooled duration shift is not explained solely by a different mix across those coarse angle bins. The angle convention is retained as supplied; the bins are not relabeled as “up-gradient” or “down-gradient.”

## Biological interpretation

The released analysis is consistent with the paper's bounded claim that RIM ablation weakens sustained forward locomotion during positive thermotaxis. It does not by itself identify the causal synapse, separate changes in run initiation from termination, or quantify an animal-level effect. The computational abstraction remains: motor-state feedback can stabilize an ongoing action under fluctuating sensory input. That abstraction is supported by the authors' neural and intervention results; it is not an algorithm directly measured in the data.

## Data limitations

- The sheet has no worm/session ID, so no cluster bootstrap or valid animal-level uncertainty can be recovered from this export.
- Event counts differ substantially (3,910 vs 1,008). This may reflect the behavior under study and creates unequal event weighting; event count must not be treated as biological replicate count.
- The ≥30 s tail cut and direction bins are exploratory descriptive summaries.
- This reanalysis uses a single published figure-source sheet and does not reproduce the paper's full thermotaxis, neural-imaging, or stimulus-response analyses.

## Artifacts

- Runner: [`model/M2_RIM_ABLATION_SOURCE_REANALYSIS/analyze_fig6c.py`](../../../model/M2_RIM_ABLATION_SOURCE_REANALYSIS/analyze_fig6c.py)
- Reviewable notebook: [`model/M2_RIM_ABLATION_SOURCE_REANALYSIS/fig6c_reanalysis.ipynb`](../../../model/M2_RIM_ABLATION_SOURCE_REANALYSIS/fig6c_reanalysis.ipynb)
- Input workbook: [`data/raw/celegans/ji_etal_2021_elife_68848_v3/elife-68848-fig6-data1-v3.xlsx`](../../../data/raw/celegans/ji_etal_2021_elife_68848_v3/elife-68848-fig6-data1-v3.xlsx)
- Machine-readable results: [`data/results/M2_RIM_ABLATION_SOURCE_REANALYSIS/summary.json`](../../../data/results/M2_RIM_ABLATION_SOURCE_REANALYSIS/summary.json)
- Direction-bin summaries and figure: same results directory.
