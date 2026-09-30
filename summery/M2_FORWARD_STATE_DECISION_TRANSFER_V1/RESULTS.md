# M2 downstream decision-utility probe V1

**Status:** post hoc exploratory analysis of frozen `M2_FORWARD_STATE_SENSORY_GATE_V3` models and streams. V3 outcomes were already known, and this is not confirmatory. Models were not retrained.

## Results on in-range, aligned episodes

A `MODE_GAIN_FILTER` estimate was converted to three fixed decision readouts. Sign-choice accuracy was `0.701` versus `0.672` for the constant-gain ablation, `0.694` for the bilinear RNN, `0.680` for the GRU, and `0.707` for the Kalman oracle. Persistent sign-action utility with a `0.10` action-switch cost was `0.690` for mode gain, `0.656` for constant gain, `0.685` for bilinear RNN, `0.669` for GRU, and `0.699` for the Kalman oracle. In the threshold-choice task, mode gain had lower regret (`0.00644`) than the constant filter (`0.00702`), bilinear RNN (`0.00690`) and GRU (`0.00813`); the Kalman oracle again had the lowest regret (`0.00614`). These are descriptive means, not inferential tests.

## Distribution-shift boundary

In the INDEPENDENT mapping, sign accuracy was `0.704` for mode gain versus `0.745` for constant gain and `0.748` for the Kalman oracle. Under REVERSED mapping, sign accuracy fell to `0.595` for mode gain; constant gain reached `0.673` and Kalman `0.705`. The threshold and persistence readouts show the same general vulnerability under reversal. Thus the aligned decision advantage carries into simple downstream utilities on these same episodes, but the frozen estimator transfers poorly when its learned context–observation relation changes.

## Interpretation and limits

This probe shows that the V3 state estimate can produce better simple decisions in the aligned synthetic condition. It does not test policy learning, interactive control, a new task family, or a biological mechanism. All conditions reuse the same latent-estimation task streams; the three utility functions are post hoc readouts. The analysis is exploratory, with no confidence intervals or multiplicity correction, and cannot support broad AI or NMI-level claims by itself.

- [`Analysis contract`](CONTRACT.md)
- [`Analysis runner`](../../model/M2_FORWARD_STATE_DECISION_TRANSFER_V1/run_analysis.py), [`finalizer`](../../model/M2_FORWARD_STATE_DECISION_TRANSFER_V1/finalize_analysis.py) and [`independent verifier`](../../model/M2_FORWARD_STATE_DECISION_TRANSFER_V1/verify_analysis.py)
- [`Episode-level decisions and summary`](../../data/results/M2_FORWARD_STATE_DECISION_TRANSFER_V1/)
