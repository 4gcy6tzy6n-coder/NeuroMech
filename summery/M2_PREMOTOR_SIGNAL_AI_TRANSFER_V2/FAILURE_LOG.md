# Failure and limitation log — M2 premotor predictive-signal transfer V2

- The biologically motivated six-parameter forecast-fusion update did not beat a six-parameter generic recurrence or the 45-parameter GRU on the aligned primary condition.
- The generic model's predictive cue benefit was larger (`+0.1762` vs `+0.1053` over each model's no-cue ablation). This rejects a unique performance advantage for the tested fusion placement under aligned conditions.
- The constrained filter was less damaged by uninformative/reversed cue mapping, but still scored below its no-cue ablation. This is a robustness trade-off, not an overall win.
- The simulator grants models a synthetic cue that directly predicts the future label; it is not calibrated from biological population traces and cannot establish biological-to-AI transfer.
- The models are small recurrent estimators on a generated binary process. No independent task family, real-world benchmark, energy measurement, or biological perturbation was tested.
- The verifier checked output integrity and contrast arithmetic from episode rows, not an independent retraining implementation. V1 and V2 are exploratory, outcome-informed results.
