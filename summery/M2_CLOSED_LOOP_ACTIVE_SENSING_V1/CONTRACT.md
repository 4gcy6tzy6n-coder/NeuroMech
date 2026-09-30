# M2 closed-loop active-sensing transfer V1

**Status:** exploratory synthetic control benchmark. Earlier M2 state-gating and decision-probe outcomes were known before this task. It is not confirmatory or biological validation.

## Question

Can a state-conditioned sensory update learned on randomly switching motor contexts support closed-loop target approach when the controller's own action determines whether the next sensory observation carries target information?

## Task and observation model

Each episode has a hidden fixed target `theta ∈ {-0.5,+0.5}` and a one-dimensional agent position initialized at zero. At each of 24 steps, the current motor mode `q ∈ {-1,+1}` determines the observation `y = H(q)*theta + 0.35*z`, `z~Normal(0,1)`. ALIGNED uses `H(+1)=1,H(-1)=0`; INDEPENDENT uses H=0.5 in both modes; REVERSED swaps the aligned mapping. The initial mode is forward (+1). The controller receives only y and q in its recurrent estimator, and uses its current estimate of theta plus known position to choose movement. Each non-hold action moves the agent by 0.05 toward or away from the estimated target; a hold occurs only when the estimate-position error is within half a step and preserves the previous motor mode. The next motor mode is set by the movement direction. Thus actions change future observation availability.

## Training and models

Train each policy only on ALIGNED observations with an exogenous binary motor-mode Markov sequence (switch probability 0.15); the hidden target is fixed for the entire training episode. Each training seed uses 512 episodes × 64 steps, 250 full-batch Adam updates, and MSE supervision of the target. Evaluate 20 independently trained seeds on 512 common target/noise episodes in each of ALIGNED, INDEPENDENT, and REVERSED closed-loop conditions.

Policies are the 4-parameter `MODE_GAIN_FILTER`, 3-parameter context-free constant-gain ablation, 4-parameter additive RNN, 5-parameter bilinear RNN, 17-parameter one-unit GRU, and an exact Bayesian posterior-mean observer with known target prior, sensor coefficient and observation variance. The same greedy position-control wrapper is applied to every estimator, including the Bayesian observer; it is not an optimal active-sensing policy. The observer is model-based, not learned or capacity-matched. All learned policies use the same data, number of optimizer steps and loss; model compute differs by architecture.

## Outcomes and estimands

The primary outcome is episode mean absolute target distance after each movement; smaller is better. The primary contrast is `distance(CONSTANT_GAIN_FILTER)-distance(MODE_GAIN_FILTER)` in ALIGNED; positive values favor the mode-gain mechanism. The primary interval uses 20,000 crossed bootstrap draws over training seeds and paired episode IDs (seed 20261008). Secondary outcomes are terminal distance and success rate (terminal distance ≤0.10), plus the same contrasts in the other channel mappings. Episodes are the independent environmental units; steps are aggregated within episode.

## Interpretation boundary

The hidden target, observation channel, motor control, and reward are synthetic. Even a positive result would establish only this toy active-sensing task, not that the worm implements the controller, not broad AI benefit, and not a publication-level claim by itself. A negative or shifted-mapping cost remains part of the result.
