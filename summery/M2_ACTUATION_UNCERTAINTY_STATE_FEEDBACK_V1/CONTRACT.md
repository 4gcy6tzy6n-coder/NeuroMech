# M2 actuation-uncertainty state-feedback dose test V1

**Classification:** outcome-informed exploratory artificial experiment. Earlier M2 results motivate the study. A six-seed task-adequacy preflight will be disclosed; the full run will use disjoint seeds. This is not biological validation.

## Question

Does realized categorical movement-state input become more useful than intended action-sign input as actuator execution becomes less predictable?

## Task and manipulation

An agent tracks a one-dimensional persistent moving target with noisy, bursty-missing relative-position observations. The actuator has inertia and motor noise. At each step, with probability `p_reverse`, its realized velocity is unexpectedly sign-reversed after the intended action update. Test levels are fixed at `p_reverse ∈ {0, 0.10, 0.25, 0.40}`; all arms see identical target, observation, motor-noise, missingness, and reversal realizations. Training episodes sample `p_reverse` uniformly from `[0, 0.40]`.

The four learned arms are equal-parameter GRUs (321 parameters): `SELF_STATE` receives the sign of realized velocity; `ACTION_STATE` receives the sign of its preceding command; `ZERO_STATE` receives a zero feedback channel; `YOKED_STATE` receives another episode's realized-state sequence through a no-fixed-point derangement. A fixed reactive controller is a nonlearned reference, not capacity matched. All arms use the same 160-update budget and paired seed initialization.

## Primary endpoint and analysis

Primary metric is episode-mean squared target-relative distance. For each test level, define state-feedback advantage as `ACTION_STATE MSE − SELF_STATE MSE` (positive favors realized state). The primary estimand is the dose interaction:

`advantage(p=0.40) − advantage(p=0.00)`.

Positive interaction means the advantage of realized state over action sign grows as actuator reversals become more common. Estimate the 95% percentile bootstrap interval by resampling 32 paired training-seed blocks (20,000 draws; fixed seed 8,765,502). Report each test level separately and the paired interaction. Episodes and time steps are nested observations, not inferential units. Zero-input and recipient-yoke comparisons are prespecified secondary controls.

## Training and test samples

Full run: 32 paired training-seed blocks (`940000–940031`), 128 held-out episodes per seed × test level × arm. Train each model on 160 updates of 32 sequences × 64 steps. Test dropouts have 50% missingness with mean missing burst 8; target persistence is `0.91`. The preflight uses disjoint seeds `930000–930005` and does not contribute to primary estimates.

## Interpretation boundary

A positive dose interaction would support a bounded artificial claim: the value of a realized categorical state signal increases under the tested form of actuator uncertainty. It would not establish that the worm circuit implements this controller, that natural RIM→AIY feedback compensates actuator reversals, or that the result generalizes beyond the tested tracking simulator. A null interaction or unresolved yoke comparison will be reported as such. No threshold-based PASS/FAIL label is used.
