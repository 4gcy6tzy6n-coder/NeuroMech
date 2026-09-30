# M2 decision-task context-information dose response — contract

**Experiment ID:** `M2_DECISION_CONTEXT_DOSE_V1`  
**Classification:** exploratory artificial objective-transfer study; prior M2 results, including the sequential-decision experiment, are known. This is not confirmatory evidence or biological validation.

## Question

Does the context-information boundary found in continuous state estimation also appear when the same state-conditioned update must accumulate noisy evidence for a terminal choice?

## Task and data

Each trial has a fixed hidden target `s∈{-1,+1}` and 32 observations. A binary context `q[t]∈{-1,+1}` switches with probability 0.25. Observation is `y[t]=(0.18*s)*(0.5+κ*q[t])+0.7*ε[t]`. Training uses only `κ=+0.50`; test evaluates `κ∈{-0.50,-0.40,...,+0.50}`. The mean observation coefficient is 0.5 at every dose in expectation; κ changes how much the context predicts the current evidence channel.

Use 30 paired training seeds `74000..74029`; nested training-set sizes `{64,256,1024}`; 250 Adam updates with minibatch size 16 for every learned fit; 256 test trials per seed; and a 32-step horizon. Models share each seed's training pools, minibatch-index streams, and test target/context/noise innovations across all κ values and policies. The seed is the independent training replicate; trial is the paired evaluation unit.

## Models

`MODE_GAIN_FILTER` (4 parameters) is the state-conditioned prediction-error update; `CONSTANT_GAIN_FILTER` (3 parameters) is its direct context-free ablation; `LINEAR_BILINEAR_RNN` (5 parameters) is a learned recurrent comparator that can represent input-by-context interaction; `BAYES_ORACLE` is an analytical reference with the exact test mapping and likelihood. The oracle is not capacity matched.

## Outcomes and analysis

Primary metric is terminal binary accuracy. The primary contrast is `accuracy(MODE_GAIN_FILTER) - accuracy(CONSTANT_GAIN_FILTER)`, averaged equally over training sizes. Report the complete κ curve and per-size estimates. Crossed bootstrap resamples training seeds and paired trial IDs together (10,000 percentile draws; fixed seed 20261017). Also report bilinear and Bayes references, terminal MSE, and Brier score. Positive primary contrast favors mode gain. No pooling with continuous-estimation MSE is allowed.

## Interpretation boundary

This tests objective transfer of the artificial context-conditioned update and whether its dose boundary persists for decisions. The context/evidence relation and κ scale are synthetic and are not measured RIM–AIY properties. A result can characterize this model and task only; it cannot establish biological-to-AI transfer, a universal AI principle, or generalization beyond the tested decision family. All results are exploratory.
