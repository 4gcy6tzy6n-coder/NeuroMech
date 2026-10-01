# M2 discrete motor-state feedback transfer V1

**Classification:** outcome-informed exploratory artificial experiment. Its task and arms were selected after inspecting the M2 continuous-tracking V1 result and a six-seed feasibility preflight. It is not confirmatory evidence or biological validation.

## Question and bounded biological motivation

Ji et al. report that AIY activity carries locomotor-state and thermosensory information, with RIM required for the locomotor-state representation. This experiment tests a narrow artificial abstraction: can a controller benefit from the *realized categorical movement state* (forward versus reverse) when updating its estimate during intermittent sensing, beyond seeing its own intended command? This does not claim that worms solve target tracking or use this exact update equation.

## Task

The controller tracks a one-dimensional target with persistent velocity. It receives noisy target-relative position on available sensor steps; sensor loss follows a Markov burst process. Its actuator has momentum and motor noise, so realized motion can diverge from the preceding command. Every learned arm receives the same three inputs: noisy relative position (zero when missing), an availability flag, and one feedback channel. The feedback is either the sign of realized actuator velocity (`SELF_STATE`), zero (`ZERO_STATE`), the sign of the preceding command (`ACTION_STATE`), or a recipient-yoked realized state (`YOKED_STATE`). The yoke preserves the batch distribution at every time point while breaking episode identity.

Training uses 32 seed blocks, the same initial weights, generated trajectories, optimizer, updates, and model size for every learned arm. Test profiles vary missing-observation burst length, dropout fraction, and target persistence. A fixed reactive controller is included as a nonlearned task-adequacy reference; it is not capacity matched. All reported endpoints remain task-specific.

## Primary endpoint and contrast

Primary profile: `LONG_BURST`. Primary metric: episode-mean squared target-relative distance, averaged within seed block. Primary contrast: `SELF_STATE − ACTION_STATE`; negative values favor feedback about realized categorical motion over the preceding intended command. Secondary contrasts compare `SELF_STATE` with `ZERO_STATE` and `YOKED_STATE`. The training seed block is the inferential unit; episodes are nested observations. Use a paired seed-block bootstrap with 20,000 draws and fixed seed 8,765,501.

## Feasibility preflight disclosure

Before freezing this full run, a six-seed preflight on the same task generator was inspected. The self-state controller outperformed the reactive reference on all six seeds, but its ranking against zero/action/yoke controls was mixed. Those outcomes are disclosed in `data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/PREPILOT.json`; the full experiment uses disjoint seeds and is classified as exploratory. No effect threshold or PASS/FAIL label is imposed.

## Interpretation

A favorable contrast would support only a conditional contribution of realized binary movement-state input in this synthetic task. It would not establish an AIY implementation, biological causality, or a general AI advantage. A null or adverse result bounds this abstraction and remains part of the evidence base.
