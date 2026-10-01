# Figure contract — M2 bursty-observation feedback placement V1

**Results-level question:** At equal expected observation availability, how does motor-feedback placement perform as missing observations become more temporally clustered, and does the long-burst placement effect survive a stronger recurrent baseline?

**Figure-level claim:** Sensory-site feedback has lower mean tracking error than the tested equal-parameter small controls at each tested burst duration, while the contrast against the 8-unit GRU is unresolved; the result therefore remains bounded to a synthetic placement effect.

**Evidence architecture (quantitative grid):**

- **Panel a — operating range:** MSE versus expected missing-run length for each policy, with 95% bootstrap intervals across the 24 training-seed means. This establishes whether the relative ordering changes as gaps lengthen while showing all five policies.
- **Panel b — decisive long-burst contrasts:** `baseline MSE − sensory-site MSE` at mean missing run 8, with the frozen paired crossed seed/episode 95% intervals for output-site, generic RNN, and GRU. Positive values favor sensory-site feedback; zero indicates no resolved difference. This directly exposes the unresolved strong-baseline comparison.

**Review risks:** The GRU has 321 parameters versus four for each small policy; it is a stronger but not capacity-matched baseline. Panel a intervals summarize seed-level means, while panel b uses the contract’s paired crossed bootstrap. The figure is artificial-task evidence only, not a biological assay.

**Export contract:** Matplotlib/Python only; 177.8 mm maximum width; editable PDF/SVG text and 600-dpi TIFF; 5-pt minimum rendered glyph; alignment gate for the two comparable panels; rendered PDF text and collision audits; canonical episode-level source data remain in `data/results/.../canonical/episode_results.csv`.
