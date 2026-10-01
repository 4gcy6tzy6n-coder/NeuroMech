# M2 AIY premotor-state prediction V2 — analysis contract

**Classification:** outcome-informed exploratory follow-up to `M2_AIY_PREMOTOR_STATE_PREDICTION_V1`; same ten animals, not an independent cohort or confirmation.

## Why V2 exists

V1 required every future sample to have a known `+1/-1` state. Its primary horizon contained reversal examples in all five WT traces but none in the five RIM-ablated traces because source label `0` marks transition/unknown samples. That made the RIM-group prediction contrast unestimable. V1 is retained as a failed target-definition attempt.

V2 treats `0` as an interval-censored transition sample. At each forward-state forecast origin, the target is the first known (`+1` or `−1`) locomotor state in the next fixed horizon; intervening `0` samples are skipped. Origins with no known future state inside the horizon are omitted. This uses only source-coded state semantics; no neural outcomes are used to choose an event-specific horizon.

## Question and unit

Does current AIY activity add held-out information about the next known motor state beyond five recent motor-state samples, and does this increment differ descriptively between WT and RIM-ablated animals? AVA is the internal neural comparator. Animal is the unit; frames, folds, and transitions are repeated samples.

## Frozen analysis

At forward-state origins, behavioral-history predictors are current state and lagged states at 0.5, 1, 2, and 5 seconds. Compare blocked out-of-fold logistic models using history alone and history plus current AIY or AVA calcium. The primary horizon is 2 seconds; 0.5- and 5-second horizons are secondary descriptive analyses. Use ten contiguous folds per animal, training-fold-only standardization, `C=1.0`, and a 20-second exclusion around test blocks. Score pooled out-of-fold AUC only where both classes occur. Record each animal, prevalence, counts, and any unscorable result.

## Interpretation

This retrospective, post-result follow-up asks whether an observable AIY signal contains prospective information conditional on recent behavior. It cannot establish causal prediction, a unique RIM→AIY route, independent replication, or AI benefit. Small group sizes require animal-level descriptive uncertainty and prohibit frame-level inferential claims. Primary and secondary horizons remain separate; no horizon is selected after looking at the others.
