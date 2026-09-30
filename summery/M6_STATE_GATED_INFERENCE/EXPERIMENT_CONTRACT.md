# M6 — State-gated sensory inference across unseen dynamics

**Status:** outcome-informed exploratory study. It follows earlier M2 experiments, including negative closed-loop results. It is a new task generator and must not be represented as confirmation of those earlier results or as biological validation.

## Biological computation being abstracted

Ji et al. (eLife 2021, DOI 10.7554/eLife.68848) reported that AIY activity carries thermosensory and locomotor-state signals; motor-circuit drive to AIY requires RIM; RIM ablation removes the AIY motor-state representation, increases downstream thermosensory representation, and reduces forward-run persistence under positive thermotaxis. This supports a bounded computation: motor-state feedback can change the influence of sensory input and contribute to sustained sensorimotor state. It does not show that motor state reports sensory reliability. Reliability modulation below is an explicit artificial task assumption.

## Question

After learning on a noisy-state mapping, does an explicit state-conditioned sensory gain generalize to unseen latent-state switching rates better than a parameter-count-matched generic innovation-adaptive filter that does not receive the state label?

## New synthetic task

A latent target takes values −3/+3 and switches with hazard `h`. A two-state motor-context signal follows a Markov chain (forward→reversal 0.03, reversal→forward 0.20). The observer receives a noisy scalar target observation at every step. Observation standard deviation depends on context in the training distribution (`sigma_forward=0.25`, `sigma_reversal=1.20`). This reliability relationship is a synthetic design choice, not a biological finding.

Train each model on 512 independent trajectories with hazards drawn log-uniformly from `[0.005, 0.08]`, 320 steps per trajectory, and the high-reversal-noise mapping. Use 20 independent model-training seeds. Freeze all learned parameters before evaluation.

## Policies

- `STATE_GATED_GAIN`: two learned gains, one for each observed context state; update estimate by `s_t = s_(t-1) + g_context * (y_t - s_(t-1))`.
- `INNOVATION_ADAPTIVE`: two learned parameters; gain is a logistic function of absolute prediction residual, without the context label. This is the primary parameter-count-matched generic control.
- `GLOBAL_GAIN`: one learned scalar gain; simple reference.
- `NO_MEMORY`: use the current observation directly.
- `ORACLE_HMM`: exact two-state Bayesian filter given the evaluation hazard and observation-noise mapping; a model-informed reference, not a capacity-matched learner.

## Evaluation

Use independent held-out target trajectories at hazards `0.005`, `0.04`, and `0.075`, none of which is used as a fixed training hazard. Evaluate three profiles: high reversal noise (primary), equal noise, and reversed noise (counterfactual stress tests). Each cell uses 256 shared trajectories of 320 steps. Primary metric is episode-averaged absolute target-estimation error. Primary contrast is `STATE_GATED_GAIN - INNOVATION_ADAPTIVE`; negative favors explicit state gating. Bootstrap independently over the 20 training seeds and 256 shared test trajectories (20,000 crossed draws).

## Interpretation

A negative primary interval supports only this small learned filter on this telegraph-target family. Performance under equal/reversed reliability tests whether the learned gate depends on the assumed context-reliability relation. The oracle is expected to be strong because it knows the generator. No result validates the C. elegans mechanism, establishes a general AI benefit, or supports organism-level causal claims. Regardless of outcome, retain all policies, seeds, conditions, and raw episode errors.
