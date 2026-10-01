# Figure contract

Create one two-panel, editable vector figure from canonical seed-level summaries.

- **Panel A:** mean tracking MSE for five arms across the four prespecified actuator-reversal probabilities. Show training-seed-block uncertainty; identify the reactive policy as a non-capacity-matched reference.
- **Panel B:** paired `ACTION_STATE − SELF_STATE` MSE contrast by reversal probability, with 95% seed-block bootstrap intervals and a zero reference line. Positive favors realized-state input.
- Use only canonical outputs; do not display pilot values as inferential results. Keep the nonmonotonic pattern visible.
- Export SVG and PDF plus 600-dpi TIFF. Labels must state synthetic task and MSE; captions must state exploratory status and seed-block unit.
