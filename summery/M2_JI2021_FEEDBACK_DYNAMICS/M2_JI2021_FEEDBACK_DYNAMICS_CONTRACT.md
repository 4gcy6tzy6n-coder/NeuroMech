# M2_JI2021_FEEDBACK_DYNAMICS — source-model replication and noise-boundary test

**Status:** post-result exploratory computational replication. The model and the direction of its published Figure 7 result are public and known; this is neither a blind confirmation nor a new biological experiment.

## Biological anchor and transfer boundary

Ji et al. report that AIY represents thermal and locomotor-state information, RIM is required for the motor-state corollary-discharge signal reaching AIY, and RIM ablation removes that representation and reduces sustained forward movement during thermotaxis. Their Figure 7 minimal model operationalizes the proposed computation as a positive feedback copy from motor output to a sensory-processing interneuron, coupled to the sensory input and a motor-output nonlinearity. This contract tests that source model's qualitative navigation result and its sensitivity to sensory-noise amplitude. It does not establish that the model uniquely identifies the worm circuit or that the same operation benefits AI systems.

Primary source: Ji et al. (2021), *eLife* 10:e68848, DOI `10.7554/eLife.68848`; official Figure 7 supplementary MATLAB script is pinned in `data/raw/celegans/ji_etal_2021_elife_68848_v3/`.

## Frozen model and factors

The runner translates the authors' Figure 7 agent equations from the published MATLAB script into Python. Author-specified constants are preserved: `N=1500`, `tmax=200`, `dt=tmax/N`, 50 agents per simulation block, `gamma_A=gamma_M=1.5`, motor-feedback slope `km=15`, sensory-to-motor slopes `kf=kr=5`, motor threshold `Mth=0`, AIY threshold `Ath=1.5`, warm-gradient coefficient `kt=-1.5`, forward drive `ff=1`, reversal drive `rf=0.7`, and velocity magnitude `kv=1`. The source's Gaussian sensory-noise term is `2*N(0,1)`; the stress test scales this term by `noise_scale ∈ {0.5,1,2}`. Feedback coefficient `fb ∈ {-1,0,+1}` represents negative feedback, no feedback, and positive feedback. All arms use common random numbers within simulation-seed blocks.

The loop equations translated from the source are:

```text
I_s(t) = kt * (x(t) - x(t - 0.5 s)) * 1[M(t) > 0]
dA/dt = 1.5 * (I_s(t) + 0.5 + 2*noise_scale*z(t) + fb*sigmoid(15*M(t)) - A(t))
dM/dt = 1.5 * (sigmoid(5*(A(t)-1.5)) - 0.7*sigmoid(-5*(A(t)-1.5)) - M(t))
```

The sign, order, and integration are source translated; the noise factor, source timestep, 50-agent block, and the listed parameter values are fixed. Forward/reversal transitions update heading as in the source code: preserve heading within a state, reverse heading by π on forward-to-reverse, and randomize heading on reversal-to-forward.

## Question, endpoint, and analysis

The primary question is whether the source's positive-feedback arm has higher warm-gradient run-direction index than its no-feedback arm at the source noise scale (`noise_scale=1`). The primary endpoint is the simulation-block mean of the source-defined forward-run-length-weighted direction index `−cos(heading)`; positive values correspond to movement toward the warm direction under the source's `kt=-1.5` convention. The primary contrast is `fb=+1 minus fb=0`. Secondary endpoints are mean forward-run duration, final warm-axis displacement, and the positive-minus-zero contrast at noise scales 0.5 and 2.0. Negative feedback is an additional sign control.

There are 100 independent simulation-seed blocks per condition, each containing 50 simulated agents. The simulation-seed block is the resampling unit; individual agents within a common block are clustered, and time steps are not replicates. Paired percentile bootstrap intervals use 20,000 resamples of seed blocks. This quantifies Monte Carlo variability under the stipulated simulation, not biological population uncertainty.

## Interpretive boundaries

- Reproduction of the positive-feedback advantage would reproduce a published computational model result, not independently validate the biological mechanism.
- Noise-scale sensitivity is a stress test; it does not estimate biological sensory noise or define a reliable parameter range for worms.
- The model is hand-specified and task-specific; it has no learning, no capacity-matched generic recurrent baseline, and no AI benchmark.
- This translation approximates MATLAB `smooth(M,4)` forward-run segmentation with a centered four-sample moving average. Any small discrepancy from MATLAB boundary handling is an implementation limitation.
- No outcome in this experiment may be described as evidence that a biological mechanism improves AI.
