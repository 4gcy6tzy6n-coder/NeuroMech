# Figure contract — M5 delayed-reward bandit memory frontier

**Question:** How does held-out expected reward change with additional active credit-assignment state as delayed reward grows from one to 64 decisions?

**Core conclusion to preserve:** the fixed 32-value trace beats current-score assignment but is not on the best-reward frontier; when a FIFO stores enough exact gradients to cover the delay it reproduces full replay and exceeds the trace, while smaller equal-state or constrained FIFOs can lose because they drop most delayed updates.

**Archetype:** four aligned small-multiple accuracy/state plots, one panel per frozen delay (`D=1,4,16,64`). Each panel uses identical x/y scales and shows seed means with 95% task-seed bootstrap intervals. Exact FIFO is the memory frontier; the eligibility trace is highlighted, current-score control is muted, and exact replay is marked where it coincides with a FIFO whose capacity covers the delay.

**Data:** canonical task metrics and update coverage; 30 independent task seeds per delay. Each arm mean uses the same task-seed bootstrap definition. State accounting uses active score values, not measured RAM. When FIFO capacity is at least D, a duplicate point is collapsed and explicitly shown as the capacity-sufficient FIFO/exact-replay point because independent verification establishes exact outcome equality.

**Risk control:** no inference from overlapping confidence intervals and no biological or general-AI claim in the figure. A figure note states that FIFO update coverage is limited when capacity is below delay and that intervals resample task seeds.

**Export:** NMI-oriented vector PDF and editable SVG, plus 600-dpi PNG/TIFF. Final canvas 183 mm wide; labels target 5–7 pt. Keep figure source, derived plotting data, alignment manifest, PDF text audit and collision audit beside the canonical outputs.
