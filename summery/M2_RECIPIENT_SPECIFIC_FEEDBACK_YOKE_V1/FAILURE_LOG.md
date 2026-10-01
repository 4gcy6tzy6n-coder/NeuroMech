# M2 recipient-specific feedback yoke V1 — failure and limitation log

This record preserves implementation corrections and scientific limits for the experiment. The study is post-result exploratory.

## Implementation issue caught before finalization

The first verifier version expected five separately fitted learned arms per seed because it counted `SENSORY_CROSS_AGENT_YOKE` as a separate fit. The yoke intentionally reuses the already fitted `SENSORY_SELF` controller and changes only donor assignment at evaluation. The verifier was corrected to expect four fits per seed; the experiment runner and canonical outcomes were not changed. The corrected verifier passed structural, arithmetic, resource, bootstrap, hash, and yoke checks.

## Figure QA issue caught before delivery

The initial primary-panel annotations were intersected by the vertical zero-reference line. The annotations were moved to the positive side of zero, the figure was re-rendered, and the strict collision audit then passed with no findings. No data or analysis code changed.

## Scientific limits that remain

- The self-versus-yoke contrast breaks alignment with the recipient's entire trajectory, including its target and observation history; it does not isolate a single biological signal pathway.
- The same sparse-tracking task family and model equations were used in earlier M2 work. Fresh seeds make this a new run, not an independent task-family replication.
- The task-aware oracle wins, while direct sensory-site placement and no-feedback differences are small and reverse in some tested conditions.
- The simulator result does not validate worm behavior, biological implementation, or general AI benefit.
