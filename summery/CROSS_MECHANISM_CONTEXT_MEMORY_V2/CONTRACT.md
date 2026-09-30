# CROSS_MECHANISM_CONTEXT_MEMORY_V2 — post-result exploratory contract

## Status and question

V1 results are already known, so this is a new post-result exploratory extension, not independent confirmation. It directly addresses two V1 limits: the M2 comparator was a narrow additive filter, and the M5 trial presented only one relevant cue at a time. The M2 and M5 results remain separate, use different task-native outcomes, and are never pooled.

Question: does context-conditioned sensory gain retain a boundary-specific effect against trained recurrent estimators, and can a low-dimensional eligibility trace assign delayed teaching signals under overlapping inputs better than an equal-state latest-input memory?

## M2 design

- Binary latent state flips with hazard 0.04. Observation standard deviation is 0.35 or 1.1, determined by context alignment `κ ∈ {+1, 0, −1}`.
- Per seed, fit the 3-parameter context-gain filter and train an 8-unit GRU that receives `(observation, context)` plus an 8-unit GRU that receives observation only. All train on the same aligned-context trajectories; evaluate on new trajectories in aligned, independent, and reversed mappings.
- Train trajectories: 24 × 300 steps; GRU training: Adam, learning rate 0.01, 50 epochs, full-batch sequence MSE. Each arm's predictions are evaluated on 64 × 300 test steps in each mapping.
- Primary native endpoint: test latent-state MSE. Primary contrast at aligned context: context-aware GRU MSE minus context-gain MSE. Report both GRUs and all mappings; no test-based tuning.
- Model size is explicit: context-gain has 3 fitted parameters; each GRU has 297 (context input) or 273 (observation-only input, including the shared readout) trainable parameters. This is a stronger but not capacity-matched comparison.

## M5 design

- Each task seed draws a 16-dimensional linear teacher and a continuous stream of independent, unit-normalized feature vectors. Each feature receives a binary teaching label, delivered after `D ∈ {1, 4, 16, 64}` subsequent feature inputs. Inputs therefore overlap in time.
- Compare (a) `ELIGIBILITY_TRACE`, a 16-dimensional state `e_t = 0.95 e_(t−1) + x_t`, (b) `LATEST_INPUT`, an equal-dimensional state storing only the current/most recent feature, and (c) `EXACT_FIFO`, a reference that retains the delayed feature explicitly. All learners have the same 16 trainable linear weights, learning rate, stream, and number of feedback updates; FIFO memory grows as `D × 16` and is not state matched.
- Train on 3,000 online updates per seed and delay. Evaluate accuracy on 1,024 fresh examples from the same teacher. No delay-specific decay or learning-rate optimization is allowed.
- Primary native endpoint: held-out classification accuracy. Primary contrast: eligibility minus latest-input accuracy, separately by delay. FIFO is a memory-rich reference, not the primary comparator.

## Shared analysis

- 32 task-seed blocks per mechanism; bootstrap the 32 blocks with 10,000 percentile resamples, seed `20261002`.
- Keep M2 state-estimation MSE and M5 accuracy separate. No combined score or cross-mechanism p-value.
- This benchmark is exploratory because prior M2/M5 outcomes informed the task and comparator selection. It tests artificial systems only and cannot establish biological validation or general AI benefit.

Runner: `model/CROSS_MECHANISM_CONTEXT_MEMORY_V2/run_experiment.py`  
Verifier: `model/CROSS_MECHANISM_CONTEXT_MEMORY_V2/verify_results.py`  
Outputs: `data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/canonical_corrected/`

## Post-run implementation correction

The first run's verifier caught an incorrect hand-calculated parameter count for the observation-only GRU: the GRU has 264 recurrent parameters plus 9 readout parameters, for 273 total. The M5 latest-input arm was also made an explicit 16-dimensional saved state rather than using the current feature array directly; this preserves the same update rule while making its state accounting explicit. The first run is retained as noncanonical. The corrected run is stored separately and is the only canonical result. This correction does not tune model outcomes, but it was made after the first run was inspected; the study remains post-result exploratory.
