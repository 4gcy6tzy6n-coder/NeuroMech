# Results — M2 premotor predictive-signal artificial transfer V2

**Classification:** outcome-informed follow-up to V1. The artificial cue directly carries noisy future-state information; it is not an AIY/AVA measurement or biological validation.

## Primary condition: 128 training episodes, aligned cue

The six-parameter `PREMOTOR_FILTER` reached mean episode AUC `0.7941`; its no-cue ablation reached `0.6887`. Adding the cue improved the structured filter by `+0.1053` (95% seed-bootstrap interval `[+0.1017,+0.1087]`; 20/20 paired seed blocks positive).

The six-parameter generic recurrent model reached `0.8643`; its no-cue ablation reached `0.6881`. Its cue increment was `+0.1762` (95% interval `[+0.1718,+0.1808]`; 20/20 blocks positive). The structured-minus-generic contrast was `−0.0702` (95% interval `[−0.0724,−0.0681]`; 0/20 blocks positive). The larger GRU was nearly identical to the matched generic update (`0.8647`). Thus the structure-specific filter did not outperform the capacity-matched generic recurrence on the primary aligned task.

Recipient yoking lowered the structured filter by `0.1573` AUC and the generic recurrent model by `0.3175`, relative to their aligned cue inputs. Under an uninformative cue (`q=0.50`), the structured model was `0.0509` below its no-cue ablation, while the generic model was `0.1227` below its no-cue ablation. Under reversed cue mapping (`q=0.28`), these penalties were `0.2302` and `0.5122`, respectively. The filter is less sensitive to mismatch, but it does not turn that robustness into an aligned-condition advantage; removing a misleading cue remains better.

## Interpretation and limit

V2 resolves V1's capacity confound: the result is not a hidden win for the six-parameter forecast-fusion filter. A generic six-parameter recurrent update integrates the same cue more effectively when cue and target align. The structured filter shows a narrower failure under distribution shift, but this may reflect its constrained form rather than a biological computation. The cue is artificially constructed as a noisy report of a future target, so this experiment tests an abstract signal-use trade-off only.

The run produced 230,400 episode rows and 360 fitted-model records. The verifier checked artifact hashes, key completeness, parameter counts, and recomputed all seven primary contrast summaries from per-episode outcomes. It did not independently reimplement model training. Detailed output: [`data/results/M2_PREMOTOR_SIGNAL_AI_TRANSFER_V2/`](../../data/results/M2_PREMOTOR_SIGNAL_AI_TRANSFER_V2/).
