# Failure and limitation log

- **Outcome exposure:** the task and contrast were motivated by earlier M2 results. Six pilot seed blocks were inspected before the full run. The full run uses disjoint seeds but remains outcome-informed exploratory work.
- **Dose shape:** state-input advantage was already positive at zero actuator reversals and was largest at p_reverse=.25, not .40. The planned linear interpretation of a simple monotonic dose response would be unsupported; report the prespecified .40-versus-0 interaction as-is and retain all four dose levels.
- **Control scope:** the reactive policy is not parameter matched. Equal parameter counts among learned arms do not equalize optimization dynamics or effective capacity.
- **Yoke scope:** the recipient-yoke distribution is matched at each time step and excludes fixed points, but it breaks episode-specific state/trajectory correspondence. It does not isolate a biological feedback pathway.
- **Task scope:** reversal is an imposed synthetic actuator disturbance. It is not a measured property of the worm motor system and the simulator is not a validated organism model.
- **Inference scope:** training seed block is the inferential unit. Episodes and time steps are nested and cannot be treated as independent replicates. Bootstrap intervals quantify variation across these training blocks only.
- **Claim boundary:** this is an artificial-system result. It neither validates the biological circuit nor establishes broad transfer or a general AI principle.
