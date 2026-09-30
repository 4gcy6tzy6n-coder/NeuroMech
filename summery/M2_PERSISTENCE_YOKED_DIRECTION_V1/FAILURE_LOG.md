# V1 failure and limitation log

- **Control adequacy failure:** development bout-duration resampling did not reproduce held-out source-model persistence adequately at noise 0.75. Mean forward duration differed by `0.609 s`, P90 by `2.623 s`, ≥30-second fraction by `0.00878`, and forward occupancy by `−0.01495` (sensory-site minus yoke). The all-scale primary cannot be treated as a clean matched-control estimate.
- **No frozen equivalence bounds:** V1 is retrospective and did not define match tolerances before the analysis. Even close values at scales 1.00 and 1.25 are descriptive, not equivalence claims.
- **Yoke scope:** sampled bout lengths are independent of position, heading, temperature and within-trajectory serial context. This is a marginal-duration null, not a biologically complete motor-feedback circuit.
- **Model provenance:** prior M2/V3/V4/V5 outcomes were known. Conclusions are exploratory source-model findings, not animal-level inference, a unique synaptic mechanism, or AI transfer.
- **Numerical parity:** the MATLAB delay index is corrected, but no MATLAB/Octave execution was available; RNG and smoothing-boundary parity remain unverified.
- **Implementation incident:** first run aborted before result CSV/summary serialization due to unequal arm fields. Output schema was fixed, same frozen seeds were rerun, and the completed output passed independent verification. No first-attempt held-out results were analyzed.
- **Next repair:** use complete development forward-state trajectories as a yoke, preserving bout sequence and horizon censoring; predefine a held-out persistence-adequacy report before interpreting direction metrics.
