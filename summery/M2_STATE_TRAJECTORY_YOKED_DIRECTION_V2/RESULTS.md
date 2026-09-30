# M2 full state-trajectory yoke V2 — results

**Classification:** retrospective, outcome-informed source-model analysis. Earlier M2 feedback-site and yoke outcomes were known before this follow-up. Do not treat it as confirmatory, biological validation, or AI-transfer evidence.

## Primary result

Across the three imposed noise scales, the equal-weighted seed-block mean for `SENSORY_SITE_FB − FULL_TRAJECTORY_YOKE` warm-direction index was **+0.45159** (paired seed-block bootstrap 95% interval **[+0.44434, +0.45887]**; **200/200** seed blocks positive). Per-scale contrasts were +0.59043 at noise 0.75, +0.43597 at 1.00, and +0.32837 at 1.25; all 200 held-out blocks were positive at each scale.

| Noise | Direction-index difference (95% paired seed-block interval) | Mean forward-bout difference | Median difference | P90 difference | ≥30 s fraction difference | Occupancy difference | Bout-count difference |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.75 | +0.59043 [+0.57295, +0.60821] | +0.0179 s | +0.0160 s | −0.3367 s | −0.00097 | +0.00013 | −0.05 |
| 1.00 | +0.43597 [+0.42636, +0.44549] | +0.0148 s | −0.0127 s | +0.0167 s | −0.00010 | −0.00005 | −2.08 |
| 1.25 | +0.32837 [+0.32189, +0.33482] | −0.0140 s | −0.0103 s | +0.0013 s | +0.00013 | −0.00330 | −7.13 |

Persistence statistics are sensory-site minus trajectory-yoke held-out means. They are descriptive diagnostics; no equivalence margins were frozen, so the yoke must not be called statistically equivalent or fully matched.

## Interpretation

Compared with V1's independent bout-duration resampling, V2 replays complete ordered movement-state sequences and the corresponding latent motor-state sign sequences from independent development trajectories. Heading changes use the source model's two-step latent-state timing. The held-out yoke therefore preserves each donor's temporal bout pattern while disconnecting it from the held-out agent's position, heading, and outcome.

The large direction-index contrast persists while the reported marginal persistence summaries are close. Within this corrected source-model implementation, replaying an independently sampled motor-state trajectory is insufficient to reproduce the sensory-feedback model's warm-direction behavior. The omitted ingredient may be coupling between current sensory/environmental state and motor-state transitions. This does not isolate a biological synapse, show that every possible motor-only controller fails, or validate the source model against new biological data. MATLAB/Octave numerical parity remains unverified.

## Provenance and implementation corrections

The analysis used development blocks 370000–370029 and held-out blocks 380000–380199, with 50 simulated agents per block and noise scales 0.75, 1.00, and 1.25. The simulation seed block—not each agent or timestep—is the analysis unit. It is a computational unit, not an animal.

An initial completed pilot was superseded because it triggered heading changes from the smoothed movement sequence. The source model instead updates heading from latent motor-state signs with a two-step history. The final runner captures both the smoothed movement state and latent motor-state sign sequence from the same donor trajectory and replays them with the original timing. Superseded outputs are retained under `data/results/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/superseded_v1_heading_timing_mismatch/` and excluded from the final estimate. The earlier incomplete capture attempt did not produce held-out results.

## Reproduction

From the repository root, run `python3 model/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/run_experiment.py`. The runner refuses to overwrite a nonempty final output directory. The final metrics, development donor sequences, source checksums, and run manifest are archived under `data/results/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/final/`.
