# Failure log — DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1

- The initial `SHUFFLED_COUNTEREVIDENCE` control permuted the candidate feature in training but not test. That version had a train/test feature-distribution mismatch and is excluded. The final run permutes both splits independently within coverage/profile strata.
- scikit-learn `lbfgs` emitted divide-by-zero/overflow warnings on this feature design. The run was repeated with `liblinear`, which optimizes the same frozen L2 logistic objective. The final execution passed with warnings treated as errors and all coefficients/predictions finite.
- The apparent primary gain is not evidence of an AI advantage: the synthetic generator directly makes the textured stationary feature class-discriminative. It is a cue-sufficiency manipulation check.
- The model fails sharply when stationary texture is removed or flickers. On those counterfactual profiles its object-motion false-positive rate is approximately 99–100%. The learned cue is brittle and overconfident under the tested shift.
- The task uses generated local-motion feature summaries rather than pixel sequences. No natural-image model, optical-flow baseline, real-world dataset, or architecture-matched learned vision control was tested.
- The author paper already contains ANN evidence for this computation. No novelty claim is made for reproducing the core concept.
