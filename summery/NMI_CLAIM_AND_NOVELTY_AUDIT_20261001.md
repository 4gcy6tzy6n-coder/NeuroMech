# NMI claim and novelty audit — 2026-10-01

## Purpose and scope

This is a bounded project-position audit, not a systematic review and not an experimental result. It combines the current repository evidence with a targeted primary-literature check to prevent the next study from repeating an already established algorithmic claim. Literature search was limited to the most relevant source papers and is not exhaustive.

## What the biological sources already establish

**M2 / C. elegans corollary discharge.** Ji et al. report that motor-circuit feedback is represented in AIY, that RIM is required for this motor-state representation, and that RIM perturbation weakens sustained forward movement during thermotaxis. The biological result is a bounded sensory-circuit feedback and motor-state persistence finding; the project should not claim to rediscover it. See the [source article](https://elifesciences.org/articles/68848).

**M5 / cerebellar teaching events.** The project record links timed climbing-fiber teaching evidence to an eligibility-trace abstraction. The exact exponential trace equation and its transfer to artificial learning remain computational hypotheses rather than a directly measured circuit rule; see the [M5 evidence and claim-boundary record](M5_CEREBELLAR/RESULTS.md).

## What the artificial results currently support

M2's artificial results are conditional and comparator-sensitive. Scalar state-estimation experiments found benefits under some aligned mappings, but task-aware Kalman references remained stronger. The first 2D closed-loop run lost to capacity-matched recurrent controls. The post-result V2 diagnostic found that changing the shared training trajectory distribution shifted the bilinear-minus-MODE_GAIN final-distance contrast by `+0.02279` (crossed 95% interval `[+0.01341,+0.03318]`) and reversed its mean sign. Yet the additive control remained better. A newer, source-aligned feedback-placement abstraction exceeded an equal-parameter output-persistence yoke by `+6.80` accuracy points at hazard `0.05`, but did not beat the no-feedback model, generic RNN, or Bayes reference. The evidence therefore supports sensitivity to training distribution and a bounded stability/switching effect in synthetic controllers; it does not establish an overall AI benefit or transfer from the worm.

M5's simplified eligibility trace beats selected no-trace/local-update controls in several synthetic delayed-credit tasks, but exact replay, BPTT, or batch-learning references remain stronger in the project's tested conditions. The positive contrast is therefore a local algorithmic effect, not a general learning advantage.

Fish1.5 supplies explicit same-specimen neuron-ID registration for listed crosswalk rows, but its inspected public release does not identify the frozen direction-switch/evidence-update computation. The registry records acquisition `PARTIAL`, with E3 closed; it cannot currently serve as a positive structure–function mechanism result.

## Novelty boundary from primary literature

Eligibility traces and online local temporal credit assignment are established computational ideas. Bellec et al.'s e-prop work already combines synaptic eligibility traces with learning signals to train recurrent spiking networks on temporal-credit tasks ([Nature Communications, 2020](https://www.nature.com/articles/s41467-020-17236-y)). A recent hardware study implemented reward-modulated STDP with decaying eligibility traces for in-situ spiking reinforcement learning ([Nature Communications, 2026](https://www.nature.com/articles/s41467-026-69898-9)). These precedents do not invalidate the project's bounded cerebellar comparison, but they make “eligibility traces enable delayed credit assignment” insufficient as the paper's novel central claim.

Likewise, “motor feedback sustains a neural state” is already the central result of the Ji et al. biological study. Reimplementing that statement in an artificial network, without a new computational prediction and discriminating controls, would be an application demonstration rather than a new mechanism discovery.

## Assessment

**Fact:** the repository contains multiple M2 and M5 source-model and synthetic runs, including null/adverse results and strong task-aware or generic baselines. These results are documented separately and are not pooled.

**Inference:** current results do not yet support a single NMI-level positive claim spanning biological evidence and AI benefit. In particular, the artificial M2 reliability-gating task does not directly instantiate the experimentally supported RIM→AIY corollary-discharge computation; the M5 local trace abstraction is not novel by itself and remains below replay-based references.

**Recommendation and update:** a source-equation stress test found sensory-site feedback exceeded the no-feedback ablation in simulated local progress across stationary and reversing gradients, with reduced progress under faster reversals. However, moving the same coefficient into the motor-state equation saturated the output-only arm at 100% forward occupancy, invalidating that arm as a persistence-matched placement control. A subsequent cross-agent yoke preserved the source feedback signal's exact instantaneous population distribution while breaking recipient-specific contingency. Self-contingent feedback exceeded the yoke at 20-s reversals (+0.04618 aligned-progress units/s; 95% interval [+0.04252,+0.04994], 100/100 simulation blocks positive), but the small contrast reversed at 5 s. This supports a bounded recipient-specific contingency effect inside the source-model equations; the yoke is a replay, not an independent biological intervention. The next step is to carry this operation into a distinct adaptive artificial task against a parameter/compute-matched generic controller and a task-aware reference. Until that comparison succeeds, report a source-model mechanism probe, not a transferred AI principle.

## Publication status

The work is active, but “NMI-ready” is not currently supported. A future paper needs a narrow central contribution, direct links from biological observations to the computational variables, strong matched controls, independent task generalization, complete provenance, and a manuscript-level novelty assessment. Further dataset acquisition is not the current bottleneck for the M2/M5 artificial studies; scientific alignment and comparative strength are.
