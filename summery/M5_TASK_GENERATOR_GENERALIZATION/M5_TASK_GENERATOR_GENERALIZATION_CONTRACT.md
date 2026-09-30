# M5 cross-generator delayed-teaching validation

**Status:** `POST_RESULT_EXPLORATORY_CONTRACT_FROZEN_BEFORE_RUN`. The original M5 eligibility result was already inspected. This is an outcome-informed, independent follow-up, not a confirmatory or preregistered result.

## Question and scope

Does the fixed, norm-matched eligibility trace that helped over `NO_TRACE` in the original IID Gaussian task retain that advantage under other input-stream generators, with its hyperparameters unchanged?

This tests robustness of one artificial delayed-label operation across three prespecified input generators. It does not test biological outcomes, new circuits, arbitrary AI tasks, or a causal cerebellar learning rule. The generator families are three fixed conditions, not a random sample of all tasks.

## Fixed task components

- 32-dimensional input, 64-dimensional random `tanh` feature map, and four output classes.
- Each generated task has a fresh random projection and a fresh four-class linear teacher defined in the 64-dimensional feature space. The same task teacher labels its train and held-out test streams.
- Features are L2-normalized. The student is the same zero-initialized 64×4 linear softmax readout in every arm.
- 3,000 training cues, 1,000 held-out cues, ordered labels delayed by `D ∈ {1, 4, 16, 64}` steps.
- Thirty task seeds per generator. Each seed has a unique projection, teacher, train stream and test stream.
- Learning rate `0.01`, eligibility decay `γ=0.98`, no hyperparameter search, and no result-guided modifications.

## Prespecified input generators

1. `IID_GAUSSIAN`: independent standard-normal input vectors. This reproduces the original M5 input-generator family for continuity, with new task seeds.
2. `AR1_GAUSSIAN`: stationary Gaussian inputs with within-stream lag-one coefficient `0.8`; train and test streams are independently generated. The teacher and feature map remain fixed within a task.
3. `SPARSE_SIGN`: independent inputs whose coordinates are zero with probability `0.8`, otherwise `±1/sqrt(0.2)` with equal probability. This gives unit marginal variance with sparse observations. Train and test streams are independently generated.

These conditions vary the temporal and marginal input statistics while retaining the same learnable teacher/readout relation. The result therefore supports generalization across these input generators only, not across unrelated task objectives.

## Fixed arms

1. `EXACT_REPLAY`: apply each delayed label error to that cue's stored feature vector; higher-memory online reference.
2. `ELIGIBILITY_TRACE_NORM_MATCHED`: at each step maintain `e_t=0.98e_(t−1)+φ_t`; when the delayed label arrives, use `e_t/||e_t||` with the prediction error stored for the labeled cue. This arm is unchanged from M5-v3.
3. `NO_TRACE`: apply the delayed label error to the current cue feature. During post-stream label delivery, the current feature is zero, matching the existing implementation's end-of-stream convention.

All arms have the same trainable readout parameters and receive the same generated train/test task. Exact replay retains cue features and is not memory-matched; it is a reference, not the primary comparator.

## Outcomes and analysis

- Primary outcome: held-out classification accuracy after all 3,000 labels.
- Primary contrast: `ELIGIBILITY_TRACE_NORM_MATCHED − NO_TRACE`.
- First compute the contrast for each task seed after averaging the four delays equally. Then average the three generator-specific means equally; no generator receives weight based on result or sample count.
- Primary 95% interval: 20,000 hierarchical bootstrap draws, resampling the 30 task seeds independently within each of the three fixed generators, retaining each seed's four paired delays and all paired arms. The interval is conditional on these three named generators.
- Report generator-specific and per-delay contrasts, cross-entropy, and the trace-minus-exact-replay contrast descriptively. No multiplicity-adjusted per-delay confirmatory claim.
- Task seed is the independent unit. Delays and arms are paired repeated conditions; cue/time steps are not independent units.

## Decision rules and stop

- If the overall 95% interval is entirely above zero and all three generator-specific mean contrasts are positive: `ADVANTAGE_RETAINED_ACROSS_THE_THREE_TESTED_GENERATORS`.
- If the overall interval is entirely above zero but one or more generator-specific means are nonpositive: `OVERALL_POSITIVE_WITH_GENERATOR_HETEROGENEITY`.
- If the interval includes zero: `INCONCLUSIVE_ACROSS_THE_THREE_TESTED_GENERATORS`.
- If the interval is entirely below zero: `ADVANTAGE_NOT_RETAINED_ON_THE_FROZEN_GENERATOR_SET`.

After reporting this one run, stop this contract. Do not tune γ, learning rate, feature map, or generators from observed outcomes. Any subsequent follow-up requires a new, explicitly outcome-informed contract. None of the possible results establishes biological validation or general AI superiority.
