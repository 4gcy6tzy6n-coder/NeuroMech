# Failure log and limitations

- This is a source-model reproduction/stress test after the published Figure 7 outcome was known. It cannot be described as blind confirmation or novel biological evidence.
- MATLAB/Octave is unavailable, so the author MATLAB script was translated to Python. The state equations and model constants were ported, but MATLAB's `smooth(M,4)` edge convention is approximated by a documented four-sample moving average.
- The source MATLAB does not declare a random seed. We used 100 independent seed blocks and common random numbers across feedback/noise conditions; numerical figure values are not expected to match the authors' original random realization exactly.
- Bootstrap uncertainty is only Monte Carlo uncertainty over this simulator. Fifty agents in each seed block are clustered, not 5,000 independent biological subjects.
- The noise multipliers 0.5× and 2× are arbitrary stress conditions; the paper does not establish a biological sensory-noise variance corresponding to them.
- Strong positive feedback raises persistence and may delay switching after a true state reversal. This task reports warm-gradient run direction and displacement, not a balanced adaptation-versus-persistence utility over arbitrary environments.
- No learned or parameter-matched generic controller is included, so this experiment makes no claim of AI superiority or useful artificial inductive bias.
- The published supplementary script contains plotting variables/functions from a larger MATLAB workspace; only the state update/navigation logic needed for this experiment was translated. Full Figure 7 reproduction is not claimed.
