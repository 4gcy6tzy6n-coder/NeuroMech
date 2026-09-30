# M5 Delayed Teaching Signal Benchmark — Exploratory Results

**Classification:** post-result exploratory synthetic study. The first run was not sufficient to attribute a benefit to eligibility; v2 and v3 method corrections were made after inspecting prior outputs. Do not call the result confirmatory.

## Biological claim and boundary

Kimpo et al. paired optogenetic climbing-fiber stimulation with a conditioned stimulus and induced learned eyeblink responses; shifting the CS–US interval shifted response timing. Silva et al. later showed that timed CF inhibition during the airpuff teaching event blocked delay eyeblink learning while sparing the unconditioned reflex, and that CF stimulation could substitute for the sensory US. The CF-inhibition behavioral contrast involved four mice per condition; the paper also discusses competing instructive pathways and tool-specific complications. These results support a causal, task-bounded role for CF/complex-spike teaching events in associative eyeblink learning; they do not specify the exact plasticity equation or establish a universal cerebellar learning rule. [Kimpo et al., 2014](https://doi.org/10.7554/eLife.02076); [Silva et al., 2024](https://doi.org/10.1038/s41593-024-01594-7).

## v3 benchmark result

Thirty seeded synthetic classification tasks were run. Each had 3,000 sequential cues, 1,000 held-out cues, 64 fixed features, four classes, delayed labels at 1/4/16/64 steps, and identical trainable linear readouts across the online methods. The local trace was `e_t = 0.98 e_(t-1) + φ(x_t)`; v3 unit-normalized each cue feature and normalized the eligibility vector using only its current state.

| Delay | Norm-matched trace | No trace | Exact replay | Batch logistic |
|---:|---:|---:|---:|---:|
| 1 | 0.610 | 0.254 | 0.762 | 0.929 |
| 4 | 0.599 | 0.258 | 0.762 | 0.929 |
| 16 | 0.552 | 0.238 | 0.762 | 0.929 |
| 64 | 0.393 | 0.256 | 0.761 | 0.929 |

The primary paired contrast, norm-matched trace minus no-trace accuracy averaged equally across the four delays, was `+0.2868`; seed-cluster bootstrap 95% interval `[+0.2712, +0.3010]` (30 independent task seeds). All four per-delay intervals were positive. The trace remained below exact replay at every delay and below batch logistic at every delay. Performance degraded with the longest delay.

## Interpretation

This supports one limited algorithmic statement: in this synthetic stream, preserving decaying recent feature eligibility improved delayed-label credit assignment relative to applying the delayed error to the current unrelated cue, even after matching update-vector norms. It does **not** demonstrate superiority to exact replay, backpropagation through time, or broader online-learning algorithms. Exact replay retained the target cue representation; batch logistic received the full labeled dataset. The trace's memory advantage (`O(64)` state versus `O(D×64)` replay features) comes with a large accuracy cost, especially at delay 64.

The v1 unnormalized-trace gain was partly confounded by larger update norms; v2 attempted norm matching but read the target feature's norm; v3 removed this information leak by unit-normalizing features and using only the local trace norm. All versions and outputs are retained separately. Since the fixes followed earlier outcomes, v3 remains exploratory. No biological endpoint was analyzed and no biological mechanism was validated by the model.

## Artifacts

- `DELAYED_TEACHING_SIGNAL_CONTRACT.md` — v3 post-result method-correction contract.
- `DELAYED_TEACHING_SIGNAL_CONTRACT_v1.md` and `_v2.md` — prior protocol versions retained.
- `run_delayed_teaching.py` — benchmark implementation.
- `results_v3_local_norm_correction/learning_curves.csv` — all run/arm/delay checkpoints.
- `results_v3_local_norm_correction/summary.json` — paired effect estimates and intervals.
- `results_v1_unnormalized_trace/` — first run retained.
- `results_v2_target_norm_reference/` — intermediate norm-matched run retained.
- `SHA256SUMS.txt` — artifact digests.
