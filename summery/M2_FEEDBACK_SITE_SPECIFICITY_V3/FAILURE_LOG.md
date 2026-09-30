# M2 feedback-site specificity robustness V3 — failure and limitation log

- **Outcome-informed:** V1/V2 results were known before V3 was specified. The new seed blocks provide a fresh simulation sample, not an independent confirmatory biological test.
- **Model only:** outputs come from a Python implementation of the published Figure 7 model; no worm recordings or behavior were generated or analyzed.
- **Mean-only calibration:** the motor-only control was calibrated to mean forward-run duration. Median duration, upper-tail duration, forward occupancy, run counts, switching latency, and internal trajectories were not matched. The observed warm-direction difference therefore cannot be uniquely assigned to sensory-site placement.
- **Held-out mismatch remains:** at noise multiplier 1.25, the mean-duration difference was small but its 95% seed-block interval excluded zero (−0.036 s, [−0.059, −0.015]). The primary contrast was not adjusted or selected using this secondary result.
- **Synthetic noise boundary:** multipliers 0.75/1.00/1.25 are imposed in the model and do not establish that locomotor state predicts sensory reliability in the animal.
- **Implementation parity:** the Python implementation's numerical parity with the authors' MATLAB/Octave implementation was not independently verified.
- **Claim boundary:** this experiment does not establish a unique biological causal carrier, animal-level effect, connectome contribution, general-purpose AI benefit, or publication readiness.
