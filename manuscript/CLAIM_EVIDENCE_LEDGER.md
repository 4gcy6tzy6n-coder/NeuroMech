# Manuscript claim–evidence ledger

Status labels: **supported** = directly supported within stated scope; **qualified** = supports a narrower claim; **open** = not established; **exclude** = do not use in current main text.

| Proposed claim | Evidence | Status | Manuscript boundary |
|---|---|---|---|
| Ji et al. support a RIM-dependent motor-state representation in AIY and a role in sustained forward thermotaxis. | Primary source paper and project source-data reanalyses. | Supported as source-literature claim; reanalysis is corroborative/retrospective. | Call it premotor/corollary-discharge-like state information, not post-actuator velocity. Do not claim new causal validation. |
| Sensory-site motor feedback improves artificial performance overall. | Placement task beats output persistence by 6.80 points but loses to no-feedback, generic RNN and Bayes. | Not supported. | State a placement-dependent local trade-off only. |
| Sensory feedback is robust to missing observations. | Bursty-observation task beats selected controls, but comparison to GRU is unresolved and frozen joint criterion failed. | Qualified. | Keep separate from telegraph task; no pooled claim or broad robustness language. |
| Biological motor-state computation transfers to AI. | Artificial tasks are simplified and several use variables not identical to source; strong comparators often match or beat structured arm. | Open. | No biological-to-AI transfer claim. Pending discriminator cannot be prewritten. |
| Source-style CF-LTD weights carry temporal information. | Within-session held-out source analysis: 15/16 > uniform, 16/16 > CF-time shuffle; ridge stronger in 14/16. | Qualified. | Modeled weight ordering; session-level prediction only, not measured synapses, causality or animal-level generalization. |
| CF-LTD abstraction improves an artificial timing system. | V2 fails frozen criterion: CF-LTD 0.1252 s; no-trace 0.1097 s; generic RBF 0.1030 s; empirical timer 0.0753 s. | Not supported for this implementation/task. | Task lacked trial-specific input about independently sampled reward jitter; do not generalize failure to biology. |
| Transfer requires preserving defining information and computation. | Inferred from task mismatch and comparator-sensitive outcomes in two heterogeneous cases. | Open, useful prospective hypothesis. | Use as organizing framework/hypothesis, not an established universal principle. |
| Project establishes a single positive NeuroAI principle or NMI-ready result. | Existing audit explicitly says no distinctive, cross-case positive AI advantage established. | Not supported. | Do not claim in abstract/title/conclusion. |
| M1 RR19 is a completed mixed result ready for integration. | Separate owner; latest actual disposition not provided in this task. | Open/out of scope. | Reserve a conditional slot only; no RR19 data or interpretation authored here. |

## Decisions required before submission

1. Add canonical M2 action-conditioned discriminator only after its complete run and independent verification; update all claims from the outcome without changing frozen criteria.
2. Request the independent M1 owner’s final, citable disposition and provenance package; preserve their authorship/ownership boundary.
3. Verify the exact Garcia-Garcia bibliographic metadata from the pinned source record.
4. Decide whether heterogeneous task studies support a full research Article or whether the contribution is better framed as a methods/resource paper. NMI fit is not established by topical scope alone.
5. Audit every number in the manuscript against canonical output tables and manifests; this draft uses values reported in result summaries.

