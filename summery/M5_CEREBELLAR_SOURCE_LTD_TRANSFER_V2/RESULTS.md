# M5 source-defined CF-LTD transfer V2 — results

**Classification:** post-result exploratory artificial transfer. The frozen transfer criterion was not met. This result is about this implementation and task generator, not a biological mechanism verdict.

## Results

The source-defined CF-LTD rule did not improve reward-time prediction on the frozen synthetic task. Across 12 paired task seeds and 500 held-out episodes per seed/mapping, its aligned mean absolute error (MAE) was `0.1252 s`. The immediate, no-trace update was better (`0.1097 s`); the CF-time-shuffled control was essentially identical (`0.1252 s`); and generic 64-unit RBF features with the same local LTD rule were better (`0.1030 s`). The training-label timer achieved `0.0753 s`.

| Arm | Aligned MAE (s) | Paired 95% interval for `arm − CF-LTD` (s) | Reversed MAE (s) |
|---|---:|---:|---:|
| Biological profiles + source CF-LTD | 0.1252 | reference | 0.1254 |
| Biological profiles + instant/no-trace update | 0.1097 | [−0.0190, −0.0119] | 0.1087 |
| Biological profiles + CF-time-shuffled LTD | 0.1252 | [−0.00002, +0.00003] | 0.1254 |
| Biological profiles + cell-shuffled LTD weights | 0.8762 | [+0.5452, +0.9427] | 0.8743 |
| Generic RBF + source CF-LTD | 0.1030 | [−0.0229, −0.0216] | 0.1037 |
| Time-shuffled biological profiles + source CF-LTD | 0.1588 | [+0.0289, +0.0379] | 0.1581 |
| Uniform population pool | 0.7214 | [+0.5880, +0.6043] | 0.7152 |
| Training-label empirical timer | 0.0753 | [−0.0522, −0.0479] | 0.0752 |

Intervals are paired bootstrap intervals over task-seed means (`20,000` resamples), not over episodes. The reversed mapping gives the same ordering. The rule fails the prewritten requirement to beat both no-trace and CF-time-shuffled controls and to avoid losing to the generic RBF basis.

## Interpretation and task limitation

This experiment does **not** support an AI benefit from the source-defined CF-LTD rule. It does show that the particular biological temporal profiles contain useful time structure relative to time-shuffled profiles, but generic RBF features decode the task better, and the source CF eligibility window loses to an immediate update.

Post-run design audit identified a central limitation in the generator: every episode used the same deterministic temporal profiles for its cue, with independent additive noise; the `±0.15 s` reward-time jitter was sampled independently of those features. Consequently, there is no trial-specific neural information about the jitter to learn. The cue identifies only the interval center, and the empirical timer's `0.0753 s` MAE is approximately the irreducible median-prediction error for uniform `±0.15 s` jitter. Shuffling teaching-event times across episodes within a cue preserves the same event-time distribution, so the primary and CF-time-shuffled weight vectors are nearly identical. This makes the frozen task a poor discriminator of event-specific temporal credit, even though it can compare static readout rules.

The appropriate conclusion is therefore bounded: **the CF-timed LTD implementation failed to add value on this synthetic task, and this task did not carry a trial-specific signal needed to establish whether the biological timing rule can exploit such information.** This is not evidence that cerebellar plasticity is ineffective in vivo or that the computation cannot transfer under a better-matched input process.

## Failure experience and reproducibility

The contract was committed before the first outcome run (`05d2fde`). The runner executed all 12 seeds without `RuntimeWarning`. The independent verifier checks the raw Dryad hash, contract and runner hashes, all output hashes, 96,000 finite episode results, and exact pairing of all eight arms on each of 12,000 episode/mapping/seed records.

The central design lesson is to make episode-specific input dynamics carry information about the timing target before testing a timing-credit mechanism. A follow-up must be a separately identified experiment with a new contract; it must preserve this negative transfer result and may not present a changed generator as a repair or replication.

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and verifier: [`run_experiment.py`](../../model/M5_CEREBELLAR_SOURCE_LTD_TRANSFER_V2/run_experiment.py), [`verify_results.py`](../../model/M5_CEREBELLAR_SOURCE_LTD_TRANSFER_V2/verify_results.py)
- Outputs and run manifest: [`data/results/M5_CEREBELLAR_SOURCE_LTD_TRANSFER_V2/`](../../data/results/M5_CEREBELLAR_SOURCE_LTD_TRANSFER_V2/)
