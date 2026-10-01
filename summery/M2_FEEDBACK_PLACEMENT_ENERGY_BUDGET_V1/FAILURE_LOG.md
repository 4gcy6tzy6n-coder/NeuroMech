# Failure and limitation log

## Implementation incident: duplicated evaluation blocks

The first execution produced 491,520 validation rows and 245,760 test rows instead of the frozen 30,720 and 15,360. The cause was an evaluator that looped over all seed blocks while its caller was already processing one training block. This mislabeled cross-block evaluations and invalidated the seed summaries. The verifier stopped at the row-count assertion. The initial run's printed contrast is invalid and is not used in the results.

The evaluator was corrected to use only the current training block. The primary question, model arms, generated training streams, energy budget, validation selection procedure, endpoints, bootstrap, and test seeds did not change. The corrected outputs passed the verifier and an independent full rerun. The initial invalid output tables remain in compressed form with a raw-hash index so they can be audited without bloating the repository with duplicate raw CSVs.

## Scientific and design limitations

- This is a synthetic controller task, not an intervention or causal test in *C. elegans*.
- The energy budget (`0.50`) was selected after seeing previous experiment outcomes. The present result is outcome-informed and cannot be called independent confirmation.
- The primary interval spans zero with only 16 seed blocks. The experiment therefore does not establish a reliable placement difference; it does not prove equivalence.
- Test-budget success is limited to the selected controllers, `TRANSIENT_PULSE`, this simulator, and the frozen mean-command-energy definition. It does not establish energy efficiency in animals or other tasks.
- Validation selection gives each of three conditions equal weight for policy selection, while the primary endpoint is one condition. This is the frozen rule; it does not guarantee optimality under other condition mixes.
- The GRU-8 uses many more parameters than the scalar policies. Its comparison is descriptive, not capacity-matched. Equal optimizer updates are not equal compute.
- Secondary metrics and other task conditions are descriptive; no multiplicity-adjusted claims are made from them.
- Training random streams are shared across arms within a seed block, but each model's learned parameters are initialized and trained independently; the block, not an episode, is the uncertainty unit.

## Next experiment implication

Do not interpret this as a sensory-site win. A distinct follow-up would need a newly frozen question and protocol—preferably an outcome-independent budget calibration and capacity/compute-aware controls—before any new run. The present result remains a negative-to-inconclusive boundary for this specific synthetic translation.
