# M2_BURSTY_COMPUTE_FRONTIER_V1 — limitations and failure lessons

## Findings that limit the claim

- **Strong GRU control reverses the MSE ranking.** The 321-parameter GRU had a near-tie with the four-parameter sensory-site controller at 60 updates, then improved substantially at 120 and 240 updates. The project cannot claim overall superiority or robustness against strong recurrent models from this task.
- **Equal update counts are not compute matching.** The GRU has 321 trainable parameters versus 4 in the structured controllers. Parameter count and per-update compute differ by more than 80-fold; the design reports this mismatch rather than calling the comparison capacity matched.
- **The MSE gain is metric-specific.** At the primary condition, sensory-site feedback's MSE advantage over output-site feedback coexists with worse MAE and slower post-gap recovery. Treating tracking MSE alone as overall control quality would conceal this trade-off.
- **The artificial outage regime is not a biological measurement.** Burst lengths, visibility transitions, and tracking objective were set by the simulator. The experiment does not show that these are the operating conditions of the RIM–AIY thermotaxis circuit.
- **Post-result status remains.** Earlier M2 model and synthetic results informed this task family, evaluation conditions, and controller set. Fresh seeds reduce direct reuse of random draws but do not make the study confirmatory or independent.

## Implementation issue caught during verification

The first verifier run failed because its exact-string check expected `optimizer_updates=240; visibility_q=0.125`, while the frozen contract expressed the same primary condition in prose. The contract was not changed. The verifier was corrected to check the actual frozen sentence, then rerun successfully. No outcome files or experiment results were modified as part of this correction.

## Next useful scientific step

Do not increase the seed count on this identical simulator to seek a preferred ranking. The unresolved research value is now clear: a small feedback-placement inductive bias can beat matched low-capacity controls but is dominated on MSE by a trained larger GRU. The next substantial step should test the same source-grounded computation in a task with a distinct objective and biologically interpretable motor-to-sensory contingency, while matching total FLOPs/data and reporting MSE, absolute error, energy, and switching/recovery together. If it again loses to adaptive recurrence, narrow or abandon the AI-advantage claim.
