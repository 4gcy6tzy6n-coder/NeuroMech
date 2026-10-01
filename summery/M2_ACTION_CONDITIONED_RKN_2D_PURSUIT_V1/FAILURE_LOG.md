# M2 action-conditioned state-space comparison — failure and limitation log

## Implementation corrections

- **Optional upstream dependency:** the vendored AcRKN cell imported `util.ConfigDict`, which was absent from this standalone experiment. Added a minimal fallback for configuration access; the experiment passes its configuration explicitly. The one-seed pilot passed before the canonical run. No outcome-dependent changes were made after the pilot.
- **Pilot output:** one-seed debugging results were written outside the repository (`/tmp`) and are not included in the canonical analysis. They were not used for model selection or to change the frozen endpoint.

## Scientific limitations and negative evidence

- **Matched generic baseline wins:** the 8-parameter bilinear recurrent estimator has lower final distance than the 8-parameter M2 mode-gain estimator in both mappings. This blocks a claim of unique M2 algorithmic benefit in this benchmark, even though the frozen mode-gain versus AcRKN contrast is positive.
- **Task-shift weakness:** mode-gain performance degrades strongly under the reversed sensor mapping. The aligned result is not robust to this defined mapping shift.
- **Adapted AcRKN is not a reproduction:** the arm adapts the official AcRKN cell with an experiment-specific encoder and readout. It uses 32 parameters, one latent observation dimension, and a small training budget. Its poor performance cannot establish that the published AcRKN method is generally inferior.
- **Unequal compute:** all learned arms receive the same number of optimizer updates and sequence tokens, but AcRKN has a larger model and materially different wall-clock cost. The task-aware Kalman reference is given the true task model and is not a learned, capacity-matched control.
- **Yoke interpretation:** the donor action multiset at each time matches exactly and the permutation has no fixed points, but donor actions cause recipient trajectories to diverge. The contrast does not isolate one biological feedback pathway.
- **Exploratory status:** the task family and related M2 outcomes were already known. Fresh seeds reduce reuse of specific episodes but do not make this a confirmatory or independent task-family test.

## Disposition

Retain the result as a task-specific boundary: mode-gain beats this adapted AcRKN baseline in the aligned primary contrast and beats a distribution-preserving action yoke, while a parameter-matched generic bilinear estimator is better in both sensor mappings. Do not promote the primary contrast alone as support for a biological mechanism or a general machine-learning principle.
