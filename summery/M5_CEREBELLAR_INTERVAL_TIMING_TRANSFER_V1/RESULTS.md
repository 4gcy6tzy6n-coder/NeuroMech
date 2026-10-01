# M5 cerebellar interval timing transfer V1 — results

**Classification:** retrospective, post-result exploratory artificial experiment. It is not independent biological validation, a confirmatory preregistration, or evidence of general AI benefit.

## Question and setup

We tested whether cell-level temporal profiles extracted from the source-filtered 1-s and 2-s expert GrC data can support timed reward prediction in an independent synthetic task. The extractor found 732 usable normalized cell profiles across the two source groups; 32 from each group were selected deterministically to form a 64-channel basis. Synthetic cues and reward times were generated independently. Twelve paired task seeds each had 1,800 training and 500 test episodes for aligned and reversed cue-to-interval mappings. The primary score is absolute reward-time error, first averaged over test episodes within each task seed.

## Results

| Arm | Aligned MAE (s) | Task-seed bootstrap 95% interval (s) | Interpretation |
|---|---:|---:|---|
| Biological profiles + eligibility update | 0.836 | [0.826, 0.845] | Poor timing decoder |
| Biological profiles + no-trace update | 0.837 | [0.827, 0.847] | Indistinguishable from eligibility arm |
| Generic 64-unit RBF basis + eligibility | 0.140 | [0.138, 0.143] | Stronger than the biological linear readout |
| Time-shuffled biological profiles + eligibility | 0.512 | [0.508, 0.515] | Temporal-order destruction degrades performance, but remains better than the unshuffled linear decoder |
| GRU with biological-profile input | 0.096 | [0.092, 0.101] | Close to the timer reference |
| GRU with constant clock input and cue only | 0.118 | [0.080, 0.190] | Generic recurrent step counting is already strong; high seed variability |
| Empirical cue-specific timer | 0.075 | [0.075, 0.076] | Estimated from training labels; near the expected 75-ms mean absolute jitter |

The primary contrast (biological-profile eligibility minus biological-profile no-trace) was `−0.00091 s` (paired 95% task-seed interval `[−0.00276, +0.00086]`; 3/12 seeds favored eligibility). There is no evidence of an eligibility benefit in this setup. Biological-profile eligibility was `+0.695 s` worse than the generic RBF arm (paired interval `[+0.684, +0.706]`; 12/12 seeds) and `+0.740 s` worse than the profile-input GRU (`[+0.730, +0.749]`; 12/12).

Adding biological profile input to the GRU changed mean aligned error by `−0.022 s` relative to the constant-input GRU, but its paired interval crossed zero (`[−0.097, +0.020]`) and 9/12 seed means were in the opposite direction. Under reversed mapping the mean was `−0.040 s` with interval `[−0.120, +0.006]` and 5/12 seed means favored the profile-input GRU. Thus the apparent profile-input gain is not stable evidence that the biological traces add value beyond a generic recurrent clock.

The reversed mapping gave the same qualitative ordering: biological-profile eligibility MAE `0.841 s`, no-trace `0.841 s`, generic RBF `0.141 s`, profile-input GRU `0.094 s`, clock-only GRU `0.134 s`, and empirical timer `0.075 s`.

## Interpretation and failure analysis

This transfer attempt **does not support** the claim that these measured GrC profiles plus a local eligibility update improve AI interval timing. The biological linear readout is badly calibrated toward late times, the trace update does not improve it over the direct local update, and generic temporal bases and recurrent models perform much better. The profile-input GRU's small mean advantage over a constant-input GRU is uncertain and seed-sensitive.

The task is an artificial interval-prediction probe, not a cerebellar circuit simulation. The selected traces are source-group cell averages after source-defined reward filters; they are not raw single-trial dynamics, directly measured synaptic weights, or independent biological replicates. Source group labels informed which traces were sampled, and the task intervals were chosen to reflect those groups. This is therefore a post-result exploratory transfer with a possible source-to-task alignment advantage. The empirical timer uses training target means and is a strong reference, not a biological model.

The result does not prove that the biological mechanism is ineffective in AI. It shows that this specific fixed 64-profile representation and this local reward-error update fail against the tested controls on this particular event-timing task. A valid next attempt must first diagnose whether the mismatch comes from the representation, the simplified eligibility rule, or the task abstraction; it must preserve the negative result and avoid treating the uncertain GRU comparison as a win.

## Preliminary pilot provenance

An initial run without the constant-input GRU control was archived under `data/results/M5_CEREBELLAR_INTERVAL_TIMING_TRANSFER_V1/pilot_pre_clock_control/`. Its task outcomes were finite but it lacked the clock control needed to distinguish profile use from generic recurrent counting. The final comparison reran all arms on the same paired seeds and episodes after adding that control. Do not use the pilot as the final interpretation.

## Reproduction artifacts

- [Contract](CONTRACT.md)
- [Runner and paired follow-up analysis](../../model/M5_CEREBELLAR_INTERVAL_TIMING_TRANSFER_V1/)
- [Episode-level outcomes, selected biological traces, checksums and manifests](../../data/results/M5_CEREBELLAR_INTERVAL_TIMING_TRANSFER_V1/)
- Primary biological source: [Garcia-Garcia et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11343686/)
- Data source: [Dryad v4](https://datadryad.org/dataset/doi%3A10.5061%2Fdryad.bk3j9kdm6)
