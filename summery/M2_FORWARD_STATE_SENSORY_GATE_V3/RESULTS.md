# M2 forward-state sensory gate transfer V3 — cross-dynamics results

**Status:** exploratory algorithmic benchmark. V1 and V2 outcomes were known before V3; this is not confirmatory or biological validation.

## Primary result

On the held-out `IN_RANGE × ALIGNED` condition, `MSE(CONSTANT_GAIN_FILTER)-MSE(MODE_GAIN_FILTER)` was `+0.00929` (crossed 95% interval `[+0.00802,+0.01068]`; 20/20 training-seed means positive). The average MSEs were 0.06287 for the constant-gain ablation and 0.05358 for the mode-gain filter, a roughly 14.8% reduction from the ablation. This is a smaller advantage than V2's fixed-dynamics estimate and is the direct mechanism-ablation contrast.

The mode-gain filter also beat a 4-parameter additive RNN by `0.01084` MSE (95% interval `[+0.00929,+0.01252]`), a 5-parameter bilinear RNN with an explicit unconstrained `y×q` term by `0.00488` (`[+0.00365,+0.00620]`), and a 17-parameter one-unit GRU by `0.00851` (`[+0.00408,+0.01421]`). The task-aware Kalman oracle remained better: MSE `0.05125` versus `0.05358` for the learned mode-gain model.

## Boundary and dynamics conditions

The relation change was costly. Within `IN_RANGE`, mode-gain minus constant-gain performance favored the context-free filter by `0.01435` MSE under `INDEPENDENT` and `0.03201` under `REVERSED`; both crossed intervals excluded zero. Under high-persistence extrapolation, the aligned mode-gain advantage over constant gain increased to `0.10924` (95% interval `[+0.09841,+0.12061]`), while it reversed sharply under independent (`−0.13318`) and reversed (`−0.30669`) mappings. Under low persistence, aligned advantage was small (`+0.00512`), and the independent/reversed conditions again favored constant gain. The Kalman oracle was best in every reported environment/condition.

## Interpretation

The benchmark gives stronger support than V2 for a **conditional** algorithmic statement: when context reliably identifies whether the sensory channel carries the latent signal, learned context-dependent gains can outperform a context-free update across variation in latent dynamics. The benefit is not uniformly large, is sensitive to context/observation mismatch, and remains below a model supplied with the true generative parameters. The bilinear RNN came relatively close in the primary condition; the result does not prove that this hand-structured filter is the only or best way to express sensory gating.

This is one family of synthetic scalar estimation tasks derived from an artificial observation-channel abstraction. It does not establish a biological computation, cross-task AI transfer, or a paper-level NMI contribution. A next study must move from state estimation to a decision/control task and compare against trained generic adaptive models under comparable data and compute budgets; prospective biological validation remains a separate missing evidence link.

## Reproducibility

- [`CONTRACT.md`](CONTRACT.md) froze the V3 question, data ranges, models and estimands before this run.
- [`runner`](../../model/M2_FORWARD_STATE_SENSORY_GATE_V3/run_experiment.py), [`finalizer`](../../model/M2_FORWARD_STATE_SENSORY_GATE_V3/finalize_results.py), and [`independent verifier`](../../model/M2_FORWARD_STATE_SENSORY_GATE_V3/verify_results.py) are included.
- The verifier independently recomputed all 36 condition×contrast means and crossed bootstrap intervals, verified all 552,960 unique episode-policy rows, and checked artifact hashes.
- Machine-readable outputs are in [`data/results/M2_FORWARD_STATE_SENSORY_GATE_V3/`](../../data/results/M2_FORWARD_STATE_SENSORY_GATE_V3/).
