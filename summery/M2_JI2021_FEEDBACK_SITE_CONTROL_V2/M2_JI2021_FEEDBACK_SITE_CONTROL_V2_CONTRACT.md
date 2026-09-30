# M2_JI2021_FEEDBACK_SITE_CONTROL_V2 — fine-grid motor-persistence calibration

**Status:** post-result exploratory follow-up to V1. V1 showed the 0.1-step motor-only calibration grid did not closely match forward-run duration. This V2 uses an independent development/test seed split and finer frozen grid before evaluating a new test set.

## Question

After more precise development-only calibration of motor-only persistence, does sensory-node feedback retain a warm-navigation advantage over that control on independent test simulations?

## Arms and calibration

- `SENSORY_SITE_FB`: source-model feedback term `fb=+1` in the interneuron equation, no extra motor feedback.
- `MOTOR_ONLY_MATCHED`: `fb=0`, and motor-only feedback coefficient selected from `0.700` through `0.800` in steps of `0.001`. Select the coefficient minimizing the absolute difference in development-set mean forward-run duration from `SENSORY_SITE_FB`; ties choose the smaller coefficient.
- `NO_FEEDBACK`: `fb=0`, motor-only feedback `0`.

Development seeds are 204000–204029; test seeds are 204100–204199. No test outcome may be used to alter the selected coefficient. The model otherwise retains the source parameters, 50 agents per seed block, 1,500 steps, and author noise scale.

## Outcomes

Primary: paired held-out warm-direction index difference, `SENSORY_SITE_FB − MOTOR_ONLY_MATCHED`. Secondary: held-out mean forward-run duration and final warm-axis displacement. The analysis unit is simulation seed block (50 agents clustered within it); use 20,000 paired percentile bootstrap resamples.

## Limits

The experiment is post-result and simulation-only. Matching mean run duration does not match run-duration distribution, switching latency, internal state, compute cost, or biological identity. A surviving difference is model-specific and does not establish a unique biological computation or AI benefit.
