# Failure log — M2 AIY premotor-state prediction V1

- **Failure:** strict complete-label future windows yielded no positive primary examples in any RIM-ablated animal.
- **Cause:** source label `0` denotes transition/unknown samples. Requiring all future samples to be known `+1/−1` discarded intervals that included these transition labels.
- **Impact:** RIM-group AUC and the primary WT-minus-RIM contrast were not estimable. Do not call the RIM effect zero, do not pool frames as replicates, and do not drop the group silently.
- **Repair path:** V2 treats `0` as interval-censored and uses the next known state within the same fixed horizon. V2 is explicitly post-result exploratory and retains a new ID and record.
- **Operational correction:** the first run emitted `NaN` summary values for an empty group. The result serializer now emits explicit `null` fields with `NOT_ESTIMABLE_NO_SCORED_ANIMALS`; the underlying scored rows and WT estimates did not change.
