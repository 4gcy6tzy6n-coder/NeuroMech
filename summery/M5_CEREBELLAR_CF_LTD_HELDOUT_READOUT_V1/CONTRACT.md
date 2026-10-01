# M5 CF-taught GrC readout on held-out trials — V1 contract

**Classification:** post-result exploratory reanalysis. Prior M5 source and artificial results are known. This is not an independent replication or confirmatory preregistration.

## Question

Does a source-faithful estimate of reward-evoked climbing-fiber (CF) gated GrC→Purkinje-cell long-term depression (LTD), fit on training trials, produce a time-progress readout on held-out trials better than uniform weights, cell-shuffled LTD weights, or LTD weights computed after within-cell time permutation?

## Source-defined computation

Follow Garcia-Garcia et al. author code `GrC_CF_main_Part4.m` at commit `124c83e1af83e9680e05f9827448579d02345fa3`:

- Training trials: `rewarded & (mvlen > 7) & goodmvdir`.
- Candidate CFs: source reward-aligned spiking increase in `[0, 0.25] s` over baseline `[-0.3, -0.025] s`, estimated from training trials only.
- CF teaching events: detected binary `sp_CF` events in `[0, 0.25] s` after reward.
- GrC eligibility window: `[-0.15, -0.025] s` before each CF spike. The source uses rounded frame offsets and an inclusive window.
- For eligible GrC samples, rectify activity at zero, scale by the cell's 95th percentile of training-trial GrC activity, apply the source logistic transform, average over training trials/time for each CF, center and normalize across GrCs within each CF, average across selected CFs, then apply the source negative sign to obtain readout weights.

The source assumes every GrC contacts every selected Purkinje cell and predicts plasticity from calcium/spike data. The resulting weights are modeled proxies, not measured synaptic strengths.

## Held-out evaluation

Include all sessions in the three released groups: `1-s expert`, `2-s novice / 1-s expert`, and `2-s expert`. Eligible trials are the author-defined rewarded, `mvlen > 7`, `goodmvdir` trials. Within each session, use five deterministic random 50/50 trial splits; the seed is `20261001 + group_index*100000 + session_index*1000 + split_index` (indices start at zero). Fit CF selection, p95 activity scales, and LTD weights on training trials only. Apply those frozen weights to held-out `midAlgn` activity from movement midpoint through the recorded reward delay, capped at 2 s. Per trial, compute Pearson correlation between readout and elapsed time, then square it to match the source analysis's direction-insensitive `r²` convention. The ridge reference is standardized on training features, uses fixed `alpha=1.0`, and is descriptive only. Summarize split outcomes within session; sessions, not cells or time bins, are the descriptive units. Because animal identity linkage is not established here, do not compute animal-level inferential claims or treat sessions as independent animals.

## Comparators

1. Source CF-LTD weights, training trials only.
2. Uniform positive weights.
3. Source LTD weight values randomly permuted across GrC identities.
4. Source LTD rule after each training trial's GrC time series is independently permuted within each cell, preserving per-cell activity values while breaking CF/time alignment.
5. An unoptimized, training-label ridge readout as a descriptive decodability reference, not a capacity-matched comparator.

## Interpretation

Evidence for the source-derived computation requires held-out time-tracking `r²` to be descriptively higher for actual CF-timed LTD weights than both uniform and CF-time-permuted controls across source groups. A win only against the cell-shuffled control is insufficient. Results are descriptive at the session level and cannot establish causality, true synaptic plasticity, population generalization, or an AI benefit.

## Reproducibility

The raw Dryad v4 file is SHA-256 pinned in the acquisition manifest. The runner records its own hash, source-code commit, all split seeds, output checksums, source group/session identifiers, and cell-level modeled readout weights. The runner refuses to overwrite existing results.
