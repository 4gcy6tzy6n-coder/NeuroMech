# M2 feedback-site counterfactual: sensory-node feedback vs motor-only persistence

**Status:** `POST_RESULT_EXPLORATORY_COMPLETE_WITH_IMPERFECT_MATCH`. This is a model counterfactual after the source-model positive-feedback outcome was already observed; it is not a biological experiment or AI-transfer test.

## Calibration and held-out result

On 30 development seed blocks, the source sensory-node-feedback model's mean forward-run duration was `4.429 s`. The motor-only persistence term was evaluated on the frozen grid from 0.0 to 1.0 by 0.1. The selected coefficient was `0.7` (mean run duration `3.948 s`); the next grid value, `0.8`, jumped to `9.356 s`, so the coarse grid could not closely match the source arm.

On 100 new test seed blocks, the warm-direction index was `0.5706` for sensory-node feedback, `0.4539` for motor-only persistence (`motor_fb=0.7`), and `0.1540` with no feedback. The paired sensory-site-minus-motor-only difference was `+0.1166` (95% seed-block bootstrap interval `[+0.1091,+0.1241]`, positive in all 100 blocks). Mean forward-run durations were `4.572 s`, `4.033 s`, and `0.918 s`, respectively. Mean final warm-axis displacements were `34.54`, `26.56`, and `6.18` model units.

## Analysis and failure lesson

The sensory-site-feedback model navigated more effectively than the selected motor-only control in this source-model task. However, the control did not match mean run duration in development or held-out seeds, and the difference increased slightly in the held-out set. Therefore the primary contrast does not isolate feedback location from the amount and distribution of motor persistence. Do not claim that sensory-site feedback is uniquely necessary based on this run.

The coarse calibration grid crossed a steep, bistable transition: mean motor-only run duration rose from `3.95 s` at coefficient `0.7` to `9.36 s` at `0.8`. This suggests a more precise development-only calibration and a fresh held-out test are needed before interpreting the feedback-site contrast. The current held-out results are frozen; they were not used to refine the coefficient.

All results are model simulations, not biological-population estimates. They do not establish that RIM feedback has this exact equation, nor that the computation benefits AI. The independent unit is the simulation seed block, with 50 agents clustered within it.

## Reproducibility

The run used a fixed 30-block development set, a disjoint 100-block test set, common random streams within each set, and a paired 20,000-resample bootstrap. `run_manifest.json`, `development_calibration.csv`, `heldout_simulation_metrics.csv`, and `POSTRUN_VERIFICATION.json` preserve calibration, test, and arithmetic verification. The runner and contract hashes are recorded in the manifest.

## Next experiment

Use a finer calibration grid or a development-only root-finding procedure near the transition, freeze the selected coefficient before opening a new set of test seeds, then compare both warm-direction index and the held-out run-duration distribution. If the matched control still fails to reproduce sensory-site behavior, test switch latency and response to cooling explicitly before claiming site-specific computational value.
