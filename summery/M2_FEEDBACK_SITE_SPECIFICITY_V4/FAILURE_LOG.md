# M2 V4 failure and limitation log

- **Main control failure:** development-only calibration minimized a standardized four-summary loss but did not meet a prespecified equivalence criterion (none was defined). Held-out mean and tail run durations remained different at every tested noise scale.
- **Calibration limitation:** one scalar motor-feedback coefficient was asked to fit four summaries of a nonlinear closed-loop process. The optimizer returned the least-bad grid value, not a demonstrated match.
- **Interpretation risk:** the primary warm-direction contrast was larger than V3, but this is not stronger mechanistic evidence. The comparator changed and remained mismatched.
- **Scope:** simulation seed blocks support uncertainty only for this Python source-model implementation and these imposed noise conditions. No animal-level or artificial-system inference is supported.
- **Provenance:** this was designed after reviewing earlier M2 and V3 results; it is retrospective and exploratory.
- **Next methodological repair:** if continuing this line, use a separate development-derived yoke of the full state-duration process and freeze a match-adequacy check before the next held-out run. Otherwise retain the bounded difference and do not call it a feedback-site-specific causal effect.
