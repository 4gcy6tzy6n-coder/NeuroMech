# M2_BURSTY_COMPUTE_FRONTIER_V1 — results and interpretation

## Outcome

This post-result exploratory experiment asked whether the sensory-site feedback controller's earlier performance under bursty observation loss would disappear when generic recurrent controls received more optimization. It trained five controllers on the same task family and data volume for 60, 120, or 240 optimizer updates, then evaluated fresh paired trajectories at three observation-gap regimes. The independent verifier passed the complete 184,320-episode and 480-checkpoint grid and recomputed the seed-block bootstrap summaries.

At the primary long-gap condition (`q=0.125`) after 240 updates, the four-parameter sensory-site controller had tracking MSE `0.66569` (95% seed-block bootstrap interval `[0.65661, 0.67478]`). It beat the four-parameter generic scalar RNN by `0.06183` MSE (`GENERIC_RNN − SENSORY_SITE = +0.06183`, 95% interval `[+0.05816, +0.06580]`, 32/32 seed blocks positive). It also had lower MSE than the equal-parameter output-site controller (`+0.01531`, `[+0.00901, +0.02146]`, 27/32 positive) and no-feedback control (`+0.01209`, `[+0.00705, +0.01776]`, 29/32 positive).

The higher-capacity 321-parameter GRU improved with added optimization and was better on the primary MSE endpoint: `GRU_8 − SENSORY_SITE = −0.07726` (`[−0.08775, −0.06633]`, 0/32 seed blocks positive for that contrast). At 60 updates its contrast was unresolved (`−0.00126`, `[−0.00983, +0.00780]`); by 120 updates it favored the GRU (`−0.04466`, `[−0.05074, −0.03899]`). More optimization therefore does not rescue the sensory-site controller's standing against this larger recurrent model.

### Long-gap endpoint by optimization budget

| Updates | Sensory-site MSE | Output-site MSE | No-feedback MSE | Generic RNN MSE | GRU-8 MSE |
|---:|---:|---:|---:|---:|---:|
| 60 | 0.6712 | 0.7355 | 0.7380 | 0.7334 | 0.6699 |
| 120 | 0.6683 | 0.7017 | 0.7040 | 0.7312 | 0.6237 |
| 240 | 0.6657 | 0.6810 | 0.6778 | 0.7275 | 0.5884 |

The sensory-site controller's advantage over the same-size output-site and no-feedback arms narrows with training (from about `0.064–0.067` MSE at 60 updates to `0.012–0.015` at 240), but remains positive on the primary endpoint. This pattern is consistent with an optimization/sample-efficiency benefit in this task, not an asymptotic performance advantage. Equal optimizer updates do not imply equal FLOPs; the GRU is over 80 times larger by parameter count and consumes more compute per update.

### Metric trade-offs

The MSE ranking is not a universal quality ranking. At 240 updates and `q=0.125`, the sensory-site controller had lower action energy (`0.3185`) than output-site feedback (`0.4680`), no feedback (`0.4381`), and the GRU (`0.4957`). It had slower post-gap recovery than output-site (`9.92` vs `8.04` steps) and no feedback (`8.34`), and higher MAE than either (`0.5751` vs `0.5482` and `0.5488`). The GRU achieved lower MSE but had higher MAE, action energy, and recovery latency than sensory-site feedback (`0.6029`, `0.4957`, and `13.52` respectively). The MSE/MAE divergence indicates tail-sensitive errors and makes any one-number “best controller” claim inappropriate.

## Interpretation

**Supported, narrowly:** in this simulator, the placement of previous motor output in the sensory-state update produces a persistent long-gap MSE advantage over equal-parameter output-site, no-feedback, and generic scalar recurrent controls, even after 240 updates. The effect weakens with optimization for the placement controls. The result also exposes a stability/accuracy/energy trade-off: sensory-site feedback uses less action energy, but recovers more slowly and has higher MAE than output-site feedback.

**Not supported:** sensory-site feedback does not outperform the trained 8-unit GRU on MSE; the GRU increasingly dominates that endpoint as update budget rises. The task's hidden observation-gap process is artificial and not a measured feature of the worm circuit. This result does not establish a biological mechanism's AI benefit, a unique synapse, or broad task generalization.

The biological motivation remains the bounded published result that RIM-dependent motor-state information alters AIY sensory representation and forward-run persistence in *C. elegans* thermotaxis ([Ji et al., eLife 2021](https://elifesciences.org/articles/68848)). This simulator does not reproduce the experiment or identify the biological circuit's transfer function.

## Reproducibility

- Primary machine-readable summary: [`summary.json`](../../data/results/M2_BURSTY_COMPUTE_FRONTIER_V1/summary.json)
- Episode-level results and fitted checkpoint parameters: [`episode_results.csv`](../../data/results/M2_BURSTY_COMPUTE_FRONTIER_V1/episode_results.csv), [`checkpoint_results.csv`](../../data/results/M2_BURSTY_COMPUTE_FRONTIER_V1/checkpoint_results.csv)
- Independent audit: [`POSTRUN_VERIFICATION.json`](../../data/results/M2_BURSTY_COMPUTE_FRONTIER_V1/POSTRUN_VERIFICATION.json)
- Runner: [`run_experiment.py`](../../model/M2_BURSTY_COMPUTE_FRONTIER_V1/run_experiment.py)
- Verifier: [`verify_results.py`](../../model/M2_BURSTY_COMPUTE_FRONTIER_V1/verify_results.py)
