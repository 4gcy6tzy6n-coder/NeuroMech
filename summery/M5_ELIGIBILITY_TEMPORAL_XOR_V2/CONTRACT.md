# M5 eligibility trace on learnable delayed temporal XOR — V2 contract

**Experiment ID:** `M5_ELIGIBILITY_TEMPORAL_XOR_V2`  
**Classification:** post-result exploratory optimization. M10 V1 and calibration outcomes are known. This is not confirmatory, biological validation, or a broad AI claim.

## Question

On a learnable short-delay two-cue XOR task, does a local eligibility trace improve online learning over a current-step-only local update, and how close is it to exact BPTT?

## V1 diagnosis and scope change

M10 V1 used per-example SGD and failed its BPTT task-viability check at all tested delays. Calibration showed Adam at learning rate 0.03 made the four-step task learnable in held-out calibration seeds, while 16/64-step tasks remained unreliable under the calibrated training exposure. This V2 therefore tests only delay 4. It does not test or claim long-delay transfer. The calibration is outcome-informed and is not used as the V2 test set.

## Task and units

- Two independent binary cues `a,b ∈ {0,1}` arrive in separate one-hot input channels; target is `a XOR b`.
- First cue at t=0; four Gaussian distractor steps (`SD=0.25`); second cue at t=5; terminal readout at t=6.
- 30 task seeds `1000..1029`; each has 3,000 training and 500 held-out episodes. Task seed is the inferential unit; examples are nested within seed.
- All three arms within a task seed share identical initial parameters and train/test episode sequences.

## Model and update arms

All arms use the same 24-unit leaky tanh RNN, full parameterization, initialization, training examples, episode order, gradient norm clip (1.0), and Adam optimizer (`lr=0.03`, `beta1=0.9`, `beta2=0.999`, `epsilon=1e-8`; optimizer state reset per arm).

1. `ELIGIBILITY_TRACE`: V1 local eligibility accumulation with decay `gamma=0.98`, followed by the terminal learning signal.
2. `NO_TRACE`: same local update but only the terminal time-step eligibility.
3. `BPTT`: exact gradient through the same complete sequence.

Training steps per arm are 3,000 online episodes. No hyperparameter or seed selection is allowed after V2 test outcomes are computed.

## Primary estimand and interpretation

Primary contrast: held-out XOR accuracy `ELIGIBILITY_TRACE − NO_TRACE` over delay 4, paired by task seed. Report mean, 20,000-resample percentile bootstrap 95% interval, and positive-seed count. BPTT is a strong conventional comparator and has a viability rule: its 95% task-seed bootstrap lower bound must exceed chance (0.50). If BPTT fails, the trace contrast is reported but classified `INCONCLUSIVE_TASK_NOT_LEARNABLE`.

Report cross-entropy and all arm accuracies. No result generalizes beyond this synthetic architecture, short-delay task, optimizer, and tested seeds. The biological motivation is the bounded cerebellar teaching-event evidence; the trace equation is an abstraction, not a measured biological synaptic rule.

## Provenance

V1's files remain unchanged. This V2 uses fresh seeds, disjoint from V1 and all calibration seeds. The contract and runner are hashed before execution; the runner performs a finite-difference gradient check and truth-table/timing checks before outcomes.
