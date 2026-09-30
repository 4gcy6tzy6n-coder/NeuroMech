# M2 decision context-dose V1 — failure and limitation log

- The learned mode-gain update is strongly harmed by reversed context. At `κ=-0.50`, terminal accuracy is about 12.9 percentage points below the constant-gain ablation.
- The learned mode-gain update remains about 13.3 percentage points below the task-aware Bayes reference at full alignment. The artificial computation is not optimal.
- The benefit boundary is objective- and data-size-dependent. At `κ=+0.20`, the pooled contrast is small; only the 64-example secondary estimate clearly excludes zero. No general data-efficiency claim follows.
- This is not an independent biological or task-family replication. It reuses the same scalar context/evidence construction as prior M2 work and changes the decision objective and context-dose grid.
- Training context/evidence mapping was fixed at full alignment. Test dose levels are distribution shifts; the curve does not compare models retrained at each dose.
- The biological source does not measure the numerical context-to-evidence relation represented by κ. The results characterize an artificial update rule only.
