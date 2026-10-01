# M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1 — failure and limitation log

## Outcome

The sensory-site LTC did not meet its frozen criterion because it lost to output-site feedback and both generic recurrent controls. Its improvements over no-feedback and yoked feedback were statistically resolved at the seed-block level but very small relative to the absolute MSE; no practical-effect threshold was frozen. The larger `GRU_4` performed much better in the aligned condition.

## What this rules out

- It rules out a useful sensory-site advantage for this specific four-unit equation-level LTC, supervised objective, data generator, optimizer, and update budget.
- It does not establish that sensory-site feedback is worse in the worm, nor does it test a biological intervention.
- The `c=0` and `c=−1` results are out-of-training-distribution conditions; their degradation is not a replication of biological context changes.

## Lessons

- Separating inference from policy learning made the task learnable for a generic recurrent controller, but did not rescue the proposed sensory-site implementation.
- A statistically positive effect against an ablation can be negligible in magnitude; freeze a practically meaningful threshold before future confirmatory work.
- The output-site control is decisive here: placing motor state directly at the estimator readout is a more effective computation in this task than routing it through the sensory-state update.
- The gap to `GRU_4` means capacity and optimization remain central; nominally capacity-matched `GRU_2` was still weaker than `GRU_4`.
- Future M2 work should begin from source-model operation/representational evidence or a new task specification, not from post-hoc changes to this generator.

The initial runner preflight caught a function-signature mismatch between LTC and GRU cells. This was corrected before any outcome run. The first short run also produced undefined secondary correlation values for constant predictions; the statistic was removed before the final preflight and full run. Neither defect affected the completed results, which were generated only after the corrected preflight.
