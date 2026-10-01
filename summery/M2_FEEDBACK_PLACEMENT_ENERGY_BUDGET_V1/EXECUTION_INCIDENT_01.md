# Execution incident 01 — duplicated evaluation blocks

## Detection

The first execution completed, but `verify_results.py` failed its frozen row-count check before any result was accepted. The expected counts were 30,720 validation rows and 15,360 selected-test rows. The produced files instead contained 491,520 and 245,760 rows, respectively.

## Cause

`eval_one()` iterated across all 16 seed blocks even though the caller was already inside one training block. Each fitted model was therefore evaluated on all evaluation blocks, and those outcomes were written under the model's training-block label. The resulting seed summaries and the printed preliminary contrast do not represent the frozen paired-seed design and are invalid. The preliminary contrast was not interpreted.

## Correction and disposition

The evaluator now receives the current block and evaluates only that block's validation and test episodes. The model, training streams, condition definitions, validation selection rule, endpoints, energy budget, test seed rules, and statistical summaries are unchanged. The correction is implementation-only and was made after a structural verifier failure, without inspecting biological outcomes or using the invalid numerical contrast to change the protocol.

The first run is preserved in `data/results/M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1/invalid_initial_execution/` for audit. Its outputs are not canonical evidence. The corrected run is separately generated in `canonical/` from the same frozen seed rules and must pass the original row-count checks plus an independent full rerun before reporting results.

## Provenance

The initial frozen runner hash and preflight remain in Git history and `PREFLIGHT.json`. The corrected runner and verifier hashes are recorded in `PREFLIGHT_CORRECTED_01.json`. This follow-up remains post-result exploratory because its question and budget were motivated by earlier M2 outcomes.
