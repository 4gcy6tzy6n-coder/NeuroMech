# M5 Cerebellar Instructive-Signal Transfer: Exploratory Benchmark Contract

**Status:** post-result method-correction follow-up v3; exploratory, after retained v1 and v2 runs.  
**Biological observation:** in mouse delay eyeblink conditioning, temporally paired climbing-fiber stimulation can replace the sensory unconditioned stimulus and drive learned responses; shifting the CS–US interval shifts learned response timing; temporally precise CF inhibition during the US blocks learning while leaving the airpuff reflex intact. This supports a bounded causal role for CF/complex-spike instructive events in this task. It does not directly establish a specific machine-learning update equation or universal cerebellar learning rule.

Primary sources: Kimpo et al. 2014, *eLife*, DOI `10.7554/eLife.02076`; Silva et al. 2024, *Nature Neuroscience*, DOI `10.1038/s41593-024-01594-7`.

## Artificial question

Can a decaying local eligibility trace assign a delayed teaching label to recently active features better than an instantaneous/no-trace update, and what is lost compared with an exact replay buffer? This is an algorithmic test of delayed credit assignment, not a cerebellum simulation.

## Frozen task

- Generate 30 independent task seeds. Each seed defines a fixed 32-dimensional input-to-4-class mapping using a random 64-feature `tanh` expansion; each feature vector is normalized to unit L2 norm before teacher labels are generated from a random linear head.
- Generate 3,000 online training cues and 1,000 held-out test cues per seed. Cues arrive once per discrete step; labels are delivered in order after delay `D ∈ {1, 4, 16, 64}` steps. Thus, at each label arrival, multiple newer cues may have intervened.
- Student uses the same fixed 64-feature expansion and a trainable 4-class softmax linear readout, initialized to zero; all algorithms have the same trainable parameters and receive the same samples and label stream.
- Learning rate is `0.01`; eligibility decay is fixed at `γ=0.98`; no outcome-based tuning. Cross-entropy error is computed from the prediction made when the cue arrived.

## Frozen arms

1. **EXACT_REPLAY:** retain each cue's feature and prediction until its matching delayed label arrives, then apply the exact per-sample gradient. This is a higher-memory online reference.
2. **ELIGIBILITY_TRACE_RAW:** maintain one feature trace `e_t = γ e_{t-1} + φ(x_t)`. At label arrival, apply the stored sample error to the current trace without normalization. This reproduces v1 and is retained as a diagnostic arm.
3. **ELIGIBILITY_TRACE_NORM_MATCHED:** use the same trace, rescaled at each update to unit L2 norm using only the trace's current state. This controls the v1 concern that a longer trace creates larger weight steps without accessing the original sample.
4. **NO_TRACE:** apply the delayed sample error to the current cue's unit-normalized feature vector at label arrival. This tests temporal misassignment when the original cue is unavailable.
5. **BATCH_LOGISTIC:** fit the same fixed feature representation using all training examples with multinomial logistic regression and L2 coefficient `1e-4`, L-BFGS, and `max_iter=500`. It is a non-online strong reference, not a matched-information online arm.

Online weights use the same learning rate (`0.01`) and same feature/readout parameter count. The exact-replay arm stores `O(D×64)` feature values; eligibility arms store `O(64)` trace values. Batch logistic sees the entire labeled training set and is reported separately. This is a compute/memory tradeoff, not a capacity-matched architecture comparison.

## Outcomes and analysis

- Primary: held-out classification accuracy after all 3,000 labels, paired by task seed; contrast `ELIGIBILITY_TRACE_NORM_MATCHED − NO_TRACE`, averaged equally over four delays.
- Secondary: per-delay held-out accuracy, cross-entropy, learning curve, raw-trace comparison, and contrasts against exact replay and batch logistic.
- Report seed-cluster bootstrap 95% intervals (30 seeds; seeds are the independent units). No multiple-comparison corrected per-delay confirmatory claims; this remains exploratory.
- No hyperparameter search, architecture changes, data-generator changes, or reruns based on observed outcomes within this contract.

## Interpretation limits

- A trace advantage over NO_TRACE shows only that preserving recent feature eligibility helps this synthetic delayed-label task.
- It does not show superiority to backpropagation through time, broader reinforcement learning, or modern sequence models; exact replay is a higher-memory comparator, not a universal strong baseline.
- A negative result rejects only this fixed local-trace implementation under these assumptions; it does not refute cerebellar learning.
- The biological mechanism is not measured by this simulation. “Eligibility trace” is the computational abstraction under test, not a directly observed neural variable in the cited experiments.

## Post-result amendments

The retained v1 run showed raw eligibility accuracy above NO_TRACE, but raw eligibility accumulated multiple feature vectors and therefore had a larger update norm. V2 added norm matching and a batch logistic reference. Code review found the v2 norm-matched arm accessed the target sample's stored feature norm; v3 instead unit-normalizes every input feature and normalizes the trace using only its own state. These amendments followed outcome inspection. V1 and v2 are retained, and no result in this contract family is confirmatory.
