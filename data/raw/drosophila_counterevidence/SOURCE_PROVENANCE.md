# Source provenance — Drosophila visual counterevidence

- Primary paper: Tanaka et al. (2023), *Neural mechanisms to incorporate visual counterevidence in self-movement estimation*, Current Biology 33:4960–4979.e7, DOI `10.1016/j.cub.2023.10.011`.
- Public experimental-data DOI: `10.5061/dryad.bcc2fqzjz` (Dryad version dated 2023-10-30; repository page lists a 13.80 GB archive and README). The raw archive was not downloaded for this synthetic AI-side stress test; no biological outcome rows were used.
- Author ANN source: `https://github.com/ClarkLabCode/SelfMotionDetectionML`, inspected at commit `75a7051a0e310311b9295afe0a2b5c68f25eba9d` on 2026-09-30. The author code uses a spatially invariant CNN on 30-frame, 72-position visual inputs and reports natural-scene-based self-motion/object-motion classification.
- Author Mi4 detector source: `https://github.com/ClarkLabCode/Mi4Decoder`, inspected HEAD `a0f50210404229ae3a1465cf65a8b6bc31a0b0fe` on 2026-09-30.
- This experiment generates reduced-order synthetic local-motion features. It neither copies nor redistributes author code or Dryad data.
