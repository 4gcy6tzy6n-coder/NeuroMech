# M7 — When does an explicit eligibility state add value beyond input autocorrelation?

**Classification:** post-result exploratory study. M5 v1–v3 and the three-generator follow-up were already inspected. This study changes the independent task family from fixed input-generator categories to a predeclared temporal-correlation sweep, and adds a regression objective. It is not confirmatory or biological validation.

## Motivation and biological scope

Timed climbing-fiber/complex-spike signals causally support acquisition of a timed conditioned response in mouse delay eyeblink conditioning (Kimpo et al., 2014, DOI 10.7554/eLife.02076; Silva et al., 2024, DOI 10.1038/s41593-024-01594-7). A local decaying eligibility state is a plausible computational abstraction of how prior synaptic activity remains available when a later teaching signal arrives; the cited experiments do not establish a unique trace equation. Online eligibility-based temporal credit assignment is already established in AI/neuroscience, including e-prop (Bellec et al., Nature Communications 2020, DOI 10.1038/s41467-020-17236-y). This study makes no algorithm-novelty claim.

## Question

When input streams have intrinsic temporal autocorrelation, how does that implicit memory change the benefit of an explicit, fixed eligibility trace for delayed labels? Does the relationship hold under both classification and regression objectives?

## Design

- Temporal correlation coefficients `rho ∈ {0.0, 0.2, 0.4, 0.6, 0.8, 0.9}` define stationary Gaussian AR(1) streams; `rho=0` is IID Gaussian.
- Two fixed teacher/readout objectives: four-class classification (argmax linear teacher) and four-output linear regression.
- Thirty paired task seeds per objective and rho. Each task has a fresh random 32→64 tanh feature map and 64→4 teacher, 3,000 training inputs, and 1,000 independent test inputs.
- Delays `D ∈ {1, 4, 16, 64}`; `learning_rate=0.01`, eligibility decay `gamma=0.98`; all fixed from M5-v3, not tuned here.
- Three online arms with identical trainable readout dimensions and examples: exact replay, norm-matched eligibility trace, and current-input no-trace update. Exact replay is retained as a strong higher-memory reference. A fixed-feature batch solution is not included in this online-mechanism phase diagram; therefore no claim of superiority to offline learning is possible.

## Outcomes

- Classification: held-out accuracy; higher is better.
- Regression: held-out mean-squared error (MSE); lower is better.
- Convert to a common trace-benefit scale: `trace accuracy − no-trace accuracy` for classification; `no-trace MSE − trace MSE` for regression. Positive means the eligibility trace helps.
- Primary interaction: equal-weighted over objectives and delays, `trace benefit at rho=0.0 minus trace benefit at rho=0.9`. Positive means stronger intrinsic input correlation reduces the relative need for an explicit trace.
- Bootstrap the 30 task seeds as paired units; retain all objectives, delays, arms, and rho values within each sampled seed. Report cellwise intervals descriptively without confirmatory multiplicity claims.

## Interpretation boundary

This tests one synthetic teacher/readout family under a controlled correlation sweep. An interaction would describe when the fixed trace helps relative to the current-input update on these tasks; it would not establish biological mechanism validation or general AI superiority. If the trace loses to exact replay, report that resource/performance tradeoff plainly. Do not tune learning rate, gamma, feature map, or select a favorable task subset after seeing results. The experiment ends with this one sweep.
