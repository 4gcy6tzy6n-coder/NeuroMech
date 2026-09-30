# M2 sequential binary-decision transfer V1 — results

**Classification:** post-result exploratory artificial task-transfer test. Prior M2 synthetic outcomes were known; this task uses disjoint seeds and a different target process and outcome. It is not biological validation or confirmatory evidence.

## Result

Twenty paired task seeds compared a state-conditioned gain filter with a constant-gain context-free filter on static hidden left/right targets requiring 32 steps of sequential evidence accumulation. In ALIGNED evaluation, terminal decision accuracy averaged over training sizes 16, 64, 256 and 1024 was **0.7029** for `MODE_GAIN_FILTER` and **0.6385** for `CONSTANT_GAIN_FILTER`. The paired mode-minus-constant difference was **+0.06448** accuracy (95% task-seed bootstrap interval **[+0.05703, +0.07232]**; positive in **20/20** seeds).

| Evaluation mapping | Mode-gain accuracy | Constant-gain accuracy | Bilinear-RNN accuracy | Bayes-oracle accuracy |
|---|---:|---:|---:|---:|
| ALIGNED | 0.7029 | 0.6385 | 0.5891 | 0.8376 |
| INDEPENDENT | 0.6145 | 0.6413 | 0.5494 | 0.7601 |
| REVERSED | 0.5192 | 0.6368 | 0.5063 | 0.8372 |

The aligned benefit was present at every training-set size: mode-minus-constant accuracy differences were +0.0602, +0.0648, +0.0707, and +0.0622 for 16, 64, 256 and 1024 episodes, respectively. In the INDEPENDENT mapping, mode-minus-constant averaged **−0.02678** (95% interval `[−0.03423, −0.01863]`; positive in 1/20 seeds). In REVERSED it averaged **−0.11765** (`[−0.12522, −0.10908]`; 0/20 positive). Thus the same filter that improves aligned decisions becomes harmful when the context-evidence relation is absent or reversed.

The Bayes oracle, which knows the true cue distribution and test mapping, was best in all conditions. The learned state filter remains 13.5 percentage points below it in ALIGNED, showing substantial headroom. The five-parameter bilinear RNN had lower accuracy than the mode-gain model in all three mappings in this fit regime; this comparison changes the update equation and optimization landscape and does not isolate a uniquely biological computation.

## Interpretation

The state-conditioned update's benefit carries from continuous AR(1) estimation to a distinct static-target decision task within the same synthetic context-reliability family. This supports cross-objective generalization of the *artificial operation* under aligned conditions, alongside a strong distribution-mismatch cost. Because the observation/context mapping is imposed by the task generator and is not a measured RIM–AIY property, this does not establish biological-to-AI transfer, broad AI benefit, or NMI readiness.

## Resource accounting and verification

Each learned fit used 250 Adam updates, batch size 16, sequence length 32, and 128,000 sequence-step tokens. Parameter counts were 4 (mode gain), 3 (constant gain), and 5 (bilinear RNN). Mean measured CPU training time per fit was 0.21 s, 0.15 s, and 0.29 s, respectively; timing is hardware-specific. The Bayes oracle is analytical and uses known test mapping/likelihood parameters.

Independent verification passed all **491,520 episode rows** and 240 learned fits, regenerated the held-out streams and recomputed every Bayes-oracle episode metric, reproduced the paired-seed primary contrast and interval, and validated artifact hashes.

## Artifacts

- Contract: [`CONTRACT.md`](CONTRACT.md)
- Runner and independent verifier: [`model/M2_SEQUENTIAL_DECISION_V1/`](../../model/M2_SEQUENTIAL_DECISION_V1/)
- Episode outcomes, training metrics and manifest: [`data/results/M2_SEQUENTIAL_DECISION_V1/`](../../data/results/M2_SEQUENTIAL_DECISION_V1/)
- Prior continuous-estimation comparisons: [M2 V1](../M2_LOW_DATA_GATING_V1/RESULTS.md), [V2](../M2_LOW_DATA_GATING_V2/RESULTS.md), and [V3](../M2_LOW_DATA_GATING_V3/RESULTS.md)
