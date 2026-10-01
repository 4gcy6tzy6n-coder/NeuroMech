# M2 AIY premotor-state prediction V1 — analysis contract

**Classification:** retrospective, outcome-informed exploratory reanalysis of the same public Ji et al. source cohort used in `M2_AIY_STATE_CONDITIONAL_ENCODING_V1`. It is neither an independent cohort nor confirmatory evidence.

## Question

Does current AIY calcium add held-out information about an impending forward-to-reversal transition beyond a short recent motor-state history, and is that increment lower after RIM ablation? AVA is the internal neural comparator.

The analysis is deliberately a prediction test. A positive result would not show that AIY causes the transition or that RIM is the unique route. The existing source paper provides the biological context; this analysis tests whether the public traces contain a candidate forward-looking signal.

## Source and unit

Use the five complete WT and five RIM-ablated constant-temperature traces already mapped in `model/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/analyze_source_data.py`. Preserve animal as the biological unit. Samples, events, and folds are repeated observations within animal.

## Frozen target and predictors

At sample `t`, include only times when current and five prespecified history samples (`t`, `t−0.5`, `t−1`, `t−2`, `t−5` seconds) are labeled forward (`+1`) or reversal (`−1`), and all samples in the prediction horizon are labeled (no transition/unknown `0`). The binary target is whether any reversal state occurs in the next horizon. The primary horizon is 2 seconds; 0.5- and 5-second horizons are secondary descriptive analyses.

Compare blocked out-of-fold logistic models using (a) the five recent motor-state samples alone and (b) the same motor history plus the current neural signal (AIY primary; AVA comparator). Primary per-animal estimand is `AUC(history + AIY) − AUC(history)`. Current calcium is not lag-scanned or selected by outcome. Fit scaling and coefficients within training folds only.

Use ten contiguous folds per animal and exclude training samples within 20 seconds of each test block, covering the 5-second history and 5-second maximum forecast horizon with a buffer. Score only pooled out-of-fold predictions. Require both target classes in pooled scored samples; retain counts and report insufficient animals rather than dropping them silently.

## Reporting

Report each animal's event prevalence, positive/negative sample count, OOF count, baseline AUC, augmented AUC, and increment. Summarize WT and RIM-ablated animals separately. Report animal-bootstrap intervals and exact 5/5 group-label permutation references as descriptive only. Do not treat frames, events, or folds as independent units. The two secondary horizons and AVA comparisons are exploratory and are not used to rescue a null primary result.

## Interpretation boundary

The existing small cohort, repeated measurements, retrospective analysis, and prior inspection of related state-decoding results make this exploratory. A positive increment is predictive information conditional on the specified history, not a causal or unique AIY mechanism. A null increment bounds this dataset and model family; it does not prove absence of prospective neural information. No AI-transfer benefit is tested here.
