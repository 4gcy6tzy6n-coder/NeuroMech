# Ji et al. Figure 7 positive-feedback model: reproduction and noise stress test

**Status:** `POST_RESULT_EXPLORATORY_SOURCE_MODEL_REPLICATION`. This reproduces a published computational result qualitatively and adds a synthetic sensory-noise stress sweep. It is not a new biological result, an independent replication of the biological experiments, or an AI-transfer test.

## Result

At the author-code noise scale (`noise_scale=1`), positive feedback (`fb=+1`) produced mean warm-direction index `0.5652`, compared with `0.1498` without feedback and `0.0433` under negative feedback (`fb=−1`). The paired positive-minus-no-feedback difference was `+0.4154` (95% simulation-seed-block bootstrap interval `[+0.4083,+0.4226]`; positive in all 100 blocks). Mean forward-run duration was `4.53 s` with positive feedback, `0.91 s` without feedback, and `0.56 s` with negative feedback. Mean final warm-axis displacement was `34.78`, `7.04`, and `1.82` model units, respectively.

The result is qualitatively consistent with the authors' Figure 7 interpretation that positive motor-to-interneuron feedback stabilizes a forward state and supports migration toward the warm side. The run-length/direction outcomes are model output, not measured worm outcomes.

## Noise stress

The positive-minus-no-feedback warm-direction-index contrast decreased as the source Gaussian sensory-noise term was scaled upward: `+0.8027` at 0.5× (95% interval `[+0.7837,+0.8219]`), `+0.4154` at 1×, and `+0.1219` at 2× (`[+0.1181,+0.1257]`). The direction index remained positive for the positive-feedback arm at all three scales (`0.8605`, `0.5652`, `0.2524`). These scales were set as engineering stress conditions and do not estimate biological noise or define an in vivo operating range.

## Interpretation

This round clarifies why the earlier scalar-action-feedback pilots were not faithful implementations of the published mechanism: the source model couples a continuous interneuron-like state and motor-like state through a saturating feedback term, while sensory drive and motor output are separate nonlinear stages. In this translation, stronger positive feedback produces longer forward states and better directional migration under the authors' task generator. The operation is consistent with a hysteretic/stabilizing computation, but the particular equation is a model abstraction, not an observed biological update rule.

The very narrow intervals quantify only Monte Carlo variability across the chosen simulation seeds. They are not biological uncertainty intervals. The stress test changes only a synthetic noise multiplier and does not test generalization to other tasks. No generic learned recurrent controller, resource-matched non-feedback state model, or artificial benchmark is included; therefore no AI benefit is established.

## Implementation and integrity

The runner translates the official MATLAB Figure 7 script's Euler state updates, movement-state-dependent heading transitions, delayed position-difference thermal input, and author parameter values. It uses 100 paired simulation-seed blocks × 50 agents, 1,500 steps per trajectory, three feedback coefficients, and three noise scales, yielding 900 metric rows. MATLAB is unavailable in this environment; run segmentation uses a centered four-sample moving average with truncated, renormalized edges, which may differ slightly from the MATLAB `smooth` edge convention. The contract, author-source hashes, software versions, result hashes, and seed design are in `M2_JI2021_FEEDBACK_DYNAMICS_CONTRACT.md` and `../../data/results/M2_JI2021_FEEDBACK_DYNAMICS/run_manifest.json`.

## Next scientific question

The next experiment should determine whether this feedback computation contributes more than generic state inertia under matched dynamics and resource use, and whether any advantage survives held-out tasks that require both persistence and rapid switching. It must compare against a learned generic recurrent controller and include a task-optimal reference. This result alone does not answer that question.
