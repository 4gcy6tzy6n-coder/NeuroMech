# M7 — Eligibility benefit across temporal correlation and delay

**Classification:** post-result exploratory study. The M5 results were known before this phase diagram. It changes the independent sweep and adds regression, but remains the same synthetic random-feature teacher family. It is not biological validation and makes no algorithm-novelty claim.

## Required correction to the planned analysis

The first run summary pooled classification accuracy differences with regression MSE differences. Those units are not commensurate, so its reported pooled interaction (`+0.1124`) is **invalid and excluded**. Raw episode/task outcomes are retained. The corrected analysis reports classification and regression separately, pairing 30 task seeds within each objective. No cross-objective pooled effect is reported.

## Main result: correlation interacts with delay

Trace benefit is `trace accuracy − no-trace accuracy` for classification, and `no-trace MSE − trace MSE` for regression. Positive values favor eligibility. The table gives the benefit at `rho=0` and `rho=0.9`; the difference is bootstrap-tested across paired task seeds.

| Objective | Delay | Benefit at rho 0 | Benefit at rho 0.9 | rho 0 minus rho 0.9 (95% CI) |
|---|---:|---:|---:|---:|
| Classification | 1 | +0.3561 | −0.1380 | +0.4940 [+0.4674, +0.5214] |
| Classification | 4 | +0.3443 | −0.0643 | +0.4086 [+0.3870, +0.4304] |
| Classification | 16 | +0.2989 | +0.2117 | +0.0872 [+0.0620, +0.1126] |
| Classification | 64 | +0.1246 | +0.2244 | −0.0998 [−0.1263, −0.0759] |
| Regression | 1 | +0.0060 | −0.0035 | +0.00947 [+0.00890, +0.01003] |
| Regression | 4 | +0.0055 | −0.0012 | +0.00666 [+0.00627, +0.00706] |
| Regression | 16 | +0.0045 | +0.0059 | −0.00141 [−0.00169, −0.00113] |
| Regression | 64 | +0.0021 | +0.0073 | −0.00522 [−0.00590, −0.00456] |

Averaging the four delays **within each objective**, the rho-0 minus rho-0.9 interaction was +0.2225 accuracy points for classification (95% CI [+0.2075, +0.2373]) and +0.00238 normalized-task MSE units for regression ([+0.00216, +0.00260]). Both averages are positive, but both hide a reliable reversal at long delays. Thus input autocorrelation can reduce the trace's relative benefit at short delays; it does not uniformly replace eligibility across longer delays.

## Strong comparator and practical meaning

Exact replay outperformed the eligibility trace in all 48 objective × rho × delay cells. The result therefore identifies a boundary against the current-input no-trace update, not an advantage over exact memory or offline learning. The trace's performance–memory tradeoff remains unresolved: this study does not match the memory budget or compare against truncated replay, BPTT, or a trained recurrent network.

## Biological interpretation

The cited mouse conditioning interventions support a task-bounded causal role for timed climbing-fiber/complex-spike teaching events. They do not establish the `gamma=0.98` trace, its interaction with AR(1) input statistics, or any of these synthetic classification/regression tasks. E-prop and other online eligibility methods already exist; this result is a boundary-condition analysis, not a new learning algorithm.

## Failed analysis experience

Do not average unlike outcome scales just because they have been sign-oriented to “higher is better.” Sign alignment does not make accuracy points commensurate with MSE. The raw run summary and pooled per-seed file are retained as `summary.json` and `primary_seed_contrasts.csv` for audit; use `analysis_v1_objective_stratified.json` and `analyze_results.py` for interpretable objective-specific estimates.
