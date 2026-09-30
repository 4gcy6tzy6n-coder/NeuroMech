# M2 closed-loop active-sensing transfer V1 — failure and limitation log

## 1. Estimator advantage did not carry over to closed-loop control

The mode-gain filter beat the constant-gain ablation in ALIGNED, but the generic additive RNN, bilinear RNN, GRU, and Bayesian observer had lower mean target distance. The primary ablation alone therefore overstates the mechanism's comparative strength if presented without the recurrent controls.

## 2. Mapping shift caused negative transfer

When motor mode no longer predicted an informative observation (`INDEPENDENT`) or the relation was reversed (`REVERSED`), the mode-gain filter underperformed the constant-gain control. This is a material robustness boundary for a mechanism whose benefit depends on a learned state-to-observation relation.

## 3. Greedy action rule can deadlock information gathering

In REVERSED, the exact Bayesian observer began in the uninformative forward mode. Its posterior stayed at the prior, so the common greedy controller held position and never switched into the informative mode. The observer must be described as a Bayesian estimator evaluated under the fixed greedy controller, not as an optimal policy or general oracle. A future active-sensing policy would need an explicit value-of-information or probing rule.

## 4. Scope and design limitations

- This is a one-dimensional, fixed-target toy environment with a hand-designed controller.
- All learned models were trained on ALIGNED exogenous context sequences; test mappings were altered afterward.
- The Bayesian observer is model-based and not capacity matched; learned models have architecture-dependent compute despite similar training data and update counts.
- Outcomes are exploratory because earlier M2 results were already known before this benchmark.
- Synthetic outcomes do not establish the corresponding computation in *C. elegans*, a general AI principle, or publication readiness.

## Implementation note

The observer was initially labeled `KALMAN_ORACLE` in the result rows. That label was inaccurate for this discrete binary-target posterior observer and invited an optimal-policy interpretation. The rows were relabeled `BAYESIAN_OBSERVER`; the data values were unchanged, and the summary and manifest hashes were regenerated from those same episode outcomes. The independent verifier passed after relabeling.
