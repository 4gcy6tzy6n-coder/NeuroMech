# M5_ELIGIBILITY_TRUNCATED_BPTT_V1 — failure log

## Preflight fixes

The initial runner preflight caught an input-weight eligibility shape error in the `NO_TRACE` arm. The update gradient was corrected to form the local hidden signal first, then take its outer product with the current input and prior hidden state. A finite-difference check of full BPTT then passed with maximum absolute error `1.31e−10`, and all five update rules produced finite losses and gradients. No outcomes were computed before the corrected preflight.

## Experimental result

Eligibility beat the no-trace local update but fell far below TBPTT-4 (`0.6974` versus `0.9633`; paired difference `−0.2659`, 95% CI `[−0.3295, −0.2003]`) and full BPTT (`0.9996`). Thus a local trace did not substitute for a short recurrent gradient on this task. The full-BPTT reference passed the frozen viability check, so this is an interpretable negative comparison rather than a task-failure result.

## Lessons

- A strong truncated recurrent gradient can retain enough performance even when its gradient path to the first cue is cut; comparing only to a no-trace local update exaggerates the trace's algorithmic standing.
- Preserve the local-trace versus no-trace contrast, but do not frame it as evidence of advantage over recurrent learning methods.
- The observed wall-time reduction is modest and implementation-specific; report it alongside the accuracy gap rather than treating it as proof of efficiency.
- The temporal XOR task is narrow and post-result. Do not claim this result generalizes to tasks where BPTT is infeasible or biologically implausible.
