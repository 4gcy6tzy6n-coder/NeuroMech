# Verification — DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1

`model/DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1/verify_outputs.py` completed successfully after the model run. It independently rechecked the downloaded preview count and every local SHA-256/Zenodo MD5, checked the contract/source/runner/output digests, verified no scene-group leakage across splits, checked row counts and finite learned-model outputs, and recomputed both primary scene-group bootstrap contrasts from the archived metric table.

Verified counts: 201 source previews; train/validation/test groups 141/30/30; 21,600 per-model-seed prediction rows; 9,600 aggregated metric rows; 30 held-out test scene groups. Both recomputed primary contrasts and confidence intervals matched `summary.json` within numerical tolerance.

The experiment itself was run with Python warnings treated as errors. The artifact verification does not establish that the renderer approximates natural flight or that the computer-vision baseline is state of the art.
