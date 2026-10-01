# Results — M2 premotor predictive-signal artificial transfer V1

**Classification:** post-result exploratory artificial transfer probe. The cue is synthetically generated to predict the target directly; it is not an observed AIY/AVA trace or a causal biological signal.

## Primary condition

At 128 training episodes and aligned cue reliability `q=0.72`, mean episode AUC was `0.7941` for the six-parameter forecast-fusion filter and `0.6876` for its same-parameter no-cue ablation. The paired seed-block contrast was `+0.1064` (95% seed-bootstrap interval `[+0.1024, +0.1103]`; 20/20 seed blocks positive). The cue also helped the larger generic GRU: `GRU_CUE − GRU_NO_CUE = +0.1886` (95% interval `[+0.1813,+0.1976]`). The cue-only reference reached `0.7192`.

The filter did not beat the 45-parameter, two-unit GRU receiving the same cue: `PREMOTOR_FILTER − GRU_CUE = −0.0709` (95% interval `[−0.0730,−0.0689]`; 0/20 blocks positive). A recipient-yoked cue reduced filter AUC by `0.1573` (95% interval `[0.1522,0.1621]`), showing that cue/episode correspondence mattered in this generator.

The effect depended on cue calibration. With `q=0.50`, the filter's cue gain over no-cue was `−0.0498`; under reversal (`q=0.28`) it was `−0.2291`. The generic GRU was more sensitive: its cue gain was `−0.1064` and `−0.4931`, respectively. Thus the small filter was less brittle to mismatch in this simulator, but it remained below its own no-cue baseline when the cue became misleading.

## Interpretation and failure lesson

This demonstrates utility of a stipulated predictive side channel and a robustness trade-off for one low-parameter update. It does not establish a distinctive biological computation or broad AI benefit. The main comparator had 45 rather than 6 parameters, so V1 could not attribute its aligned-condition loss to model structure. V2 adds a six-parameter generic recurrent control with paired initialization and batches. V1 is retained as its own completed result, not overwritten by that follow-up.

The run produced 161,280 episode rows and 240 model fits. The artifact verifier checked row/key completeness, parameter counts, output hashes, and all four primary contrast calculations; it did not independently retrain the models. See the V1 failure log and V2 results for the matched comparison.
