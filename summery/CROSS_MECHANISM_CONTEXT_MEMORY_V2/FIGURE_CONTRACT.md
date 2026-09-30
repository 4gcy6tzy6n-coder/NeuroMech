# Figure contract — CROSS_MECHANISM_CONTEXT_MEMORY_V2

## Core conclusion

The V2 benchmark does not support one shared mechanism-specific performance advantage: trained GRUs outperform the small M2 context-gain filter, while the M5 eligibility trace improves over a latest-input cache only at short/intermediate delays and remains below exact FIFO memory.

## Figure question and evidence roles

**Question:** Which comparisons bound the apparent benefits in the two artificial tasks?

- **Panel a (M2):** paired seed-block MSE contrasts for both GRUs against the context-gain filter across aligned, independent, and reversed context mappings. Zero denotes no contrast; negative values favor the GRU.
- **Panel b (M5):** paired seed-block accuracy contrasts for eligibility against equal-state latest-input memory and exact FIFO across four delays. Zero denotes no contrast; positive favors eligibility.

Panel outcomes use different units and opposite favorable directions, so they receive separate axes, labels, and annotations. The panels must not be pooled or visually encoded as one common effect scale. All 32 task-seed blocks are displayed; means and 95% seed-bootstrap intervals are over seed blocks. Bootstrap intervals are descriptive, not confirmatory inference, because the benchmark is post-result exploratory.

## Archetype, output and risks

- Archetype: two-panel quantitative comparison with distinct task-native estimands.
- Target: NMI review-stage evidence figure; also export editable vector files and high-resolution raster for later production adaptation.
- Width: 180 mm, with aligned panel plot areas and a readable minimum 5 pt text floor.
- Required files: Python source, PDF, SVG, PNG, panel-alignment audit JSON, PDF text audit, collision audit, and the exact plotted source-data CSVs.
- Main reviewer risks: M2 parameter mismatch; M5 FIFO's delay-dependent state cost; distinct metrics/sign conventions; and post-result protocol status. These are stated in panel labels or legend and in the results record.

## Source and exclusions

Use all 32 seed blocks for each M2 mapping and M5 delay from the corrected canonical CSVs. No data rows are excluded. No biological outcome, biological validation, combined score, or confirmatory claim is represented.
