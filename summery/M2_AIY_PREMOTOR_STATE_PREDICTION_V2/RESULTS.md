# Results — M2 AIY premotor-state prediction V2

**Classification:** retrospective, outcome-informed exploratory analysis of five WT and five RIM-ablated animals from Ji et al.'s public constant-temperature traces. V2 follows a target-definition failure in V1; it is not an independent confirmation.

## Primary 2-second result

Using the five recent motor-state samples as baseline, adding current AIY calcium increased per-animal blocked out-of-fold AUC by a WT mean of `0.2098` (five-animal bootstrap 95% interval `[0.1129, 0.2861]`) and by `0.0779` after RIM ablation (`[0.0154, 0.1505]`). The descriptive WT-minus-RIM contrast was `0.1318` (animal bootstrap interval `[0.0163, 0.2357]`; exact 5/5 label permutation reference `p=0.0794`, 252 allocations). These intervals and permutation values are descriptive; five animals per group do not support a strong group-level claim.

AVA showed a larger corresponding increment: `0.3033` in WT versus `0.0804` after RIM ablation; WT-minus-RIM `0.2229` (descriptive animal-bootstrap interval `[0.0626, 0.3732]`; label-permutation reference `p=0.0397`). This internal comparator weakens an AIY-specific interpretation. Current AIY signal contains predictive information about the next labeled motor state conditional on the selected history in this small source cohort, but this reanalysis does not establish unique AIY coding, causal prediction, or a RIM→AIY route.

The primary horizon contained only 6–18 positive samples per animal. Event prevalence was about `0.7%–3.9%`. AUC estimates are therefore sensitive to a small number of events even though time blocks were purged and animals—not frames—were summarized as the biological units. The 0.5- and 5-second horizons are secondary and remain separate; they do not rescue or replace the primary horizon.

## Interpretation and next use

The result is compatible with a broader motor/premotor signal that precedes state transitions, and the AVA pattern cautions against locating the signal specifically to AIY. It motivates a focused model comparison: explicit recent motor-state memory versus neural-state-like recurrent features, with no assumption that the biological signal encodes sensor reliability. It is not an AI-transfer result and cannot by itself justify an NMI-level claim.

V1 and V2 outputs, source workbook hashes, code, and verification are retained under the corresponding `data/results/` and `model/` directories. The source is Ji et al. (2021), [eLife 68848](https://elifesciences.org/articles/68848).
