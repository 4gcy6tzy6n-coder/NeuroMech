# M2 state-trajectory yoke V2 contract

**Experiment ID:** `M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2`

**Classification:** retrospective, outcome-informed source-model analysis. Previous M2/V3/V4/V5 and marginal-yoke V1 results were known before this follow-up. It is not confirmatory, biological validation, or AI-transfer evidence.

## Question

Does the corrected source model's sensory-site feedback produce warm-direction behavior that cannot be reproduced by replaying complete ordered motor-state trajectories independently of each held-out agent's position, heading, and outcome? This extends the V1 marginal-duration yoke, which resampled each bout independently and therefore discarded serial order between bouts.

## Arms and yoke construction

The held-out comparison includes `SENSORY_SITE_FB` (sensory-site coefficient 1.0, motor coefficient 0), `MOTOR_MULTI_STAT_MATCHED` (V5 development-selected motor-only coefficients 0.760, 0.665, and 0.610 at noise scales 0.75, 1.00, and 1.25), `NO_FEEDBACK`, and `FULL_TRAJECTORY_YOKE`. For each noise scale, 30 development seed blocks generate complete ordered movement-state sequences and their corresponding latent motor-state sign sequences from 50 agents each. Each held-out yoke agent independently draws one donor and replays both sequences over the full 1,500-step, 200-second record. Movement uses the donor's smoothed movement-state sequence; heading transitions use the donor's latent motor-state signs with the source model's two-step transition timing. The donor is independent of the held-out position, heading, and direction outcome. Source and yoke arms use paired held-out seed blocks; yoke sequence selection uses a separate deterministic random stream.

## Samples and unit

Development seed blocks are 370000–370029; held-out seed blocks are 380000–380199. Noise scales are 0.75, 1.00, and 1.25. There are 50 agents per seed block, with 1,500 simulation steps per trajectory. The analysis unit is the simulation seed block; agents and timesteps are clustered. These simulation units are not biological animals.

## Outcomes

The primary estimand is the equal-weighted within-seed `SENSORY_SITE_FB − FULL_TRAJECTORY_YOKE` warm-direction-index difference averaged across the three noise scales. Report the mean, paired seed-block bootstrap 95% percentile interval (20,000 resamples; seed 20261007), and positive-block count. Secondary outcomes include forward-bout mean, median, P90, fraction at least 30 seconds, occupancy, and bout count. Report persistence differences descriptively; no equivalence margin is defined, so do not claim the motor distributions are statistically equivalent or matched.

## Interpretation limits

A nonzero direction contrast can show only that replaying a donor motor-state sequence independently of the held-out environment is insufficient to reproduce the source model's outcome. It does not identify a unique biological synapse, establish that all motor-only controllers fail, validate the source model biologically, or demonstrate AI transfer. A persistence mismatch weakens the feedback-placement interpretation. The analysis is retrospective because prior outcomes motivated the sequence-preserving repair.

## Provenance

The execution archives the contract, copied source-model implementation with sequence capture, author MATLAB source file checksum, V5 coefficient summary checksum, development sequence library, held-out outputs, runtime, and SHA-256 manifest. Historical M2 experiments remain unchanged.
