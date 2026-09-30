# Failure and limitation log — M2_JI2021_FEEDBACK_SITE_CONTROL_V2

- **Not a biological replication:** all outputs are from a Python implementation of the published Figure 7 model; no animal observations were generated or analyzed.
- **Post-result follow-up:** this addresses the V1 control mismatch and is exploratory, not an independent confirmatory preregistration.
- **Mean-only control matching:** the motor-only parameter was chosen to match development-set mean forward-run duration. The held-out mean difference was small and its paired 95% interval included zero, but run-duration distributions and other dynamics remain unmatched.
- **Model implementation limitation:** moving-average edge behavior is a Python approximation; MATLAB/Octave parity was not checked in this environment.
- **Mechanism interpretation limit:** persistence of the contrast does not establish that biological sensory feedback is the sole or unique causal mechanism, nor does it establish transfer to artificial systems.
