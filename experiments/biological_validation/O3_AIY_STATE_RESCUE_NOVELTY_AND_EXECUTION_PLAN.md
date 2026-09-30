# O3 — AIY state-pattern rescue: novelty audit and execution plan

**Record ID:** `O3_AIY_STATE_RESCUE_NOVELTY_AUDIT_V1`  
**Date:** 2026-10-01  
**Status:** focused literature audit complete; one integrated prospective biological study is the active execution route. No new biological outcomes were collected in this audit.

## Decision

Proceed with one prospective *C. elegans* AFD–AIY–RIM study. Stop searching for another public dataset as the default next move. The proposed contribution is a computation-specific causal rescue: test whether restoring the normal forward-state temporal pattern in AIY, under RIM perturbation, restores thermosensory gating and forward-run persistence compared with an illumination- and waveform-matched but state-yoked pattern.

The claim must stay narrow. Motor-state-dependent sensory processing, optogenetic control of AIY, and closed-loop stimulus delivery are each established. The potentially distinctive question is whether the *state-contingent timing* of the AIY pattern is sufficient to rescue the particular RIM-dependent thermotaxis computation. A bounded search did not find a direct test of that exact rescue contrast; this is a non-detection in a focused search, not proof of novelty or a “first” claim.

## Evidence audit: facts, inference, and judgement

### Directly reported biological facts

