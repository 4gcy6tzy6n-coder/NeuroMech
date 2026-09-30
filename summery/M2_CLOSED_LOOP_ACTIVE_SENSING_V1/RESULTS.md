# M2 closed-loop active-sensing transfer V1 — results

**Status:** exploratory synthetic benchmark. The task and outcomes were informed by earlier M2 experiments. This is not a biological validation or a confirmatory test.

## Main result

The mode-gain filter reduced aligned-condition mean distance relative to the constant-gain ablation: `distance(constant) − distance(mode) = +0.03617` (crossed 95% bootstrap interval `[+0.02959, +0.04258]`; 20/20 trained-seed means positive). The mode filter's mean distance was `0.28436` and success rate was `19.4%`, compared with `0.32053` and `8.4%` for the constant-gain filter.

That narrow advantage did not extend to the stronger recurrent controls. In ALIGNED, the generic additive RNN reached mean distance `0.20710` (success `69.9%`), the bilinear RNN `0.25015` (success `46.7%`), and the GRU `0.26547` (success `43.8%`). A Bayesian posterior-mean observer under the same greedy controller reached `0.14296` (success `86.7%`). The Bayesian observer is model-based and not capacity matched; it is not an optimal active-sensing policy.

Transfer depended strongly on the observation mapping. In INDEPENDENT, the mode filter had higher mean distance than the constant-gain filter (`0.38406` vs `0.33106`), and in REVERSED it was also worse (`0.47153` vs `0.34678`). Under REVERSED, the Bayesian observer stayed at its uninformative prior because the greedy controller held its initial motor mode; this is a controller-induced information deadlock, not evidence that Bayesian updating itself failed.

## Interpretation

This closed-loop test does not support a claim that the biological state-gating abstraction is a generally superior controller. It shows a small conditional advantage over the direct constant-gain ablation in the aligned synthetic environment, while generic recurrent controls perform better. The loop matters: an estimator's behavior changes motor actions, which changes later observations, so estimator-only prediction metrics did not determine closed-loop task performance.

The result motivates a separately frozen follow-up that tests information-seeking control, but that would be a new, outcome-informed exploratory version. V1 outcomes and contract remain unchanged. The target, sensory channel, motor dynamics, and reward are artificial; no prospective biological experiment was performed.

## Reproducibility

- Task contract: [`CONTRACT.md`](CONTRACT.md)
- Runner, finalizer and verifier: [`model/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/`](../../model/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/)
- Machine-readable outcomes and checksums: [`data/results/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/`](../../data/results/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/)
- Verification: `python3 model/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/verify_results.py` (`184,320` unique episode-policy rows; checksums and primary bootstrap reproduced).
