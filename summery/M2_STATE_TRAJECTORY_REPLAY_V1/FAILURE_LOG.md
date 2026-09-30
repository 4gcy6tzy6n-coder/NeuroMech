# Full-trajectory replay V1 limitation log

- **Residual control mismatch:** forward persistence summaries are close across noise scales, but reverse-run mean and P90 differ at noise 0.75 (`+0.784 s` and `+3.513 s`, sensory-site minus replay). No equivalence bounds were frozen; do not call the yoke exactly matched.
- **Replay scope:** the yoke preserves development mode sequences but breaks their relationship to each held-out position, heading and temperature history. The contrast indicates this relation matters in the source model; it does not identify a unique controller or biological synapse.
- **Exploratory lineage:** earlier M2, V1-yoke and V5 outcomes were known before this analysis. It is not an independent confirmatory result.
- **Model parity:** V5's source-index correction is retained, but MATLAB/Octave execution, random-number stream parity, and all smoothing-edge behavior remain unverified.
- **Inference scope:** seed-block uncertainty is for this simulation only; no animal-level biological or AI-transfer inference follows.
