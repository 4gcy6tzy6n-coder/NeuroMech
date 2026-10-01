# M5 source-defined CF-LTD transfer V2 — contract

**Classification:** post-result exploratory artificial transfer. The prior M5 synthetic transfer and the held-out biological source-data readout are known. This is not confirmatory and cannot establish biological causality.

## Question

Does the source-defined reward-timed climbing-fiber (CF) to granule-cell (GrC) LTD operation produce a useful temporal readout on independently generated reward episodes when applied to measured GrC temporal profiles?

## Frozen task and representation

Use the existing source-filtered Dryad v4 cell-level GrC temporal-profile extractor from the 1-s expert and 2-s expert groups. It yields 32 cells per group on an 81-bin `0–2.4 s` grid. Profiles are cell averages, not single-trial network activity. Add the same realization of Gaussian observation noise (`SD=0.025`) to every compared feature basis in each episode.

Each episode has one of two cues. In the aligned condition, cue 0 maps to `0.9 s` and cue 1 to `1.8 s`; in the reversed condition these assignments swap. Add independent uniform timing jitter in `[-0.15,+0.15] s`. Use 1,800 training and 500 test episodes per mapping for each of 12 task seeds (`6100–6111`). Training and test task draws are independent; all model arms receive paired episodes and noise.

## Source-defined learning operation

For each cue-specific output, model one binary CF teaching event at the target reward time in every training episode. A CF event marks GrC activity at the source's inclusive frame offsets corresponding to `[-0.15,-0.025] s` before that event. Fit the per-cell 95th-percentile activity scale using training episodes only, rectify GrC activity at zero, apply the source logistic transform, replace noneligible samples by `sigmoid(0)=0.5`, average over training episodes and time, center across GrCs, normalize by the uncentered sum, and apply the source negative sign. Decode a test episode using the minimum of its cue-specific weighted population signal; this represents the greatest learned LTD-associated suppression. No test target enters the fitted weights.

## Comparison arms

1. `BIO_CF_LTD`: biological profiles with the source `[-0.15,-0.025] s` CF eligibility window.
2. `BIO_NO_TRACE`: identical source transform and update, with eligibility restricted to the CF-event frame.
3. `BIO_CF_TIME_SHUFFLED`: identical rule but permute teaching-event times across training episodes within each cue.
4. `BIO_CELL_SHUFFLED`: permute the fitted LTD weight vector across GrC identities.
5. `GENERIC_RBF_CF_LTD`: 64-unit evenly spaced RBF temporal basis, with the same local source rule.
6. `SHUFFLED_BIO_CF_LTD`: independently permute each biological feature's temporal order before fitting and testing, preserving its marginal values.
7. `UNIFORM_POOL`: equal negative weights over the biological profiles; no learned cell-specific LTD weights.
8. `EMPIRICAL_TIMER`: cue-specific training-label mean reward time; a strong explicit-time reference, not a capacity-matched network.

## Primary outcome and decision rule

Primary outcome: per-episode absolute reward-time error in seconds, averaged first within task seed. The aligned mapping is primary; reversed mapping is a boundary diagnostic. Compute paired 95% bootstrap intervals over the 12 task-seed means (`20,000` resamples, seed `20261014`).

Evidence that the source-defined LTD operation adds an artificial temporal inductive bias requires `BIO_CF_LTD` to improve over both `BIO_NO_TRACE` and `BIO_CF_TIME_SHUFFLED` (paired 95% interval for control minus primary wholly above zero) and not lose to `GENERIC_RBF_CF_LTD`. A result only against one weak control does not establish source-mechanism specificity. The empirical timer is reported as an attainable task reference, not a biological or capacity-matched comparator.

## Interpretation boundary and reproducibility

Any positive result is limited to this artificial task, representation, and local source-derived update. It does not verify synaptic LTD in vivo or show general AI benefit. A null or adverse result is retained as a failed transfer of this implementation. The runner records raw input, contract, code, and output hashes, environment, seeds, and paired episode outcomes. It refuses to overwrite existing results. No hyperparameter selection is performed.
