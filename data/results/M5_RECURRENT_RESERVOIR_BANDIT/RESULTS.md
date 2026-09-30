# M5 recurrent-reservoir contextual-bandit follow-up

**Status:** completed once under the post-result exploratory contract. Prior M5 outcomes were known before this architecture follow-up. This is not confirmatory evidence.

## Result

Across 30 task seeds, averaging the paired eligibility-trace minus no-trace held-out expected-reward contrast equally over delays 1, 4, 16, and 64 gave **+0.002887** (paired task-seed bootstrap 95% interval **[+0.002089, +0.003815]**). The four-delay contrast was positive in 27/30 seeds. By delay, trace-minus-no-trace was +0.003982, +0.003530, +0.002612, and +0.001423. Exact replay remained stronger: mean held-out expected reward was 0.51812 for replay, 0.50327 for trace, and 0.50038 for no-trace.

This supports a narrow claim: on this fixed random recurrent-reservoir policy and this synthetic contextual-bandit objective, the norm-matched eligibility update modestly exceeded the current-score update. The primary mean was smaller than in the feed-forward bandit run (+0.00914), and the benefit decayed with delay. The reservoir state was recurrent, but its core weights were fixed; only the linear readout was trained. This is not a trained RNN/LNN/LTC, architecture-family generalization, biological evidence, or connectome transfer.

## Execution and audit

The run produced 360 seed × delay × arm metric rows, 4,320 training-trajectory rows, and 120 seed-delay contrast rows. An independent post-run script recomputed the seed-level estimand and 20,000-resample bootstrap interval from the saved metrics; all values were finite and the frozen contract and runner hashes matched preflight.

The run emitted NumPy `RuntimeWarning`s during matrix operations in task-probability/evaluation calculations. The resulting saved metrics and trajectories were finite and independently reproduced, but the warning's origin was not isolated. This runtime issue is disclosed as a reproducibility concern and should be diagnosed before extending this particular implementation.

## Files

- Frozen contract: `M5_RECURRENT_RESERVOIR_BANDIT_CONTRACT.md`
- Runner: `run_recurrent_reservoir_bandit.py`
- Preflight: `M5_RECURRENT_RESERVOIR_BANDIT_PREFLIGHT.json`
- Metrics, contrasts, and manifest: this directory
- Independent verification: `POSTRUN_VERIFICATION.json`
