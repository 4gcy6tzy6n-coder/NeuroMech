# M5 — cerebellar delayed teaching / eligibility benchmark

**Status:** post-result exploratory synthetic study. The results do not validate a biological learning rule or constitute confirmatory AI transfer.

## Biological evidence scope

Kimpo et al. (2014, DOI: 10.7554/eLife.02076) and Silva et al. (2024, DOI: 10.1038/s41593-024-01594-7) support a task-bounded causal role for climbing-fiber teaching events in associative eyeblink learning. They do not determine the exact plasticity equation or establish a universal cerebellar rule. The source experiments also have limitations, including small group sizes and tool-specific caveats described in `RESULTS.md`.

## Positive computational result

In v3, an eligibility trace improved accuracy over a no-trace online update by a mean +0.2868 across delays 1, 4, 16, and 64; seed-cluster bootstrap 95% interval [+0.2712, +0.3010] across 30 task seeds. This is a narrow result on a synthetic stream.

## Limitations and failures

- The trace remained below exact replay and batch logistic at every delay; accuracy degraded at the longest delay.
- v1's apparent gain was partly confounded by larger update norms.
- v2 norm matching used the target feature's norm, leaking information unavailable to a strictly local learner.
- v3 corrected both issues using unit-normalized inputs and only the current local trace norm. Because these corrections followed inspection of earlier outcomes, v3 remains post-result exploratory.
- Replay and batch comparators have different memory/data access, so the comparison does not establish broad algorithmic superiority.

## Cross-input-generator follow-up

A separate outcome-informed follow-up kept the v3 learning rate and trace decay fixed and evaluated 30 new tasks in each of three input generators (IID Gaussian, AR(1) Gaussian, and sparse-sign inputs). The equal-generator, four-delay mean contrast (eligibility trace minus no-trace) was `+0.2284` accuracy (95% hierarchical seed-bootstrap interval `[+0.2213,+0.2357]`); all 30 seed-level four-delay averages were positive within each generator. The result is conditional on three input-stream distributions sharing the same classification objective. Under AR(1) inputs, no-trace was better at delays 1 and 4; the trace helped at delays 16 and 64. Exact replay still outperformed the trace across all generator-delay cells. This is input-distribution robustness, not generalization across unrelated task families or biological validation. See [`../M5_TASK_GENERATOR_GENERALIZATION/RESULTS.md`](../M5_TASK_GENERATOR_GENERALIZATION/RESULTS.md).

## Different-objective follow-up: delayed-reward contextual bandit

A further post-result run moved from supervised delayed labels to a two-action contextual bandit with delayed stochastic scalar rewards. The fixed norm-matched trace exceeded the no-trace update by `+0.00914` held-out expected reward (paired task-seed bootstrap 95% interval `[+0.00772,+0.01088]`, 30 seeds; equal average over four delays). The gain shrank with longer delay, from `+0.01308` at delay 1 to `+0.00310` at delay 64; exact replay remained substantially stronger (`0.5525` mean reward versus `0.5096` for trace). This is a first limited positive result across two synthetic objectives, not broad task generalization, an LNN result, or biological/connectome transfer. The bandit was designed after earlier M5 results and remains exploratory. See [`../M5_DELAYED_REWARD_BANDIT/RESULTS.md`](../M5_DELAYED_REWARD_BANDIT/RESULTS.md).

## Recurrent-reservoir architecture follow-up

A fixed random leaky recurrent reservoir with a learned linear readout retained a smaller positive trace advantage on the same contextual-bandit objective: `+0.002887` held-out expected reward (paired task-seed bootstrap 95% interval `[+0.002089,+0.003815]`, 30 seeds; 27/30 positive four-delay seed averages). The contrast declined from `+0.003982` at delay 1 to `+0.001423` at delay 64. Exact replay remained stronger (`0.51812` versus `0.50327` trace and `0.50038` no-trace). This is evidence in a recurrent feature generator only: reservoir weights were fixed, so it is not a trained RNN/LNN/LTC or architecture-generalization result. The run emitted NumPy matrix-operation warnings despite finite, independently reproduced outputs; the warning source remains unresolved. See [`../M5_RECURRENT_RESERVOIR_BANDIT/README.md`](../M5_RECURRENT_RESERVOIR_BANDIT/README.md).

## Files

- Code: [`model/M5_CEREBELLAR/run_delayed_teaching.py`](../../../model/M5_CEREBELLAR/run_delayed_teaching.py)
- Results: [`data/results/M5_CEREBELLAR/`](../../../data/results/M5_CEREBELLAR/)
- Protocol versions and detailed interpretation: this directory.

## Temporal-correlation boundary follow-up (M7)

A fixed-parameter six-rho × four-delay sweep evaluated separate classification and regression objectives. Within each objective, stronger input autocorrelation reduced the trace's advantage at short delays, but this relation reversed at long delays. Exact replay remained better in all 48 cells. An initial pooled summary averaged accuracy and MSE differences and was invalidated; read the objective-stratified analysis in [`../M7_TEMPORAL_CORRELATION_BOUNDARY/RESULTS.md`](../M7_TEMPORAL_CORRELATION_BOUNDARY/RESULTS.md). This is still the same synthetic teacher family, not a general task-family result or biological validation.

## Trained recurrent-gradient comparison (M5_ELIGIBILITY_TRUNCATED_BPTT_V1)

A fresh 32-seed delayed-XOR study compared the local eligibility update with no-trace local learning, TBPTT-1, TBPTT-4, and full BPTT in the same 24-unit, 746-parameter RNN. Eligibility reached 0.6974 held-out accuracy: it exceeded no-trace by +0.14125 (paired task-seed 95% interval [+0.07188,+0.21288]) but fell below TBPTT-4 by −0.26588 ([−0.32950,−0.20031]); full BPTT reached 0.9996. Since full BPTT demonstrated task viability, the TBPTT comparison is interpretable negative evidence against treating this trace as a competitive substitute for recurrent gradients on this task. It remains a post-result exploratory synthetic experiment and does not validate a cerebellar learning rule. See [`../M5_ELIGIBILITY_TRUNCATED_BPTT_V1/RESULTS.md`](../M5_ELIGIBILITY_TRUNCATED_BPTT_V1/RESULTS.md).
