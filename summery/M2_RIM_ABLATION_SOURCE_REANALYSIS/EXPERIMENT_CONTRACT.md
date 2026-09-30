# Figure 6C source-data reanalysis: RIM ablation and forward-run persistence

**Status:** completed, post-publication exploratory reanalysis of the released source observations. This is not a new animal experiment and does not revise the original paper's inferential analysis.

## Question

In the released Figure 6C run-direction/run-duration observations, is the event-level forward-run duration distribution lower after RIM ablation, including within coarse bins of run direction?

## Source and unit

- Primary source: Ji et al., *eLife* 2021, 10:e68848, Figure 6C source data, version 3.
- Input workbook: `data/raw/celegans/ji_etal_2021_elife_68848_v3/elife-68848-fig6-data1-v3.xlsx`, sheet `Fig 6C`.
- Fields: run direction (radian) and run duration (seconds), in side-by-side WT and RIM-ablated columns.
- The workbook does not provide a worm/session key for these run events. The analysis unit is therefore a released run event for descriptive summaries only. It is not a valid animal-level inferential sample.

## Registered calculations for this reanalysis

1. Validate paired direction/duration values, finite values, and positive run durations.
2. Report event-weighted mean, median, quartiles, and tail fractions for each group.
3. Plot direction-binned medians and event counts with 12 equal bins over the source's radian range.
4. Report a six-bin coarse direction summary as descriptive context.
5. Do not compute p-values, confidence intervals, animal-level sample sizes, or animal-level effects. Do not infer animal IDs from row order.

The 30 s tail threshold and angular binning are descriptive choices introduced after the published results were known. They do not constitute a confirmatory test.

## Interpretation limit

The source paper reports that RIM ablation reduces the ability to sustain forward runs during positive thermotaxis. This analysis checks the released event table's descriptive shape and directional consistency. Because events are nested in animals and animal identifiers are absent, pooled event contrasts weight animals by the number of runs they contribute and cannot independently establish a population-level effect.
