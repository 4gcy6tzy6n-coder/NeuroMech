# Natural-scene preview provenance

- Dataset: HDRIHaven public-domain high dynamic range panoramic image dataset, Zenodo record `10.5281/zenodo.1285800`, version `v1.0.1`.
- Dataset record: https://zenodo.org/records/1285800
- API metadata: https://zenodo.org/api/records/1285800
- Original panoramas: 201 equirectangular 360° × 180° scenes; this experiment acquires only the JPEG preview files, not the approximately 47 GB full-resolution HDR tree.
- License: Zenodo API metadata labels the record `other-pd`; its description states the underlying HDRIHaven images were published under CC0. The complete public metadata and each file's official MD5 are pinned in `source_manifest.json`; local SHA-256 digests are recorded there too.
- Acquisition: `model/DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1/acquire_previews.py` downloads only `.preview.jpg` files and validates each byte size and Zenodo MD5 before writing it. The run obtained 201/201 previews (154,737,391 bytes).
- Image use: each JPEG preview is cropped to the central 105° elevation band, converted to grayscale, and resampled for a controlled renderer. These are scene backgrounds, not source fly recordings or biological outcomes.
