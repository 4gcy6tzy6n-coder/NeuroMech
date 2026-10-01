# M2 recipient-specific motor-feedback yoke — results

**Classification:** post-result exploratory artificial mechanism-transfer study. The question was prompted by earlier M2 source-model and transfer outcomes. This is not an independent confirmatory study, biological validation, or evidence of general AI benefit.

## Primary result

In the training-range condition (target-switch hazard `1/120`, missingness `0.50`), the recipient's own motor-feedback signal reduced tracking MSE relative to the cross-agent yoke that preserved the exact cohort-level motor-signal distribution at each timestep. The primary contrast `MSE(CROSS_AGENT_YOKE) − MSE(SELF)` was **+0.04143** (crossed seed/episode bootstrap 95% interval **[+0.03901, +0.04383]**); all **32/32** seed-block means were positive.

| Arm | Mean held-out tracking MSE | Difference from SELF (95% crossed interval) |
|---|---:|---:|
| `SENSORY_SELF` | 0.26069 | — |
| `SENSORY_CROSS_AGENT_YOKE` | 0.30212 | +0.04143 [+0.03901, +0.04383] |
| `OUTPUT_SITE_PERSISTENCE` | 0.26485 | +0.00416 [+0.00340, +0.00494] |
| `NO_FEEDBACK` | 0.26486 | +0.00417 [+0.00342, +0.00498] |
| `GENERIC_RNN_1H` | 0.30511 | +0.04441 [+0.04290, +0.04590] |
| `ORACLE_RELATIVE_ERROR` | 0.23021 | −0.03048 [−0.03194, −0.02905] |

The three-parameter sensory-site model also had lower MSE than the three-parameter generic recurrent controller in the primary condition. The task-aware oracle remained substantially better. The sensory-site versus output/no-feedback differences were small in absolute MSE even though their crossed intervals excluded zero; they should not be described as a large control advantage.

## Operating boundary

The self-versus-yoke contrast was positive in all nine hazard/missingness cells and grew with faster target switching and more missing sensation. At the slowest hazard (`1/240`) with 75% missing observations, however, sensory-site feedback had higher MSE than both output persistence (`0.21512` versus `0.19365`) and no feedback (`0.19432`). The same pattern appeared at the training hazard with 75% missingness (`0.34040` versus `0.32031` and `0.32026`). Thus recipient-specific contingency is robustly useful relative to the yoke in this task, while placing the signal at the sensory update does not dominate simpler direct controls across every environment regime.

## Interpretation

The new discriminator holds the signal's empirical cohort distribution fixed at every time step and changes its recipient assignment. In the tested simulator, breaking the correspondence between motor signal and the recipient's own sensory/action history increased tracking error. This supports a **recipient-specific contingency effect** in this artificial closed-loop task. It does not show that the worm implements the same equation or that contingency is the only mechanism behind the contrast: the yoke also breaks alignment with recipient-specific latent target and observation history.

This experiment advances an existing adaptive tracking transfer result by adding the source-model-motivated cross-agent counterfactual. It is not a wholly independent task-family replication: it reuses the sparse-sensation tracking environment and model equations, with fresh training and evaluation seeds. All claims remain post-result exploratory and artificial.

## Strengths and failure lessons

- The self and yoke arms use the same fitted sensory-site controller, recipient observations, training, optimizer budget, and action rule. The donor assignment is a bijective derangement, fixed before scoring.
- Across 288 seed × condition blocks and 69,120 block-time points, the yoke's sorted timestep signal values exactly matched the self-feedback cohort values; no recipient donated to itself.
- All learned controllers have three parameters, share the same pre-generated training minibatches, and receive the same number of updates and sequence tokens. The task-aware oracle is clearly labeled as an unmatched reference.
- The self-feedback advantage over the yoke is large and consistent, but the direct placement and no-feedback margins are small; the task-aware oracle wins in every condition. These comparisons must not be collapsed into a single “mechanism wins” statement.
- A run verifier initially expected five separately fitted learned arms because it counted the yoke as its own fit. Inspection showed that the yoke correctly reuses the fitted self-feedback controller; the verifier was corrected to expect four fits per seed. No experiment runner or outcome file changed in that correction, and the verifier then passed all structural, audit, resource, contrast, bootstrap and hash checks.

## Reproducibility

The independent full rerun passed the verifier. `PREFLIGHT.json`, `episode_results.csv`, `yoke_signal_audit.csv`, and `summary.json` were byte-identical to canonical outputs. All non-runtime fields in 128 training-fit rows also matched; only `training_seconds` is expected to vary. See [REPRODUCIBILITY.json](../../data/results/M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1/REPRODUCIBILITY.json).

The plotted primary contrast and descriptive task grid are available as editable PDF/SVG and 600-dpi PNG/TIFF in [the figure bundle](../../data/results/M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1/figures/). Static source checks, strict panel alignment, 5-pt PDF text audit, and strict collision audit passed; see `FIGURE_MANIFEST.json` in that folder.

## Claim boundary

The supported result is conditional: in this action-coupled synthetic tracking task, recipient-specific previous-motor feedback at the sensory update outperformed a distribution-preserving cross-agent replay and a parameter-matched one-state RNN at the tested primary condition. It did not beat the task-aware oracle, and the direct sensory-site placement advantage disappeared or reversed under slow switching with heavy missingness. This is neither animal-level evidence nor a general AI advantage. It motivates an independently implemented task family with an equally strong task-aware reference and a preregistered estimate of when recipient-specific feedback helps versus harms.
