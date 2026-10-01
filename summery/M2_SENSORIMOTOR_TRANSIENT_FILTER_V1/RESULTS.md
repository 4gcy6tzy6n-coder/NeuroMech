# M2_SENSORIMOTOR_TRANSIENT_FILTER_V1 — results

**Run date:** 2026-10-01  
**Classification:** post-result exploratory artificial mechanism-transfer test; the within-study protocol was frozen before execution. This is not independent confirmation, biological validation, or evidence of a general AI benefit.

## Question and scope

Motivated by Ji et al.'s report that RIM-dependent motor-state feedback contributes to AIY sensory processing and sustained forward movement, this synthetic test asked whether placing actual motor-state feedback in a sensory-state update suppresses brief contradictory sensor pulses better than placing the feedback term at the output. The source motivates the question but does not specify this model, task, or expected AI performance. [Ji et al., eLife 2021](https://elifesciences.org/articles/68848)

The experiment used 20 paired training/task seed blocks, five fitted models, two evaluation-only references, five test conditions, and 64 episodes per seed/model/condition: 44,800 episode-arm rows and 100 fitted model records. The primary outcome was pulse-window movement MAE, averaged over the union of eligible pulse and two-step post-pulse samples within each episode, then across episodes within a seed block. Uncertainty was bootstrapped over the 20 paired seed blocks.

## Primary result

The primary contrast was `OUTPUT_SITE_1D − SENSORY_SITE_1D`; positive values would favor sensory-site feedback. Instead, the mean contrast was **−0.0921 movement units**, with a 95% paired seed-block bootstrap interval of **[−0.1081, −0.0766]** (`n=20`). Thus output-site feedback had lower pulse-window MAE than sensory-site feedback in this task.

| TRANSIENT_PULSE arm | Pulse-window MAE, mean (95% seed-block bootstrap CI) | Whole-episode movement MAE |
|---|---:|---:|
| SENSORY_SITE_1D (4 parameters) | 0.6458 [0.6338, 0.6578] | 0.4681 |
| OUTPUT_SITE_1D (4 parameters) | 0.5537 [0.5384, 0.5700] | 0.3890 |
| NO_FEEDBACK_1D (3 parameters) | 0.7228 [0.7055, 0.7423] | 0.4876 |
| GENERIC_RNN_1D (6 parameters) | 0.6502 [0.6398, 0.6609] | 0.4660 |
| GRU_8 (297 parameters) | 0.7138 [0.7070, 0.7203] | 0.3517 |
| DIRECT_SENSOR (fixed, no fitting) | 0.7265 [0.7220, 0.7309] | 0.3396 |
| TARGET_ORACLE (privileged target access) | 0.0605 [0.0589, 0.0621] | 0.1177 |

Among the learned arms, the output-site model had the lowest primary error. The no-feedback model's worse pulse-window score than both feedback-placement models is compatible with a benefit from adding motor feedback in this particular simulator, but the experiment's primary hypothesis concerned **where** feedback enters, and that contrast favored output placement. The privileged oracle is an upper reference that sees the hidden target; it is not a fair learned comparator. Equal training updates do not equate compute, and the GRU has far more parameters.

For completeness, the table reports mean movement MAE for every model and evaluation condition. The fixed direct-sensor and privileged oracle references are included but are not trained comparisons.

| Arm | Clean stable | Transient pulse | Long pulse | Sustained switch | Combined stress |
|---|---:|---:|---:|---:|---:|
| SENSORY_SITE_1D | 0.3547 | 0.4681 | 0.4857 | 0.5555 | 0.7070 |
| OUTPUT_SITE_1D | 0.2581 | 0.3890 | 0.4063 | 0.5125 | 0.6764 |
| NO_FEEDBACK_1D | 0.3474 | 0.4876 | 0.4905 | 0.5443 | 0.7017 |
| GENERIC_RNN_1D | 0.3500 | 0.4660 | 0.4843 | 0.5508 | 0.7051 |
| GRU_8 | 0.1634 | 0.3517 | 0.3466 | 0.4025 | 0.6058 |
| DIRECT_SENSOR | 0.1509 | 0.3396 | 0.3368 | 0.3858 | 0.5948 |
| TARGET_ORACLE | 0.1187 | 0.1177 | 0.1178 | 0.3024 | 0.3034 |

Pulse-window MAE across all conditions is reported below. `CLEAN_STABLE` has no pulse windows, so this endpoint is undefined there.

| Arm | Clean stable | Transient pulse | Long pulse | Sustained switch | Combined stress |
|---|---:|---:|---:|---:|---:|
| SENSORY_SITE_1D | — | 0.6458 | 0.8533 | 0.6523 | 0.9435 |
| OUTPUT_SITE_1D | — | 0.5537 | 0.7570 | 0.5826 | 0.8828 |
| NO_FEEDBACK_1D | — | 0.7228 | 0.9223 | 0.7078 | 0.9871 |
| GENERIC_RNN_1D | — | 0.6502 | 0.8630 | 0.6528 | 0.9491 |
| GRU_8 | — | 0.7138 | 0.9594 | 0.6906 | 1.0276 |
| DIRECT_SENSOR | — | 0.7265 | 0.9802 | 0.7046 | 1.0460 |
| TARGET_ORACLE | — | 0.0605 | 0.0528 | 0.1004 | 0.0809 |

All secondary model-by-condition summaries (movement MSE, state accuracy, command energy, and switch latency) are retained in `summary.json`; seed-block values are in `seed_summary.csv`.

Secondary results do not show that sensory-site placement preserves a general switch advantage. In `SUSTAINED_SWITCH`, sensory-site mean switch latency was 3.06 steps versus 3.42 for output-site feedback, but whole-episode MAE was 0.556 versus 0.513. In `COMBINED_STRESS`, whole-episode MAE was 0.707 for sensory-site and 0.676 for output-site. These are descriptive secondary outcomes, not replacements for the primary endpoint.

## Interpretation boundary

This run **does not support** the tested claim that sensory-site motor feedback is superior for rejecting brief contradictory sensory pulses. It does not refute the biological finding that motor-state feedback in the C. elegans circuit supports persistent behavior: the model omits the identified neurons, circuit dynamics, biological perturbations, and measured animal behavior. It tests one hand-specified artificial translation with a synthetic pulse generator and actuator. Parameter matching between the two scalar models does not guarantee equal expressivity or equal optimization, and the test does not establish an AI benefit beyond this simulator.

## Reproducibility and artifacts

- The frozen contract, runner, verifier, and preflight manifest were committed before execution in `9f70f60`.
- The independent verifier passed: 44,800 unique episode-arm rows, 100 fit records, 700 seed summaries, manifest hashes, and recomputed primary contrast/bootstrap.
- A separate full run reproduced `episode_metrics.csv`, `seed_summary.csv`, and `summary.json` byte-for-byte. Fit parameters, training losses, and protocol metadata matched; wall-clock timing differed as expected.
- Environment: Python 3.12.13, NumPy 2.4.4, PyTorch 2.11.0, CPU, one Torch thread.

See [the frozen contract](CONTRACT.md), [failure log](FAILURE_LOG.md), [runner and verifier](../../model/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/), the [canonical outputs](../../data/results/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/canonical/), and the [validation manifest](../../data/results/M2_SENSORIMOTOR_TRANSIENT_FILTER_V1/VALIDATION_MANIFEST.json).
