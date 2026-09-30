# V3 implementation and inference failure log

## Implementation failure

The first V3 launch stopped on the GRU comparator because `GRUCell` was given a one-dimensional hidden state. The process exited before writing any metrics. The code was corrected to initialize GRU hidden state with shape `[batch, hidden_size]`, then the same frozen run completed. No partial outputs from the failed launch are used.

## Inference limits

- V1 and V2 results were already known, so V3 is exploratory even though its own task ranges and primary contrast were written before the V3 run.
- The task family is scalar state estimation with synthetic context-dependent observation coefficients. Results are conditional on this generator and do not prove biological implementation.
- The aligned benefit over the bilinear RNN is materially smaller than the benefit over the additive RNN. The architecture itself matters; avoid presenting only the simplest comparator.
- A Kalman oracle that knows true episode parameters performs best in every condition. Learned models do not beat the conventional model-based reference.
- The exact condition mapping is deliberately changed at evaluation. Strong negative transfer under reversed/independent mappings is a central boundary, not a result to hide through aggregation.
- The GRU has more parameters (17) than the 4-parameter gate model; equal update counts do not imply equal compute. This is a stronger-capacity reference, not a compute-matched comparison.
- Secondary contrasts span multiple environment, mapping and baseline combinations; intervals are descriptive and are not adjusted for multiplicity. The single primary contrast was designated in the V3 contract.
- No biological recordings, animals, or intervention data were analyzed.
