# M5 delayed-reward contextual-bandit results

**Status:** `POST_RESULT_EXPLORATORY_TRANSFER_TEST`. The M5 classification results were already known when this different-objective follow-up was designed. No parameters were tuned from bandit outcomes.

## Primary result

The fixed norm-matched eligibility trace minus the no-trace update had a mean held-out expected-reward difference of **`+0.00914`** (0–1 reward scale), with paired task-seed bootstrap 95% interval **`[+0.00772, +0.01088]`**. The task-seed-averaged four-delay contrast was positive for all 30 independent task seeds.

| Delay | Eligibility trace | No trace | Exact replay | Trace − no trace |
|---:|---:|---:|---:|---:|
| 1 | 0.5131 | 0.5000 | 0.5525 | `+0.01308` |
| 4 | 0.5123 | 0.5005 | 0.5525 | `+0.01180` |
| 16 | 0.5093 | 0.5008 | 0.5525 | `+0.00859` |
| 64 | 0.5037 | 0.5006 | 0.5525 | `+0.00310` |

Across seeds and delays, mean expected reward was `0.5096` for the eligibility trace, `0.5005` for no-trace, and `0.5525` for exact replay. Per-delay differences are descriptive under the frozen contract; only the four-delay seed-level average has an interval and primary decision.

## What transferred, and what did not

This task changes the learning problem from supervised classification with delayed class labels to a two-action contextual bandit with delayed stochastic scalar rewards. The same fixed eligibility operation retains a small advantage over assigning reward to the current decision. This is a first positive result across two synthetic task objectives, within a deliberately narrow online-gradient setting.

The advantage falls as reward delay increases, from about 1.31 percentage points at delay 1 to 0.31 points at delay 64. Exact replay remains about 4.3 percentage points above the trace averaged over all conditions. The trace's advantage over no-trace is statistically distinguishable from zero in this fixed bandit, but modest in magnitude and not competitive with retaining the correct decision's score vector.

## Limitations

- The result is post-result and uses one hand-specified contextual-bandit generator, 30 task seeds, one policy parameterization and one fixed reward baseline.
- The actor is a linear softmax policy; it is not an LNN, RNN or cerebellar model.
- The task is synthetic. The simulation does not measure neural eligibility, climbing-fiber signals or any connectome motif.
- Exact replay is a stronger, higher-memory comparator and remains substantially better.
- This does not establish broad AI benefit, architecture generalization, biological mechanism transfer or an NMI-level connectome result.

## Integrity

The frozen contract/script hashes match preflight. Independent recomputation verified all 360 seed × delay × arm cells, reproduced the primary mean and interval, and checked 4,320 training-trajectory rows. Details and hashes are in [`POSTRUN_VERIFICATION.json`](POSTRUN_VERIFICATION.json); complete results are in [`task_metrics.csv`](task_metrics.csv), [`training_reward_trajectory.csv`](training_reward_trajectory.csv), and [`per_seed_delay_contrasts.csv`](per_seed_delay_contrasts.csv).

## Disposition

The fixed trace showed a small positive advantage over no-trace in this distinct delayed-reward objective. Preserve the delay-dependent decline and the exact-replay gap. Stop this frozen run without tuning. This advances only the artificial algorithmic evidence; it does not close the biological-to-AI transfer chain.
