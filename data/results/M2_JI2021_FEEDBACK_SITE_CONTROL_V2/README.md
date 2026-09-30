# M2_JI2021_FEEDBACK_SITE_CONTROL_V2 results

Post-result exploratory computational counterfactual using a Python port of the published Ji et al. Figure 7 model. This package contains simulation outputs only; it contains no newly collected biological data.

## Main result

On an independent 100-seed-block test split, sensory-node feedback had a higher warm-direction index than development-calibrated motor-only feedback: paired difference `+0.090275` (95% paired seed-block bootstrap CI `[+0.084015, +0.096588]`, positive in 100/100 blocks). Mean forward-run duration was closely matched: sensory feedback `4.5901 s`, motor-only `4.6251 s`; paired difference `−0.03494 s` (95% CI `[−0.10304, +0.03445]`).

## Interpretation and limits

This shows a feedback-placement difference in this implementation of the published navigation model under approximately matched mean run duration. The match is at the mean only; distributions, switching dynamics, internal states, and computational resources were not matched. This is a post-result simulation, not an independent biological test, and it does not establish that the biological circuit uniquely implements this computation or that the computation benefits AI systems.

## Reproduction

Run from repository root:

```sh
python3 model/M2_JI2021_FEEDBACK_SITE_CONTROL_V2/run_site_control.py
```

The runner records source, contract, runner, and result hashes in `run_manifest.json`.
