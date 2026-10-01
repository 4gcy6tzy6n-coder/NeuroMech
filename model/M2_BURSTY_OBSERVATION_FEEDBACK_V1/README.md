# M2 bursty-observation feedback placement V1

`run_experiment.py` executes the frozen artificial task in [`CONTRACT.md`](../../summery/M2_BURSTY_OBSERVATION_FEEDBACK_V1/CONTRACT.md). The empty canonical output directory must first receive `PREFLIGHT.json`; that file pins the contract and runner hashes before outcome generation.

```bash
python3 model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/run_experiment.py \
  --output-dir data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical --preflight
python3 model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/run_experiment.py \
  --output-dir data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical
python3 model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/analyze_results.py \
  data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical
python3 model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/verify_results.py \
  data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical \
  --contract summery/M2_BURSTY_OBSERVATION_FEEDBACK_V1/CONTRACT.md \
  --runner model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/run_experiment.py
python3 model/M2_BURSTY_OBSERVATION_FEEDBACK_V1/plot_results.py \
  data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical \
  --output-dir data/results/M2_BURSTY_OBSERVATION_FEEDBACK_V1/canonical/figures
```

The independent verifier checks the full seed × burst-condition × episode × policy grid, parameter/update accounting, pinned sources, and recomputes the primary paired crossed-bootstrap contrasts. Result interpretation belongs in `summery/`; episode and fit data belong in `data/results/`.
