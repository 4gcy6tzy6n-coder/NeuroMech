# M5 eligibility trace under a bounded feature-memory budget — V1

**Status:** post-result exploratory experiment. Earlier M5 outcomes are known; this experiment uses disjoint task seeds and a new explicit memory-budget comparison. It is not biological validation or a confirmatory test.

## Question

On the established delayed-label task, how does the accuracy of a fixed 64-value eligibility trace compare with exact FIFO feature replay under the same active feature-state budget, and how does exact replay's performance change as its memory budget grows?

The narrow computational hypothesis is that a decaying eligibility state can use a small fixed feature-state budget more effectively than an exact FIFO buffer that cannot retain every pending cue. This does not predict superiority to unbounded replay.

## Task

Reuse the M5 delayed-label classification generator: 32-dimensional inputs, 64-dimensional random tanh features normalized to unit norm, four classes, 3,000 training cues, 1,000 held-out cues, delays `D ∈ {1,4,16,64}`, and fixed eligibility decay `γ=0.98`. Test the three previously used input generators (IID Gaussian, AR(1) Gaussian with coefficient 0.8, sparse sign with 20% active coordinates). Use 30 new task seeds per generator (`100..129`) under master seed `20261002`. Teacher, feature projection, stream, and test set are shared across arms within each task.

## Arms and resource accounting

All arms use the same zero-initialized 64×4 linear softmax readout, online update rule, learning rate `0.01`, task data, prediction-error queue, and held-out set.

- `ELIGIBILITY_TRACE_64`: retain the 64-value state `e_t = 0.98 e_(t−1) + φ_t`; use its normalized value when each delayed label arrives.
- `EXACT_FIFO_64`, `EXACT_FIFO_256`, `EXACT_FIFO_1024`, `EXACT_FIFO_4096`: retain at most 1, 4, 16, or 64 exact 64-value cue vectors. If the cue associated with an arriving label has already been evicted, skip that update. This is the declared bounded-memory behavior, not an approximate reconstruction.
- `CURRENT_FEATURE_64`: retain no historical feature and apply each delayed error to the current feature, as in the prior no-trace control.
- `EXACT_REPLAY_UNBOUNDED`: retain the exact feature for every pending cue; reference upper bound with delay-dependent state `64×D`.

The primary resource quantity is active feature-state values. The delayed label/prediction-error queue and fixed dataset storage are shared interface/task costs and excluded equally. The separately stored softmax readouts have identical 256 trainable values in every arm. This accounting is algorithmic active-state accounting, not measured process RAM, energy, or wall-clock compute.

## Outcomes and inference

Primary outcome: held-out accuracy after the complete online stream. Primary contrast: `ELIGIBILITY_TRACE_64 − EXACT_FIFO_64`, averaged first across the four delays per task seed and then equally across the three named generators. The interval is a 20,000-draw hierarchical bootstrap, resampling 30 task seeds within each fixed generator; the generators themselves are not treated as a random sample.

Report all generator×delay means and paired intervals descriptively, plus the full accuracy-by-active-feature-state frontier for every exact FIFO budget and unbounded replay. Report update coverage because bounded FIFO arms may drop cue-label updates after eviction. Do not rank arms by a post hoc single delay or choose a new decay factor.

## Interpretation boundary

A positive primary contrast means only that the fixed trace exceeds a one-vector exact FIFO under this stated task and feature-state accounting. It does not show superiority to full replay, other compressed-memory algorithms, published online-learning systems, or biological mechanisms. A null or negative contrast remains informative about where the trace is not a useful compressed state. No biological endpoints or cross-task pooled accuracy scores are used.
