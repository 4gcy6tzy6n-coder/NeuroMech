# Results — M2 AIY premotor-state prediction V1

**Outcome:** `PARTIAL / PRIMARY GROUP CONTRAST NOT ESTIMABLE`.

Under the frozen strict-label definition (all samples in the forecast window must be labeled `+1` or `−1`), the 2-second primary target produced 6–18 positive samples per WT animal but zero positive samples in each of the five RIM-ablated animals. WT AIY incremental AUC averaged `0.1675` (animal values `0.3061, 0.1862, 0.1288, 0.2015, 0.0151`), but the WT–RIM group comparison cannot be calculated. No group-level biological conclusion follows.

This is a failed target-definition attempt rather than a null neural effect. The 20-second purged blocked-CV model cannot estimate AUC when a cohort has no positive scored outcomes. The source's transition/unknown state `0` was excluded from the whole future horizon, removing reversal examples in the RIM cohort. The output now records the group as `NOT_ESTIMABLE_NO_SCORED_ANIMALS`; no NaN estimate is treated as zero.

V1 is retained unchanged as a transparent failure record. V2 separately defines the target as the next known state within a fixed horizon while skipping transition/unknown labels; it is an outcome-informed exploratory follow-up on the same animals, not a repair that upgrades V1.
