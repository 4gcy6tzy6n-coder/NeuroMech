# M2 premotor predictive-signal artificial transfer V2

**Classification:** outcome-informed follow-up to V1. It is a separate artificial experiment, not biological confirmation.

## Purpose

V1 found that a six-parameter forecast-fusion filter beat its own no-cue ablation in the aligned mapping, but lost to a 45-parameter, two-unit GRU by about `0.071` episode-AUC. Because model capacity and initialization were not matched, that comparison could not attribute the trade-off to computation structure. V2 adds an equal-six-parameter generic recurrent update and pairs model initialization and sampled training batches within each architecture family.

## Task and conditions

The binary switching process, observation bursts, four-step target, forecast-cue construction, sample sizes, 20 training/test seed blocks, and aligned / uninformative / reversed test mappings are exactly those specified in V1. Training uses aligned cue reliability `q=0.72`; all other conditions are held out.

## Arms

- `PREMOTOR_FILTER`: six parameters; observation history updates one recurrent state, while the prospective cue contributes additively to the target logit.
- `NO_CUE_FILTER`: same initialization, six parameters, batches, optimizer, and updates; cue fixed to zero.
- `GENERIC_RNN_6P`: six parameters; observation, visibility, and cue enter one unconstrained scalar recurrent update before the readout.
- `NO_CUE_GENERIC_RNN_6P`: same generic recurrence and six parameters; cue fixed to zero.
- `GRU_CUE` and `GRU_NO_CUE`: the 45-parameter two-unit GRU references from V1, retained as capacity-rich context.
- `CUE_ONLY`: fixed cue-score reference.
- Yoked-cue evaluations reassign each test episode's cue from a different episode using a fixed cyclic shift, preserving the per-time cue marginal while breaking recipient correspondence.

At each training size, paired arms within each architecture receive identical initialization seeds, sampled minibatch sequences, training data, 160 Adam updates, and 16-episode batches. No condition-specific refitting or hyperparameter selection is used.

## Endpoints

Primary metric is per-episode AUC. Primary contrasts at 128 training episodes under aligned testing are (1) `PREMOTOR_FILTER − NO_CUE_FILTER`, (2) `GENERIC_RNN_6P − NO_CUE_GENERIC_RNN_6P`, and (3) `PREMOTOR_FILTER − GENERIC_RNN_6P`. The GRU comparison, cue yokes, other sample sizes, uninformative/reversed mappings, and Brier score are secondary. Bootstrap resampling is across paired seed blocks; episodes remain nested.

## Interpretation

If the two six-parameter cue models differ, this supports an implementation-specific effect of routing the cue into the readout versus the recurrent update in this simulator. A difference against the GRU remains a resource-budget comparison, not proof of general algorithmic superiority. The synthetic cue is directly informative about the future label; this task does not establish that a biological circuit computes or causally delivers it.