Ji et al. report that AIY activity encodes thermal and locomotor-state information during positive thermotaxis; the locomotor-state component requires RIM. RIM ablation allows thermosensory signals to appear in downstream premotor activity and reduces forward-run persistence. The authors state that the molecular/synaptic route is unresolved, and specifically propose cell-specific SER-2 perturbation or rescue in AIY as a test of tyramine signaling. [Ji et al., *eLife* 2021](https://doi.org/10.7554/eLife.68848).

AIY activity patterns can drive behavior: Kocabas et al. used optogenetic AIY stimulation to evoke virtual chemotaxis and showed that distinct AIY activity patterns can control reversals and gradual turns. Thus general AIY excitation is not an adequate control for a state-code rescue. [Kocabas et al., *Nature* 2012](https://doi.org/10.1038/nature11431).

Motor-state-dependent sensory gating is not unique to the thermotaxis circuit. Kumar et al. showed that turning-associated neurons suppress mechanosensory-evoked reversals during turns, with behavior-triggered perturbations. [Kumar et al., *PLOS Biology* 2023](https://doi.org/10.1371/journal.pbio.3002280).

Dunn et al. reported short-term memory in *C. elegans* using distributed neural oscillation phase and closed-loop, state-timed sensory stimulation with whole-brain imaging and optogenetic perturbation. This makes broad claims about motor state, sensory gating, or state-dependent memory especially unsuitable as the novelty claim. [Dunn et al., *Current Biology* 2025](https://doi.org/10.1016/j.cub.2025.10.018).

AIY-specific SER-2 rescue has been reported for imprinted olfactory aversion, not the RIM-dependent thermotaxis/state-persistence question. It is relevant precedent for cell-specific manipulation, not evidence that SER-2 is the thermotaxis mediator. [Jin et al., *Cell* 2016](https://doi.org/10.1016/j.cell.2016.01.007).

Behavior-triggered closed-loop stimulation in freely moving worms is technically established, including high-throughput methods. That evidence does not itself establish simultaneous AIY calcium measurement, selective AIY stimulation, and controlled thermotaxis waveforms in the same freely moving animal. [Liu et al., *PLOS Biology* 2022](https://doi.org/10.1371/journal.pbio.3001524).

### Inference

Together, the evidence supports a cell-class-level computation: motor-state feedback changes how sensory input is represented and can help sustain a behavioral state in the tested navigation context. A state-contingent AIY rescue could test whether the timing of that sensory-node state is sufficient to restore the function lost after RIM perturbation. It would not identify a unique RIM→AIY synapse, establish the molecular carrier, or prove that an artificial filter is the animal's implementation.

### Research judgement

The broad “corollary discharge gates sensory processing” story is not novel. A paper contribution would have to rest on a direct causal rescue with a temporal-yoking control, same-animal neural/stimulus/behavior alignment, and a separately tested artificial computation. If that exact contrast is infeasible, do not relabel simple AIY activation as an equivalent experiment.

## Integrated prospective study

### Primary biological question

In RIM-perturbed animals undergoing positive thermotaxis, does an AIY activity pattern contingent on the forward state restore forward-run persistence and state-dependent thermosensory representation better than the same pattern delivered at yoked times?

### Core arms

Use a compact factorial design with sham/intact and RIM-perturbed backgrounds. In the RIM-perturbed background compare no light, forward-state-contingent AIY pattern replay, and a temporally yoked or phase-scrambled replay matched for total photon dose, waveform, and exposure duration. Include opsin-negative/light-only controls to measure illumination and heating effects. The state-contingent and yoked arms are the decisive contrast; intact animals define the reference pattern and assay range.

The replay waveform should be estimated from an independent intact-animal calibration cohort, then frozen before the rescue cohort is analyzed. Match the waveform's total energy and marginal timing distribution across the contingent and yoked arms. Do not optimize it against rescue outcomes.

### Measurements and unit of inference

Synchronously record per-worm ID, genotype and perturbation, delivered light, measured temperature, timestamps, AIY calcium, locomotion state, and run/reversal boundaries. The worm is the independent unit. Frames, bouts, temperature cycles, and repeated perturbations are nested within worm and must not be counted as independent animals.

Use one animal-level forward-run persistence summary as the primary behavioral endpoint. A restricted-mean forward-run duration over a fixed observation window is a candidate because run durations can be skewed; the observation window and handling of censored runs must be set from instrument duration and outcome-blind calibration, not selected after seeing the rescue contrast. AIY state-by-temperature coupling is the mechanistic secondary endpoint and target-engagement check.

### Interpretation

- If contingent replay exceeds the matched yoked replay on the animal-level behavior endpoint and restores the preregistered AIY state/thermal interaction, the data support a timing-specific, cell-class-level sufficiency result in this assay.
- If both light patterns improve behavior similarly, the result supports nonspecific AIY stimulation, not the state code.
- If AIY target engagement is absent, the behavioral contrast is technically inconclusive.
- If target engagement succeeds but contingent replay does not outperform the yoked pattern, the state-timing sufficiency hypothesis is not supported in this assay.
- None of these results identifies a single synapse or proves a universal computation.

Before confirmatory collection, use a blinded feasibility/pilot phase to establish optical cross-talk, thermal artifacts, state-detection latency, waveform delivery, and animal-level variance. Determine the final sample size and smallest effect of interest from the pilot plus the minimum behaviorally meaningful difference. Keep pilot animals disjoint from the confirmatory cohort. This is ordinary experimental design needed to make the result interpretable, not a dataset-acquisition gate.

## Artificial transfer linked to this study

The artificial operation should be redefined around the supported evidence as **motor-state-conditioned sensory updating / persistence**, not “motor state encodes sensor reliability.” The latter was an unsupported synthetic assumption in `M2_CROSS_TASK_STATE_FEEDBACK_V1`; retain that run as a boundary test and do not present it as the main biological transfer result.

The next AI study should implement a minimal state-gated update and compare it, under identical training exposure and parameter accounting, with (1) the same controller with the gate removed, (2) a reversed or phase-mismatched gate, (3) a generic recurrent controller, and (4) an exact task-aware Bayesian reference. Evaluate across a navigation task and a distinct sequential decision task, with context-aligned, context-independent, and context-reversed regimes. The key estimand is within-task improvement over the capacity-matched generic controller; do not pool raw outcomes across task families. Run this artificial study alongside protocol feasibility, but keep its conclusions explicitly conditional until the biological rescue succeeds.

## Immediate work and unavoidable external dependency

The repository now has a concrete study question and controls. The next practical work is to resolve rig access and an experienced worm-neurobiology collaborator, then construct a short outcome-blind optical/thermal feasibility pilot. The repo and public literature do not establish that this laboratory resource is available. I cannot manufacture worms, run microscopy, or claim a wet-lab result from simulations. This is the remaining external dependency for the biological half of the NMI-level claim; artificial modeling and analysis can continue in parallel.

## Search scope and limitations

Focused searches covered: Ji et al. 2021 and cited follow-ups; RIM/AIY state-dependent sensory gating; AIY optogenetic activity-pattern manipulation; SER-2 cell-specific rescue; behavior-triggered closed-loop stimulation; and recent *C. elegans* state-dependent memory/whole-brain work. Sources were prioritized from primary papers, PubMed, eLife, Nature, PLOS Biology, and Cell. This was not a systematic review and cannot support an exhaustive “no prior study” claim.

## Source ledger

| Source | Verified contribution | Relevance / limit |
|---|---|---|
| Ji et al. 2021, DOI `10.7554/eLife.68848` | RIM-dependent AIY motor-state coding, thermosensory gating, forward-run persistence; mechanism unresolved. | Direct biological anchor; existing study already establishes broad phenomenon. |
| Kocabas et al. 2012, DOI `10.1038/nature11431` | AIY activity patterns can drive chemotactic behavior. | Requires waveform/time-yoked control; generic excitation is not specific. |
| Kumar et al. 2023, DOI `10.1371/journal.pbio.3002280` | Motor feedback gates mechanosensory response during turns. | Establishes adjacent state-dependent sensory gating in another modality. |
| Dunn et al. 2025, DOI `10.1016/j.cub.2025.10.018` | Distributed oscillator phase and state-timed sensory stimulation support short-term memory. | Recent conceptual and technical overlap; narrows broad novelty. |
| Jin et al. 2016, DOI `10.1016/j.cell.2016.01.007` | AIY SER-2 rescue in developmental olfactory imprinting. | Cell-specific rescue precedent; different behavior and developmental context. |
| Liu et al. 2022, DOI `10.1371/journal.pbio.3001524` | High-throughput behavior-triggered optogenetic stimulation in moving worms. | Supports feasibility of closed-loop stimulation generally, not the exact thermotaxis/AIY/imaging combination. |
