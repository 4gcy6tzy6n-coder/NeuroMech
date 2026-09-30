# M5 Cerebellar Instructive-Signal Transfer: Exploratory Benchmark Contract

**Status:** post-result method-correction follow-up v2; exploratory, after a retained v1 run.  
**Biological observation:** in mouse delay eyeblink conditioning, temporally paired climbing-fiber stimulation can replace the sensory unconditioned stimulus and drive learned responses; shifting the CS–US interval shifts learned response timing; temporally precise CF inhibition during the US blocks learning while leaving the airpuff reflex intact. This supports a bounded causal role for CF/complex-spike instructive events in this task. It does not directly establish a specific machine-learning update equation or universal cerebellar learning rule.

Primary sources: Kimpo et al. 2014, *eLife*, DOI `10.7554/eLife.02076`; Silva et al. 2024, *Nature Neuroscience*, DOI `10.1038/s41593-024-01594-7`.

## Artificial question

Can a decaying local eligibility trace assign a delayed teaching label to recently active features better than an instantaneous/no-trace update, and what is lost compared with an exact replay buffer? This is an algorithmic test of delayed credit assignment, not a cerebellum simulation.

## Frozen task

- Generate 30 independent task seeds. Each seed defines a fixed 32-dimensional input-to-4-class mapping using a random 64-feature `tanh` expansion and a random linear teacher head.
- Generate 3,000 online training cues and 1,000 held-out test cues per seed. Cues arrive once per discrete step; labels are delivered in order after delay `D ∈ {1, 4, 16, 64}` steps. Thus, at each label arrival, multiple newer cues may have intervened.
- Student uses the same fixed 64-feature expansion and a trainable 4-class softmax linear readout, initialized to zero; all algorithms have the same trainable parameters and receive the same samples and label stream.
- Learning rate is `0.01`; eligibility decay is fixed at `γ=0.98`; no outcome-based tuning. Cross-entropy error is computed from the prediction made when the cue arrived.

## Frozen arms

1. **EXACT_REPLAY:** retain each cue's feature and prediction until its matching delayed label arrives, then apply the exact per-sample gradient. This is a higher-memory online reference.
2. **ELIGIBILITY_TRACE_RAW:** maintain one feature trace `e_t = γ e_{t-1} + φ(x_t)`. At label arrival, apply the stored sample error to the current trace without normalization. This reproduces v1 and is retained as a diagnostic arm.
3. **ELIGIBILITY_TRACE_NORM_MATCHED:** use the same trace, but rescale its norm at each update to match the target sample feature's norm. This controls the v1 concern that a longer trace creates larger weight steps than the other online arms.
4. **NO_TRACE:** apply the delayed sample error to the feature vector of the current cue at label arrival, rescaled to the target sample feature norm. This tests temporal misassignment when the original cue is unavailable.
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

## Post-result amendment

The retained v1 run showed raw eligibility accuracy above NO_TRACE, but raw eligibility accumulated multiple feature vectors and therefore had a larger update norm. That makes the v1 contrast insufficient to attribute its gain to credit assignment. V2 adds an update-norm-matched trace arm and a batch logistic reference. This amendment followed outcome inspection, so no v2 result is confirmatory.
