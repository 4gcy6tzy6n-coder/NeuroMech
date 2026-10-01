# Failure and limitation log — M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1

## Execution incident 01: yoke dispatch bug

The first formal invocation stopped during the first seed block because `CROSS_AGENT_YOKED_SENSORY` was sent through the generic-RNN branch, which referenced parameters absent from the four-parameter yoke controller. The run failed before evaluation and before any outcome metrics were produced or inspected. The incident and correction are preserved in [`EXECUTION_INCIDENT_01.md`](EXECUTION_INCIDENT_01.md). The runner was corrected to use the same sensory-state equation as `SELF_SENSORY`, with recipient-specific yoke signal as the intended difference; no statistical endpoint, sample size, or training schedule changed. A one-update smoke check then passed.

## Scientific and design limits

- The experiment is a synthetic translation, not direct testing of the biological circuit.
- The positive recipient-contingency contrast occurred only in the preregistered `SLOW_TRANSIENT` condition; it did not reproduce in `FAST_TRANSIENT` or either clean condition.
- Output-site feedback and generic recurrence both outperformed the sensory-feedback arm on primary-condition movement MSE; the larger GRU did too. There is no overall AI advantage.
- Parameter counts range from 3 to 297. Results do not establish capacity-matched superiority or compute efficiency.
- Prior M2 results were known before this study. The contract was frozen within this experiment but the study remains exploratory and partially informed at the project level.
- Test episodes are nested within seed blocks; inference uses 32 paired training seed blocks as the resampling unit, not individual frames/episodes as independent seeds.
- The primary interval quantifies seed-block variability for this simulator and does not establish transfer across tasks, environments, or biological preparations.

## Disposition

Retain the corrected canonical run and the failed initial attempt record. Do not describe the first attempt as a scientific null or include it in outcomes. Do not promote this conditional result to a biological claim, a robust feedback-site claim, or a general AI principle. Any follow-up must be separately versioned and must address the unfavorable generic/output/GRU controls and the condition dependence rather than selecting only the successful regime.
