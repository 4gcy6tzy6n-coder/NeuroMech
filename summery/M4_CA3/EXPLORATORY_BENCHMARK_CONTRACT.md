# M4 CA3 Partial-Cue Recall: Exploratory Artificial Benchmark Contract

**Status:** post-result method-correction follow-up; exploratory and literature-informed, not confirmatory. This v2 protocol follows two retained v1 runs.  
**Biological claim under study:** some rodent spatial-memory paradigms support recovery of a learned representation from partial cues, with CA3 involvement. The specific recurrent-attractor explanation remains contested and is not isolated by the cited interventions.  
**Artificial question:** when does recurrent associative completion recover the intended stored pattern from incomplete/noisy cues, and how does it compare with exact exemplar retrieval?

## Scope boundary

This benchmark tests an algorithmic abstraction. It does not simulate rodent place cells, CA3 plasticity, DG input, or the water-maze task. A result cannot validate or refute the biological CA3 mechanism. Because the exact exemplar decoder is Bayes-optimal for the benchmark's uniform stored-pattern prior and known cue-noise model, the recurrent network is not expected to beat it on target-identification accuracy. The useful comparison is the accuracy/cost tradeoff and the recurrent network's own failure region, not a win manufactured against a weak baseline.

## Frozen benchmark

- Generate independent random bipolar memories (`-1/+1`) of width `N=120`; memory count is `P/N ∈ {0.05, 0.10, 0.15, 0.20}` (rounded to at least one pattern).
- For each seed and memory load, query 10 stored memories. Reveal a uniformly sampled fraction `{0.2, 0.4, 0.6, 0.8, 1.0}` of cue bits. Independently flip each revealed bit with probability `{0.0, 0.1, 0.2}`. Hidden bits remain unknown, not zero-valued evidence.
- Use 25 independent memory-set seeds. Within each set, every arm receives identical target memories and cue masks/noise draws.
- **Recurrent associative arm:** classic Hebbian Hopfield weights `J = XᵀX/N`, zero diagonal; initialize observed cue bits to their possibly corrupted values and erased bits to zero; asynchronously update **all** units in deterministic seed-shuffled order without clamping, allowing recurrent dynamics to correct noisy cue bits. Set a unit to the sign of its field; if the field is exactly zero retain its current value, using `+1` if that value is zero. Stop on a fixed point or after 100 sweeps.
- **Exact exemplar/Bayes-MAP arm:** select the stored pattern(s) with minimum Hamming distance on visible cue bits, break exact ties uniformly at random, and return the selected complete pattern. Under the frozen uniform memory prior and symmetric independent bit-flip model, nearest Hamming distance is the maximum a posteriori memory decoder.
- Do not tune thresholds, loads, seeds, stopping rules, metrics, or tie handling after seeing results.

## Outcomes

Primary: exact target-pattern recovery rate, paired by memory-set seed and query.  
Secondary: mean bit accuracy, recurrent-output-not-in-memory rate, convergence fraction, and update sweeps. Record cue ambiguity: whether another stored memory is equally or more compatible on the observed cue bits. This output-validity measure is not called a false-attractor rate because it does not establish an attractor's biological status.

Report paired differences with seed-cluster bootstrap 95% intervals; seeds, not individual queries, are the resampling units. Also report algorithm storage estimates separately: explicit exemplars (`P*N` bits, ignoring metadata) versus dense recurrent weights (`N*N*32` bits). Do not describe these as capacity matched.

## Post-result method correction and interpretation rules

The original v1 implementation clamped every observed bit. That is suitable for clean partial cues but prevents any recurrent correction of flipped observed bits. The v1 contract and outputs are retained for audit; v2 removes clamping to make the recurrent arm capable of denoising, while preserving the frozen patterns, loads, cue masks, noise rates, MAP comparator, seed count, and outcomes. Since this change followed inspection of v1 results, v2 is an exploratory method-correction follow-up and not confirmatory evidence.

- If the recurrent arm underperforms exact exemplar retrieval, conclude only that this classic Hebbian implementation is inferior on this synthetic task under the stated cost model.
- If it wins any cell, inspect whether the advantage survives cue-ambiguity stratification and memory-cost accounting before proposing any transfer claim.
- Any follow-up architecture, training rule, cue regime, or threshold change is a new post-result experiment with a new contract.
- No biological endpoint, E3/E4 status, or NMI-readiness claim is produced by this benchmark.

## Biological source boundary

Nakazawa et al. (2002) reported impaired partial-cue spatial recall after adult CA3-specific NMDA receptor deletion: <https://doi.org/10.1126/science.1071795>. Neunuebel & Knierim (2014) reported CA3 ensemble representations coherent with degraded input: <https://doi.org/10.1016/j.neuron.2013.11.017>. Mei et al. (2011) reported preserved full- and partial-cue recall after NMDA-receptor disruption under their protocol: <https://doi.org/10.1371/journal.pone.0019326>. These studies differ in protocol and do not directly isolate CA3 recurrent-collateral computation.
