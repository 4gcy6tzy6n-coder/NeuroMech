# Results — M5 eligibility trace under a bounded feature-memory budget V1

**Status:** completed, post-result exploratory comparison. The M5 task family and earlier eligibility results were already known. This run uses task seeds 100–129 and does not serve as independent biological or confirmatory evidence.

## Primary result

Across three fixed input generators, 30 task seeds per generator, and four delays, the 64-value eligibility trace exceeded the one-vector `EXACT_FIFO_64` arm by **0.14779 held-out accuracy** on average (hierarchical task-seed bootstrap 95% interval **[0.13757, 0.15796]**; positive in **90/90** generator-by-seed blocks). Generator-specific averages were +0.12261 (IID Gaussian), +0.19160 (AR(1) Gaussian), and +0.12916 (sparse sign).

That aggregate contrast is delay-dependent. Trace minus FIFO-64 was −0.15363, +0.32943, +0.29311, and +0.11550 at delays 1, 4, 16, and 64 respectively, averaging over the three generators. At delay 1, exact retention of one cue was better. At longer delays, the one-vector FIFO often discarded the cue before its label arrived: its update coverage was 1/3000 at delays 4–64. The primary result therefore compares a decaying compressed state with a FIFO that loses almost all delayed updates at those delays.

## Memory–accuracy frontier

Exact FIFO accuracy rose as capacity became sufficient to preserve delayed cues. At delay 4, a four-vector FIFO (256 feature values) approached exact replay. At delay 16, a 16-vector FIFO (1,024 values) did so. At delay 64, a 64-vector FIFO (4,096 values) approached exact replay. The unbounded exact-replay reference remained around 0.747–0.766 mean accuracy, depending on generator and delay, while the trace used 64 active feature values. The trace is a compact alternative in this task, not a more accurate learner when replay has sufficient capacity.

The normalized feature-state accounting counts retained feature vectors only; common prediction/error queues and task storage are excluded. It is not a measurement of RAM, energy, or runtime efficiency. The task is one synthetic delayed-label classification family with three fixed input generators and a fixed trace decay (`γ=0.98`). It does not compare against other compressed-memory algorithms, tune a frontier across decay factors, or establish transfer to arbitrary tasks.

## Interpretation

The evidence supports a narrow, conditional statement: under this task and declared active-feature-state budget, an eligibility trace can preserve useful delayed credit better than a one-vector FIFO at delays 4–64, while direct one-vector retention wins at delay 1 and adequately sized exact replay wins once memory scales with the delay. The observed gain is partly explained by the FIFO comparator's update loss. This is a bounded-memory tradeoff, not a general eligibility-trace advantage, biological validation, or a shared project-level AI principle.

The figure and complete seed-level outputs are in [`data/results/M5_ELIGIBILITY_MEMORY_FRONTIER_V1/`](../../data/results/M5_ELIGIBILITY_MEMORY_FRONTIER_V1/); the runner and independent verifier are in [`model/M5_ELIGIBILITY_MEMORY_FRONTIER_V1/`](../../model/M5_ELIGIBILITY_MEMORY_FRONTIER_V1/). See [`CONTRACT.md`](CONTRACT.md) for the frozen estimand and resource accounting.
