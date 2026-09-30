# M2 context-information dose response V1 — results

**Classification:** exploratory artificial mechanism study. Prior M2 outcomes informed the design; this is neither confirmatory evidence nor biological validation.

## Main result

Thirty independently generated training datasets/initializations were fit at the fully aligned context mapping (`kappa=+0.50`) and evaluated on the same 256 held-out trajectories over 11 context-information levels. The latent path, motor-state path, and observation-noise innovations were held fixed across dose levels. The primary contrast is `MSE(CONSTANT_GAIN_FILTER) - MSE(MODE_GAIN_FILTER)`; positive values favor state-conditioned gain.

| Test context dose κ | Mode-gain MSE | Constant-gain MSE | Constant − mode (crossed 95% CI) |
|---:|---:|---:|---:|
| −0.50 | 0.09521 | 0.06356 | −0.03165 [−0.03626, −0.02761] |
| −0.20 | 0.07556 | 0.05435 | −0.02121 [−0.02486, −0.01823] |
| 0.00 | 0.06623 | 0.05311 | −0.01312 [−0.01582, −0.01081] |
| +0.20 | 0.05989 | 0.05577 | −0.00412 [−0.00610, −0.00248] |
| +0.30 | 0.05786 | 0.05857 | +0.00072 [−0.00098, +0.00232] |
| +0.40 | 0.05657 | 0.06235 | +0.00578 [+0.00409, +0.00759] |
| +0.50 | 0.05603 | 0.06711 | +0.01108 [+0.00904, +0.01328] |

The estimated zero crossing was `κ=0.285` (crossed-bootstrap 95% interval `[0.251, 0.318]`; a crossing occurred in all 10,000 bootstrap draws). At the fully aligned endpoint, all 30 training-seed means favored mode gain. At `κ=+0.30`, the interval still overlaps zero; the first tested level with a clearly positive interval is `+0.40`.

At the fully aligned endpoint, mode gain also beat the learned generic RNN by `0.01261` MSE and the bilinear RNN by `0.00617` MSE (both seed-bootstrap intervals excluded zero). The task-aware Kalman oracle remained better than mode gain by `0.00231` MSE. At `κ=0`, the generic RNN was better than mode gain by `0.01305`. This reinforces that the structured update's advantage is conditional and its transfer depends on the context-information relation.

## Interpretation and limits

The experiment quantifies a sharp operating boundary for this trained model: a gain filter learned under full alignment incurs increasing error as context becomes less informative, is clearly worse than the context-free ablation through `κ=+0.20`, is statistically unresolved at `+0.30`, and becomes better at `+0.40` and `+0.50`. The sign reversal under negative κ is expected from using a mapping learned under the opposite relation.

This is an artificial scalar estimation task. It does not show that the worm circuit represents observation reliability as `H(q,κ)`, and does not show that the biological mechanism itself has this numerical threshold. The test stream is one fixed cohort of 256 generated episodes, paired across policies and κ; uncertainty resamples both training seeds and test episodes, but broader task-generator and task-family generalization remain to be tested. The oracle is task-aware and not capacity matched.

## Reproduction and artifacts

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner, analyzer, and independent verifier: [`model/M2_CONTEXT_INFORMATION_DOSE_V1/`](../../model/M2_CONTEXT_INFORMATION_DOSE_V1/)
- Raw episode metrics, fitted parameters, seed contrasts, summary, manifest, and checksums: [`data/results/M2_CONTEXT_INFORMATION_DOSE_V1/`](../../data/results/M2_CONTEXT_INFORMATION_DOSE_V1/)
- Independent verification reproduced all 422,400 unique episode-policy rows and all 11 primary crossed-bootstrap intervals.
