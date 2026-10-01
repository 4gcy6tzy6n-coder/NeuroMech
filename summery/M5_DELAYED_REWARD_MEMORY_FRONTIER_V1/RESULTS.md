# Results — M5 delayed-reward bandit memory frontier V1

**Status:** completed, post-result exploratory transfer on new task seeds 30–59. Earlier M5 classification and bandit results informed this experiment. This is not a confirmatory test or biological validation.

## Main finding

The 32-value eligibility trace did **not** outperform the equal-state one-vector exact FIFO across the four delays. The paired task-seed contrast (trace minus FIFO-32, averaging delays within seed) was **−0.002484 held-out expected reward** (95% paired task-seed bootstrap interval **[−0.003243, −0.001717]**); only **1/30** seed-level delay averages favored the trace.

This aggregate masks a delay interaction. Trace minus one-vector FIFO was −0.03532 at delay 1, then +0.01211, +0.00969, and +0.00358 at delays 4, 16, and 64. However, at delays 4–64 the one-vector FIFO applied only **1 of 6,000** delayed reward updates (0.0167%); it is a same-state but severely update-starved comparator. The trace exceeded current-score assignment by **+0.009480** on average (95% interval **[+0.007905, +0.011087]**, positive in 30/30 task seeds), but this is a different contrast and does not show that the trace outperforms exact memory.

## Accuracy–state frontier

When FIFO capacity was sufficient for the delay, it applied all 6,000 updates and exactly reproduced the full exact-replay reference for every seed. Mean held-out expected reward was:

| Delay | Eligibility trace (32 values) | One-vector FIFO (32 values) | FIFO with enough state / exact replay | State for sufficient FIFO |
|---:|---:|---:|---:|---:|
| 1 | 0.51326 | 0.54858 | 0.54858 | 32 |
| 4 | 0.51240 | 0.50029 | 0.54858 | 128 |
| 16 | 0.50998 | 0.50029 | 0.54858 | 512 |
| 64 | 0.50387 | 0.50029 | 0.54859 | 2,048 |

The trace retains a single 32-value state as delay increases. Exact FIFO/replay reaches about 0.549 expected reward when its state grows to `32 × D`. The trace therefore trades accuracy for a smaller active score state in this task; it does not occupy the best-accuracy frontier. Its apparent gain over small FIFOs at delays 4–64 should be interpreted alongside those FIFOs' near-zero update coverage.

## Interpretation and limits

The fixed trace improves over applying delayed reward to the current decision's score, but performs worse than replaying the score that generated each reward. These outcomes are consistent with the value of correct temporal assignment and the cost of retaining the assignment signal; they do not establish an eligibility-trace advantage over strong exact-memory methods.

This is one synthetic contextual-bandit family with a linear-softmax policy, 30 independent task seeds, one fixed reward baseline and trace decay. It is a post-result follow-up to an already studied M5 line. Active state is counted as scalar score values, not measured RAM, energy, or wall time. It does not test a cerebellar circuit, a trained recurrent network, natural data, arbitrary tasks, or general AI benefit.

## Reproducibility

The pre-run contract and runner hashes are preserved in [`PREFLIGHT.json`](PREFLIGHT.json). The canonical run contains 840 task-metric rows, 840 update-coverage rows, and 10,080 trajectory rows. The independent verifier recomputed the primary mean and interval, checked expected update coverage and active-state accounting, verified all output hashes, and confirmed capacity-sufficient FIFO outcomes equal exact replay for every seed and delay. A fresh full runner execution reproduced all task-metric, coverage, trajectory, and contrast CSVs byte-for-byte; see [`REPRODUCIBILITY.json`](../../data/results/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/canonical/REPRODUCIBILITY.json). One post-run verifier expectation was corrected to account for the frozen no-trace rule that skips the D-step flush; the canonical runner and outcome files were not changed. See [`FAILURE_LOG.md`](FAILURE_LOG.md), [`POSTRUN_VERIFICATION.json`](../../data/results/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/canonical/POSTRUN_VERIFICATION.json), and the [figure and QA bundle](../../data/results/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/figures/).
