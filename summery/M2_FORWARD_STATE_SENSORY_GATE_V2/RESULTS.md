# M2 forward-state sensory gate transfer V2 — corrected exploratory results

**Status:** exploratory corrected run, not confirmatory. V1 outcomes were inspected before this correction. V1 is invalid due to a train/evaluation input mismatch; see [`V1 implementation incident`](../M2_FORWARD_STATE_SENSORY_GATE_V1/IMPLEMENTATION_INCIDENT.md).

## Corrected data flow

The model now trains on the same gated, noisy observations it receives at evaluation and is supervised by the corresponding latent state. The source-inspired synthetic channel is `y[t]=H(q[t])x[t]+0.25z[t]`, with H=1 in forward state and H=0 in reverse state for ALIGNED training. INDEPENDENT uses H=0.5 in both states; REVERSED swaps the ALIGNED mapping. Twenty independently initialized training seeds were evaluated on 512 shared held-out episodes per condition.

## Results

In ALIGNED, `MSE(GENERIC_RNN_1D)-MSE(MODE_GAIN_FILTER)` was `+0.15479` (crossed 95% bootstrap interval `[+0.13915,+0.17098]`; 20/20 seed means positive). The mechanism-specific ablation gave `MSE(CONSTANT_GAIN_FILTER)-MSE(MODE_GAIN_FILTER)=+0.11812` (95% crossed interval `[+0.10310,+0.13381]`; 20/20 seed means positive). Unlike invalid V1, the learned model used context: across seeds, mean learned gain was about `0.62` for q=+1 (forward) and `0.02` for q=-1 (reverse).

This advantage depended on preserving the training relationship. In INDEPENDENT, the mode-gain filter was worse than the constant-gain filter by `0.08168` MSE (95% interval `[-0.09044,-0.07344]`); in REVERSED it was worse by `0.27462` (95% interval `[-0.29150,-0.25838]`). The generic RNN and constant-gain filter both outperformed the mode-gain filter in these shifted conditions. The task-aware Kalman reference remained slightly better in ALIGNED (`0.26103` vs `0.26310`) and substantially better in shifted conditions.

## Interpretation and limits

The corrected simulation supports a narrow algorithmic result: a context-gated sensory update can help on this synthetic task when the state-to-channel mapping is stable, and can hurt when the mapping changes. It does not show that the worm’s circuit implements this exact estimator, establish a general AI advantage, or validate a biological causal claim. The source-model operation is only an inspiration for the synthetic observation channel; the synthetic channel itself is an explicit modeling assumption. V2 is exploratory because the V1 outcome and bug were known before correction. Further work should test robustness across task families and modern, capacity-controlled adaptive baselines before this could support a paper-level AI claim.

## Artifacts

- [`CONTRACT.md`](CONTRACT.md) — task, models, units and estimands.
- `../M2_FORWARD_STATE_SENSORY_GATE_V1/IMPLEMENTATION_INCIDENT.md` — V1 failure provenance.
- [`runner, finalizer and verifier`](../../model/M2_FORWARD_STATE_SENSORY_GATE_V2/) — reproducible code and independent result check.
- [`machine-readable outputs`](../../data/results/M2_FORWARD_STATE_SENSORY_GATE_V2/) — episode-level metrics, learned parameters, summary and checksums.
