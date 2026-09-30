#!/usr/bin/env python3
"""Independent integrity and primary-statistic verification; never trains a model."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = "DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1"
OUT = ROOT / f"data/results/{EXPERIMENT}"
RAW = ROOT / "data/raw/drosophila_counterevidence_natural_scenes"
MODEL = ROOT / f"model/{EXPERIMENT}"
SUMMARY = json.loads((OUT / "summary.json").read_text())
MANIFEST = json.loads((OUT / "run_manifest.json").read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def close(a, b, tol=1e-12):
    return abs(float(a) - float(b)) <= tol


source = json.loads((RAW / "source_manifest.json").read_text())
assert source["preview_count"] == 201
assert sha(RAW / "source_manifest.json") == MANIFEST["source_manifest_sha256"]
assert sha(MODEL / "run_experiment.py") == MANIFEST["runner_sha256"]
assert sha(ROOT / f"summery/{EXPERIMENT}/CONTRACT.md") == MANIFEST["contract_sha256"]

for file in source["files"]:
    path = RAW / "previews" / file["key"]
    assert path.stat().st_size == file["bytes"]
    assert hashlib.md5(path.read_bytes()).hexdigest() == file["zenodo_md5"]
    assert sha(path) == file["local_sha256"] == MANIFEST["all_preview_files_sha256"][file["key"]]

for name, expected in MANIFEST["output_sha256"].items():
    assert sha(OUT / name) == expected, name
assert sha(OUT / "natural_scene_transfer_summary.png") == MANIFEST["supplementary_plot_sha256"]

with (OUT / "scene_split_manifest.csv").open() as f:
    split_rows = list(csv.DictReader(f))
assert len(split_rows) == 201
split_groups = defaultdict(set)
for row in split_rows:
    split_groups[row["split"]].add(row["scene_group"])
assert not (split_groups["train"] & split_groups["validation"])
assert not (split_groups["train"] & split_groups["test"])
assert not (split_groups["validation"] & split_groups["test"])

with (OUT / "per_example_predictions.csv").open() as f:
    predictions = list(csv.DictReader(f))
assert len(predictions) == 21600
keys = [(r["arm"], r["model_seed"], r["motion_seed"]) for r in predictions]
assert len(keys) == len(set(keys))
assert all(np.isfinite(float(r["score_global_rotation"])) and
           np.isfinite(float(r["p_global_rotation"])) for r in predictions)
assert all(.0 <= float(r["p_global_rotation"]) <= 1.0 for r in predictions)
assert {r["arm"] for r in predictions} == {"AUTHOR_STYLE_CNN", "COUNTEREVIDENCE_MODEL", "SHAM_CHANNEL_CNN"}

with (OUT / "scene_metrics_long.csv").open() as f:
    metrics = list(csv.DictReader(f))
assert len(metrics) == 9600
assert {r["arm"] for r in metrics} == {"AUTHOR_STYLE_CNN", "COUNTEREVIDENCE_MODEL", "SHAM_CHANNEL_CNN", "FLOW_FIELD_COHERENCE"}
cell = defaultdict(list)
for r in metrics:
    cell[(r["arm"], float(r["coverage"]), r["scene_id"])].append(r)
scene_metric = {}
for key, rows in cell.items():
    y = np.asarray([int(r["label"]) for r in rows])
    pred = np.asarray([int(r["prediction"]) for r in rows])
    scene_metric[key] = float(np.mean(pred[y == 0] == 1))
scene_to_group = {r["scene_id"]: r["scene_group"] for r in split_rows if r["split"] == "test"}
test_groups = sorted(set(scene_to_group.values()))

for ordinal, comparator in enumerate(("AUTHOR_STYLE_CNN", "SHAM_CHANNEL_CNN")):
    contrasts = {}
    for group in test_groups:
        scenes = [s for s, g in scene_to_group.items() if g == group]
        vals = [scene_metric[("COUNTEREVIDENCE_MODEL", cov, scene)] - scene_metric[(comparator, cov, scene)]
                for cov in (.75, .90) for scene in scenes]
        contrasts[group] = float(np.mean(vals))
    values = np.asarray(list(contrasts.values()))
    rng = np.random.default_rng(73001 + ordinal)
    draws = values[rng.integers(0, len(values), size=(20000, len(values)))].mean(axis=1)
    found = SUMMARY["primary"][f"CE_minus_{comparator}_high_coverage_object_motion_FPR"]
    assert close(values.mean(), found["mean"])
    assert close(np.quantile(draws, .025), found["scene_group_bootstrap_95_ci"][0])
    assert close(np.quantile(draws, .975), found["scene_group_bootstrap_95_ci"][1])

print(json.dumps({"verified": True, "source_previews": len(source["files"]),
                  "split_groups": {s: len(split_groups[s]) for s in split_groups},
                  "test_groups": len(test_groups), "prediction_rows": len(predictions),
                  "metric_rows": len(metrics), "primary_statistics_recomputed": True,
                  "all_recorded_hashes_checked": True}, indent=2))
