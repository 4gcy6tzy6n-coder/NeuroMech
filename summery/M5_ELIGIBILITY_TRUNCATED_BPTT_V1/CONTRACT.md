# M5_ELIGIBILITY_TRUNCATED_BPTT_V1 — eligibility versus truncated recurrent credit

## Question and scope

In a recurrent network trained on delayed temporal XOR, does a local eligibility trace improve online learning over truncated backpropagation through time (TBPTT) with the same recurrent architecture and training stream, and what is the remaining gap to full BPTT?

Kimpo et al. (2014, DOI `10.7554/eLife.02076`) and Silva et al. (2024, DOI `10.1038/s41593-024-01594-7`) support a task-bounded causal role for cerebellar climbing-fiber teaching events in associative eyeblink learning. They do not establish the exact synaptic equation or a universal eligibility rule. This experiment tests an artificial local-credit abstraction inside an RNN; it does not reproduce eyeblink conditioning or validate a biological learning rule.

This is a post-result exploratory comparison: the task and optimizer were informed by the earlier temporal-XOR V2 result. Fresh seeds do not make it confirmatory. The specific aim is to distinguish local eligibility from a generic recurrent-credit method with a deliberately truncated temporal gradient.

## Task

Two independent binary cues arrive at different times. The target is their XOR. The first cue is presented at step 0, four Gaussian distractor steps (`SD=0.25`) follow, the second cue arrives at step 5, and the terminal readout is evaluated at step 6. The sequence therefore requires a recurrent state to preserve the first cue across the distractor interval.

- 32 task-seed blocks: `2000..2031`.
- 3,000 online training episodes and 500 fresh test episodes per seed and arm.
- All arms within a task seed share initialization and episode order.
- All arms use the same 24-unit leaky tanh RNN, 746 trainable parameters, global gradient clipping at 1.0, and Adam (`lr=0.03`, `β1=0.9`, `β2=0.999`, `ε=1e−8`); optimizer state is reset per arm.

## Update arms

1. `ELIGIBILITY_TRACE`: local presynaptic/hidden-state eligibility traces with decay `γ=0.98`, followed by the terminal teaching signal.
2. `NO_TRACE`: the same local rule using only terminal-step eligibility.
3. `TBPTT_1`: exact autodifferentiation through only the final recurrent step; hidden state before that step is detached.
4. `TBPTT_4`: exact autodifferentiation through the final four steps; earlier hidden state is detached at the truncation boundary.
5. `BPTT_FULL`: exact autodifferentiation through all seven steps; strong reference.

The four-step TBPTT horizon spans the second cue and response but cuts the gradient path to the first cue's encoding. All arms use identical forward dynamics. Report per-arm measured training time, update rule, and total trainable parameter count. Runtime is descriptive because Python/NumPy and autodiff overhead differ; it is not a hardware-independent FLOP estimate.

## Outcomes and analysis

- Primary endpoint: held-out XOR accuracy, averaged within task seed and arm.
- Primary contrast: `ELIGIBILITY_TRACE − TBPTT_4` accuracy, paired by task seed.
- Secondary contrasts: trace minus no-trace, TBPTT-1, and full BPTT; also report cross-entropy and training time.
- Independent unit: task-seed block (`n=32`); episodes are nested.
- Uncertainty: 20,000-resample paired percentile bootstrap, RNG seed `20261013`.
- Task-learnability reference: full BPTT must achieve an interval lower bound above chance (`0.50`) to interpret trace-versus-TBPTT comparisons as a successful task transfer. Regardless of viability, retain and report every outcome.
- No test-set tuning, seed exclusion, or post-result changes within this experiment version.

## Interpretation

If the eligibility trace beats TBPTT-4 while remaining below full BPTT, the result supports a bounded local-credit advantage over that truncated gradient horizon with an explicit performance gap to full temporal credit. It does not imply superiority to exact gradient methods or general AI benefit. If it does not beat TBPTT-4, this implementation does not support the tested local-trace advantage. If full BPTT fails its task-viability reference, the comparison is inconclusive about the mechanism but remains a reported implementation result.

## Artifacts

- Runner: `model/M5_ELIGIBILITY_TRUNCATED_BPTT_V1/run_experiment.py`
- Analysis, verifier, and figure generator: `model/M5_ELIGIBILITY_TRUNCATED_BPTT_V1/`
- Raw results: `data/results/M5_ELIGIBILITY_TRUNCATED_BPTT_V1/`
- Results, scope, and failure notes: this directory.
