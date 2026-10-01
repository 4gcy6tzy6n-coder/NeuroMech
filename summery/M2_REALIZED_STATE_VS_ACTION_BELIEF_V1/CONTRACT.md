# M2 realized-state feedback versus action-conditioned state estimation V1

**Classification:** outcome-informed exploratory follow-up. It is motivated by `M2_ACTUATION_UNCERTAINTY_STATE_FEEDBACK_V1`; it cannot be reported as independent confirmation. No biological or general-AI claim is licensed by this simulation alone.

## Question

Does a compact action-conditioned recurrent state estimator gain control performance from a direct, one-channel measurement of realized movement state when actuator reversals are hidden, beyond what it can infer from intended actions and intermittent sensory observations?

This is a narrower and stronger question than whether an equal-parameter GRU receiving realized movement sign beats one receiving command sign. The action-conditioned baseline has a learned latent transition explicitly conditioned on the command, using an AcRKN cell adapted as an end-to-end controller.

## Task

Use the existing one-dimensional target-tracking plant and its bursty, 50%-missing relative-position observations. Fix target persistence to `0.91`, target-velocity innovation SD to `0.055`, observation-noise SD to `0.14`, missing fraction to `0.50`, mean missing-burst duration to `8`, and episode length to `64` steps. Remove additive motor noise and actuator inertia for this test. Executed displacement is `0.40 × command × reversal_sign`, where `reversal_sign` is −1 with the sampled probability and +1 otherwise. Training samples reversal probability uniformly from `[0, 0.25]`. Generate the reversal sequence independently of the controller so paired arms share it. The held-out conditions are:

- `NO_REVERSAL`: probability 0; realized movement sign is fully determined by the command.
- `HIDDEN_REVERSAL`: probability 0.25; the reversal event is not observed.
- `REVEALED_REVERSAL`: same reversal trajectories as the hidden condition, but the reversal-event bit is supplied as an additional observation. Given the intended command, this reconstructs the realized movement sign and is an information-recovery control.

All arms receive paired target, observation-noise, missingness, and reversal random streams within each training-seed block. Closed-loop trajectories may diverge after different actions; seed block, not episode or time step, is the inferential unit.

## Arms

1. `ACRKN_ACTION_ONLY`: AcRKN-cell policy; command enters its action-conditioned latent transition, with no valid realized-state measurement.
2. `ACRKN_REALIZED_STATE`: same AcRKN architecture and budget, with the sign of realized movement as a valid one-dimensional proprioceptive measurement.
3. `ACRKN_REVERSAL_REVEALED`: same architecture and budget, with the reversal-event bit as the measurement; command plus event reconstructs executed movement.
4. `GRU_ACTION_ONLY` and `GRU_REALIZED_STATE`: equal-parameter generic recurrent controls, retaining the previous implementation family to test whether any effect depends on the AcRKN inductive structure.
5. `TASK_AWARE_PARTICLE_FILTER`: an explicitly non-capacity-matched model-based reference. A bootstrap particle filter tracks target position/velocity, agent position, and latent reversal events from commands and sensory observations, but does not observe hidden reversals. Feed posterior target-relative position and agent velocity to the common fixed feedback law `command = tanh(k_p × estimated_error − k_d × estimated_velocity)`. Select `k_p` and `k_d` on disjoint validation streams shared across seed blocks. Report particle-count/ESS convergence and inference compute separately; this is a model-based reference, not a learned AI baseline.

The AcRKN arms must have equal trainable parameter counts (target 321, tolerance at most 2 parameters, with exact realized counts reported), identical optimizer/update/sample budgets, and the same action-conditioned transition. No inert padding parameters are allowed. The GRU pair must likewise be exactly parameter matched. If implementation cannot preserve those conditions, reduce the comparison to a clearly labeled diagnostic and do not interpret it as architecture-specific.

## Primary estimand

Primary endpoint: episode-mean squared target-relative distance (MSE; lower is better).

Primary contrast: `ACRKN_ACTION_ONLY − ACRKN_REALIZED_STATE` in `HIDDEN_REVERSAL`. A positive contrast favors direct realized-state measurement.

Information-recovery contrast: difference between that contrast in `HIDDEN_REVERSAL` and `ACRKN_REVERSAL_REVEALED − ACRKN_REALIZED_STATE` in `REVEALED_REVERSAL`. If the movement bit's advantage is information-specific, the latter gap should be near zero once the reversal bit is revealed.

Report paired seed-block bootstrap 95% intervals, all arm means, all three conditions, calibration/particle diagnostics, trainable parameter counts, optimizer updates, training tokens, and measured inference wall time. Do not pool episode or frame counts as independent samples.

## Samples and reproducibility

Use 32 paired training-seed blocks (`950000–950031`) and 128 held-out episodes per seed block, arm, and condition. Train with 160 optimizer updates, batch size 32, and sequence length 64 for each learned arm. Use disjoint implementation-feasibility seeds only if necessary and report them separately. Retain every seed-level outcome, model-fit record, environment stream identifier, source hash, and independent verifier output. Repeat the full run and compare scientific outputs byte-for-byte, excluding only declared nondeterministic timing fields.

## Falsification and interpretation

- If `ACRKN_ACTION_ONLY` matches `ACRKN_REALIZED_STATE` under hidden reversals, direct feedback has no demonstrated task-performance value beyond action-conditioned inference in this plant.
- If realized-state input helps at zero reversal, check the implementation: the state bit should be derivable from the command. A performance gap here indicates architecture/training imbalance or an input-path confound, not evidence for hidden-state information.
- If `ACRKN_REVERSAL_REVEALED` fails to approach the realized-state arm, the information-recovery control has failed; do not interpret the hidden-reversal contrast as specific to information access.
- If only the exact, uncorrupted state signal helps, label the effect privileged-sensor dependent. A separate corruption/delay test is required before any robust-sensor claim.
- Even a clean positive result establishes only a bounded artificial benefit of an execution-state observation over action-conditioned inference in this task. It does not show that RIM→AIY transmits this exact physical variable, prove biological-to-AI transfer, or establish general AI benefit.

No single PASS label will replace the arm-level results and their interpretation.
