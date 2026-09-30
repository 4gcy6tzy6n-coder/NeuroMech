# V5 failure and limitation log

- **Prior translation offset found:** V3/V4 selected the sensory position one sample earlier than the pinned MATLAB source. V5 corrects the index and leaves historical artifacts immutable.
- **Full parity not established:** MATLAB/Octave was unavailable. Random-number generation, smoothing boundary conventions, and other numerical details remain unverified against MATLAB execution.
- **Control mismatch persists:** the selected single motor-feedback coefficient does not match the sensory-site arm's mean, median, upper-tail, and long-run fraction simultaneously. The positive directional contrast therefore cannot be attributed specifically to feedback placement after persistence is controlled.
- **Outcome-informed lineage:** M2/V3/V4 results were already inspected before V5. The result is exploratory and not an independent confirmatory test.
- **Scope:** all uncertainty is over source-model seed blocks and imposed noise scales; it is not animal-level biological inference and does not show AI transfer.
- **Next repair:** use a separately developed flexible persistence yoke/control, freeze an adequacy report before direction outcomes, and compare under the same source-corrected implementation. Do not repeat scalar fitting as if it resolves the confound.
