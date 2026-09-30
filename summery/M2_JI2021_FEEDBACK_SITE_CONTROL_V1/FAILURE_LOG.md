# Failure log

- The motor-only controller was not closely matched to the sensory-site model's forward-run duration. With the frozen 0.1 grid, `motor_fb=0.7` was nearest on development seeds, but its held-out mean duration was 4.03 s versus 4.57 s for sensory-site feedback.
- The motor-only duration response has a steep jump between coefficients 0.7 and 0.8, reflecting bistability. Coarse-grid selection is inadequate for a strong feedback-site claim.
- The positive warm-direction contrast is therefore confounded by imperfect persistence matching. Preserve as exploratory evidence only; do not retune against the held-out seed outcomes.
- The comparison adds a motor persistence parameter in a different equation location. Parameter count is similar, but dynamical effects, switching distributions, and computation/energy are not matched.
- This is a source-model counterfactual, not direct evidence about synaptic feedback location in the worm and not evidence of AI benefit.
