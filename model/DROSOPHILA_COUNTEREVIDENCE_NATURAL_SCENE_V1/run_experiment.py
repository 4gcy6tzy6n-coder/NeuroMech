#!/usr/bin/env python3
"""Pixel-sequence transfer pilot using CC0 panoramic scene previews."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
import platform
import random
from pathlib import Path

import numpy as np
from PIL import Image
import scipy
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = "DROSOPHILA_COUNTEREVIDENCE_NATURAL_SCENE_V1"
CONTRACT = ROOT / f"summery/{EXPERIMENT}/CONTRACT.md"
ACQ = ROOT / "data/raw/drosophila_counterevidence_natural_scenes/source_manifest.json"
IMAGE_DIR = ROOT / "data/raw/drosophila_counterevidence_natural_scenes/previews"
OUT = ROOT / f"data/results/{EXPERIMENT}"
T, W, H = 30, 72, 20
TRAIN_COVERAGES = (0.25, 0.50)
TEST_COVERAGES = (0.25, 0.50, 0.75, 0.90)
N_REPS_TRAIN, N_REPS_VAL, N_REPS_TEST = 8, 8, 10
TRAIN_SEED, VAL_SEED, TEST_SEED = 100_031_001, 200_041_001, 300_051_001
MODEL_SEEDS = (61001, 61002, 61003)
EPOCHS, BATCH, LR, PATIENCE = 15, 64, 1e-3, 3
BOOTSTRAPS, BOOT_SEED = 20000, 73001
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_scene_split(files):
    # Group numbered capture variants such as *_1 and *_2 so sibling views stay together.
    groups = {}
    import re
    for path in files:
        stem = path.name.removesuffix(".preview.jpg")
        slug = re.sub(r"_\d+$", "", re.sub(r"^hdrihaven_\d+_", "", stem))
        groups.setdefault(slug, []).append(path)
    ranked = sorted(groups, key=lambda slug: hashlib.sha256(("DCE-NATURAL-2026|" + slug).encode()).hexdigest())
    n = len(ranked)
    train_cut, val_cut = int(round(.70 * n)), int(round(.85 * n))
    group_split = {slug: ("train" if i < train_cut else "validation" if i < val_cut else "test")
                   for i, slug in enumerate(ranked)}
    rows = []
    for slug, paths in groups.items():
        for p in paths:
            rows.append((p, slug, group_split[slug]))
    return sorted(rows, key=lambda x: x[0].name)


def load_scenes():
    files = sorted(IMAGE_DIR.glob("*.preview.jpg"))
    if len(files) != 201:
        raise RuntimeError(f"Expected 201 acquired previews, found {len(files)}")
    split_rows = stable_scene_split(files)
    scenes = []
    for path, group, split in split_rows:
        with Image.open(path) as image:
            image = image.convert("L")
            width, height = image.size
            # Retain the central 105-degree band used for the fly-like panoramic field.
            image = image.crop((0, int(height * .2083), width, int(height * .7917)))
            image = image.resize((W, H), Image.Resampling.BICUBIC)
            a = np.asarray(image, dtype=np.float32) / 255.0
        scenes.append({"path": path, "scene_id": path.stem.replace(".preview", ""),
                       "group": group, "split": split, "image": a})
    return scenes


def sample_shift(rng, forced_direction):
    sign = int(forced_direction)
    speed = float(rng.uniform(.22, .85))
    phase = float(rng.uniform(0, 2 * np.pi))
    omega = float(rng.uniform(.035, .11))
    t = np.arange(T, dtype=np.float32)
    drift = sign * speed * t + .45 * np.sin(phase + omega * t)
    return drift, sign, speed


def periodic_sample(row, positions):
    x = np.arange(W, dtype=np.float32)
    xp = np.concatenate([x, [float(W)]])
    fp = np.concatenate([row, [row[0]]])
    pos = np.mod(positions, W)
    return np.interp(pos, xp, fp).astype(np.float32)


def standardize(row):
    return (row - row.mean()) / max(float(row.std()), 1e-5)


def render_episode(scene, label, coverage, seed, forced_direction):
    rng = np.random.default_rng(seed)
    img = scene["image"]
    bg_row = int(rng.integers(4, H - 4))
    patch_row = int(rng.integers(0, H))
    while patch_row == bg_row:
        patch_row = int(rng.integers(0, H))
    base = img[bg_row].copy()
    patch = img[patch_row].copy()
    shifts, direction, speed = sample_shift(rng, forced_direction)
    frames = []
    if label == 1:  # global rotation
        for s in shifts:
            frames.append(standardize(periodic_sample(base, np.arange(W) - s)))
    else:
        width = int(np.clip(round(coverage * W), 2, W - 1))
        start = int(rng.integers(0, W))
        patch_source = periodic_sample(patch, np.arange(width, dtype=np.float32) + rng.uniform(0, W))
        for s in shifts:
            frame = base.copy()
            idx = np.mod(start + np.rint(s).astype(int) + np.arange(width), W)
            frame[idx] = patch_source
            frames.append(standardize(frame))
    x = np.stack(frames).astype(np.float32)
    return x, {"scene_id": scene["scene_id"], "scene_group": scene["group"],
               "label": int(label), "coverage": float(coverage), "motion_seed": int(seed),
               "direction": direction, "speed": speed}


def static_texture_evidence(x):
    # Explicit stationary-pattern detector: texture + low temporal variation.
    temporal = np.mean(np.abs(np.diff(x, axis=0)), axis=0)
    spatial = np.mean(np.abs(np.diff(x, axis=1, append=x[:, :1])), axis=0)
    mask = (temporal < 0.18) & (spatial > 0.10)
    return float(mask.mean())


def make_split(scenes, split, coverages, n_reps, base_seed):
    subset = [s for s in scenes if s["split"] == split]
    xs, cues, metadata = [], [], []
    for scene_i, scene in enumerate(subset):
        for coverage in coverages:
            for label in (0, 1):
                for rep in range(n_reps):
                    seed = base_seed + scene_i * 100000 + int(coverage * 1000) * 100 + label * 10 + rep
                    direction = 1 if rep % 2 == 0 else -1
                    x, meta = render_episode(scene, label, coverage, seed, direction)
                    meta["stationary_texture_evidence"] = static_texture_evidence(x)
                    xs.append(x)
                    cues.append(meta["stationary_texture_evidence"])
                    metadata.append(meta)
    return np.stack(xs), np.asarray(cues, np.float32), metadata


class SpaceInvariantCNN(nn.Module):
    """Small reimplementation of source CNNSpaceInv (30 temporal channels, circular 1D spatial conv)."""
    def __init__(self, use_counterevidence=False):
        super().__init__()
        self.conv = nn.Conv1d(T, 4, kernel_size=3, padding=1, padding_mode="circular")
        self.readout = nn.Conv1d(4, 2, kernel_size=1)
        self.use_counterevidence = use_counterevidence
        if use_counterevidence:
            self.raw_inhibitory_gain = nn.Parameter(torch.tensor(-1.0))

    def forward(self, x, cue=None):
        h = torch.relu(self.conv(x))
        logits = self.readout(h).sum(dim=-1)
        if self.use_counterevidence:
            if cue is None:
                raise ValueError("counterevidence arm requires cue")
            gain = -torch.nn.functional.softplus(self.raw_inhibitory_gain)
            logits[:, 1] = logits[:, 1] + gain * cue
        return logits


def make_shuffled_cue(cue, metas, seed):
    out = cue.copy()
    rng = np.random.default_rng(seed)
    strata = {}
    for i, meta in enumerate(metas):
        # Keep the cue's broad coverage dependence, but destroy its episode/class alignment.
        key = (meta["coverage"], meta["scene_group"])
        strata.setdefault(key, []).append(i)
    for ids in strata.values():
        if len(ids) < 2:
            ids = [i for i, m in enumerate(metas) if m["coverage"] == metas[ids[0]]["coverage"]]
        vals = out[ids].copy()
        rng.shuffle(vals)
        out[ids] = vals
    return out


def train_one(x, cue, y, xv, cuev, yv, seed, use_ce, shuffled=False):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)
    ctrain = make_shuffled_cue(cue, TRAIN_META, seed + 1) if shuffled else cue.copy()
    cval = make_shuffled_cue(cuev, VAL_META, seed + 2) if shuffled else cuev.copy()
    model = SpaceInvariantCNN(use_counterevidence=use_ce).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    dataset = TensorDataset(torch.from_numpy(x), torch.from_numpy(ctrain), torch.from_numpy(y))
    loader = DataLoader(dataset, batch_size=BATCH, shuffle=True, generator=torch.Generator().manual_seed(seed))
    xt = torch.from_numpy(xv).to(DEVICE)
    ct = torch.from_numpy(cval).to(DEVICE)
    yt = torch.from_numpy(yv).to(DEVICE)
    best, best_epoch, stale, best_state = math.inf, 0, 0, None
    for epoch in range(EPOCHS):
        model.train()
        for xb, cb, yb in loader:
            xb, cb, yb = xb.to(DEVICE), cb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad(set_to_none=True)
            loss = nn.functional.cross_entropy(model(xb, cb if use_ce else None), yb)
            loss.backward(); optimizer.step()
        model.eval()
        with torch.no_grad():
            val_loss = float(nn.functional.cross_entropy(model(xt, ct if use_ce else None), yt).item())
        if val_loss < best - 1e-5:
            best, best_epoch, stale = val_loss, epoch + 1, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= PATIENCE:
                break
    model.load_state_dict(best_state)
    return model, best_epoch, best


def correlation_shift(a, b, radius=3):
    scores = []
    for shift in range(-radius, radius + 1):
        aa = np.roll(a, shift)
        if np.std(aa) < 1e-6 or np.std(b) < 1e-6:
            scores.append(-1.0)
        else:
            scores.append(float(np.corrcoef(aa, b)[0, 1]))
    return int(np.argmax(scores) - radius), max(scores)


def flow_coherence(x):
    shifts = []
    centers = np.arange(W)
    offsets = np.arange(-2, 3)
    displacement = np.arange(-3, 4)
    index = (centers[:, None] + offsets[None, :]) % W
    for t in range(T - 1):
        a = x[t, index]
        a0 = a - a.mean(axis=1, keepdims=True)
        anorm = np.sqrt(np.sum(a0 * a0, axis=1))
        scores = []
        for d in displacement:
            b = x[t + 1, (index + d) % W]
            b0 = b - b.mean(axis=1, keepdims=True)
            bnorm = np.sqrt(np.sum(b0 * b0, axis=1))
            denom = anorm * bnorm
            corr = np.divide(np.sum(a0 * b0, axis=1), denom,
                             out=np.full(W, -1.0, dtype=np.float32), where=denom > 1e-6)
            scores.append(corr)
        scores = np.stack(scores)
        best_idx = np.argmax(scores, axis=0)
        best_score = scores[best_idx, np.arange(W)]
        valid = (anorm > .08) & (best_score > .2)
        shifts.extend(displacement[best_idx[valid]].tolist())
    if not shifts:
        return 0.0
    vals, counts = np.unique(shifts, return_counts=True)
    return float(counts.max() / counts.sum())


def choose_threshold(scores, labels, target_sensitivity=.90):
    candidates = np.unique(scores)
    candidates = np.concatenate(([candidates.min() - 1e-6], candidates, [candidates.max() + 1e-6]))
    valid = []
    for threshold in candidates:
        sens = float(np.mean(scores[labels == 1] >= threshold))
        if sens >= target_sensitivity:
            valid.append((float(threshold), sens))
    return max(valid, key=lambda z: z[0])


def scene_bootstrap(contrast_by_scene, seed=BOOT_SEED):
    values = np.asarray(list(contrast_by_scene.values()), dtype=float)
    rng = np.random.default_rng(seed)
    draws = values[rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))].mean(axis=1)
    return float(values.mean()), [float(np.quantile(draws, .025)), float(np.quantile(draws, .975))]


# Filled only in main after rendering. Explicit globals keep the per-arm fit signature compact.
TRAIN_META, VAL_META = [], []


def main():
    global TRAIN_META, VAL_META
    OUT.mkdir(parents=True, exist_ok=True)
    scenes = load_scenes()
    split_counts = {s: sum(x["split"] == s for x in scenes) for s in ("train", "validation", "test")}
    if min(split_counts.values()) < 20:
        raise RuntimeError(f"too few independent panorama groups: {split_counts}")
    groups_by_split = {s: {x["group"] for x in scenes if x["split"] == s} for s in split_counts}
    if any(groups_by_split[a] & groups_by_split[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise RuntimeError("scene-family leakage across data splits")
    with (OUT / "scene_split_manifest.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["scene_id", "scene_group", "split", "filename_sha256"])
        writer.writeheader()
        for s in scenes:
            writer.writerow({"scene_id": s["scene_id"], "scene_group": s["group"], "split": s["split"],
                             "filename_sha256": hashlib.sha256(s["path"].name.encode()).hexdigest()})
    xtr, ctr, TRAIN_META = make_split(scenes, "train", TRAIN_COVERAGES, N_REPS_TRAIN, TRAIN_SEED)
    xv, cv, VAL_META = make_split(scenes, "validation", (.50,), N_REPS_VAL, VAL_SEED)
    xte, cte, metate = make_split(scenes, "test", TEST_COVERAGES, N_REPS_TEST, TEST_SEED)
    ytr = np.asarray([m["label"] for m in TRAIN_META], np.int64)
    yv = np.asarray([m["label"] for m in VAL_META], np.int64)
    yte = np.asarray([m["label"] for m in metate], np.int64)

    # Flow-only baseline; threshold selected on validation to meet the same sensitivity target.
    flow_val = np.asarray([flow_coherence(x) for x in xv])
    flow_test = np.asarray([flow_coherence(x) for x in xte])
    flow_threshold, flow_val_sens = choose_threshold(flow_val, yv)
    flow_pred = (flow_test >= flow_threshold).astype(np.int64)

    predictions = []
    model_info = []
    checkpoint_dir = Path(__file__).resolve().parent / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for arm, use_ce, shuffled in (("AUTHOR_STYLE_CNN", False, False),
                                  ("COUNTEREVIDENCE_MODEL", True, False),
                                  ("SHAM_CHANNEL_CNN", True, True)):
        # Sham channel is trained/evaluated on cue values independently permuted within coverage strata.
        for seed in MODEL_SEEDS:
            model, best_epoch, best_val = train_one(xtr, ctr, ytr, xv, cv, yv, seed,
                                                    use_ce=use_ce, shuffled=shuffled)
            cue_eval = make_shuffled_cue(cte, metate, seed + 3) if shuffled else cte
            model.eval()
            with torch.no_grad():
                xt = torch.from_numpy(xte).to(DEVICE)
                ctensor = torch.from_numpy(cue_eval).to(DEVICE)
                score = model(xt, ctensor if use_ce else None)[:, 1].cpu().numpy()
                probability = torch.softmax(model(xt, ctensor if use_ce else None), dim=1)[:, 1].cpu().numpy()
                if use_ce:
                    # Ablation counterfactual: same fitted model and input, stationary channel set to zero.
                    ablated = model(xt, torch.zeros_like(ctensor))[:, 1].cpu().numpy()
                else:
                    ablated = np.full_like(score, np.nan)
            valcue = make_shuffled_cue(cv, VAL_META, seed + 2) if shuffled else cv
            with torch.no_grad():
                val_score = model(torch.from_numpy(xv).to(DEVICE),
                                  torch.from_numpy(valcue).to(DEVICE) if use_ce else None)[:, 1].cpu().numpy()
            threshold, val_sensitivity = choose_threshold(val_score, yv)
            for i, meta in enumerate(metate):
                ablated_pred = int(ablated[i] >= threshold) if use_ce else ""
                predictions.append({**meta, "arm": arm, "model_seed": seed,
                    "score_global_rotation": float(score[i]), "threshold": threshold,
                    "p_global_rotation": float(probability[i]),
                    "prediction_global_rotation": int(score[i] >= threshold),
                    "val_sensitivity": val_sensitivity,
                    "score_after_cue_ablation": float(ablated[i]) if use_ce else "",
                    "prediction_after_cue_ablation": ablated_pred})
            model_info.append({"arm": arm, "seed": seed, "epochs_run": best_epoch,
                "best_validation_cross_entropy": best_val, "validation_sensitivity": val_sensitivity,
                "parameters": sum(p.numel() for p in model.parameters()),
                "counterevidence_gain": (float((-nn.functional.softplus(model.raw_inhibitory_gain)).item()) if use_ce else None)})
            torch.save({k: v.detach().cpu() for k, v in model.state_dict().items()},
                       checkpoint_dir / f"{arm}_seed_{seed}.pt")

    with (OUT / "per_example_predictions.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(predictions[0]))
        writer.writeheader(); writer.writerows(predictions)

    # Evaluate image-clustered metrics; model initializations are averaged within each scene/condition.
    rows = []
    arm_names = ["AUTHOR_STYLE_CNN", "COUNTEREVIDENCE_MODEL", "SHAM_CHANNEL_CNN", "FLOW_FIELD_COHERENCE"]
    prediction_lookup = {}
    for r in predictions:
        prediction_lookup.setdefault((r["arm"], r["motion_seed"]), []).append(r)
    for i, meta in enumerate(metate):
        for arm in arm_names:
            if arm == "FLOW_FIELD_COHERENCE":
                pred = int(flow_pred[i])
                score = float(flow_test[i])
                probability = float(flow_test[i])
            else:
                seed_predictions = prediction_lookup[(arm, meta["motion_seed"])]
                pred = int(np.mean([r["prediction_global_rotation"] for r in seed_predictions]) >= .5)
                score = float(np.mean([r["score_global_rotation"] for r in seed_predictions]))
                probability = float(np.mean([r["p_global_rotation"] for r in seed_predictions]))
            rows.append({"arm": arm, "scene_id": meta["scene_id"], "scene_group": meta["scene_group"],
                         "coverage": meta["coverage"], "label": int(meta["label"]),
                         "prediction": pred, "score": score, "probability": probability,
                         "flow_score": float(flow_test[i]),
                         "stationary_texture_evidence": meta["stationary_texture_evidence"]})
    with (OUT / "scene_metrics_long.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

    # Metrics by scene and coverage and primary high-coverage paired contrasts.
    scene_cell = {}
    for arm in arm_names:
        for coverage in TEST_COVERAGES:
            for scene in sorted({m["scene_id"] for m in metate}):
                rr = [r for r in rows if r["arm"] == arm and r["coverage"] == coverage and r["scene_id"] == scene]
                y = np.asarray([r["label"] for r in rr]); p = np.asarray([r["prediction"] for r in rr])
                if len(rr):
                    scene_cell[(arm, coverage, scene)] = {
                        "balanced_accuracy": float(.5 * (np.mean(p[y == 0] == 0) + np.mean(p[y == 1] == 1))),
                        "object_motion_fpr": float(np.mean(p[y == 0] == 1)),
                        "global_rotation_sensitivity": float(np.mean(p[y == 1] == 1))}
    primary = {}
    test_scenes = sorted({m["scene_id"] for m in metate})
    test_groups = sorted({m["scene_group"] for m in metate})
    for comparator in ("AUTHOR_STYLE_CNN", "SHAM_CHANNEL_CNN"):
        contrasts = {}
        for group in test_groups:
            group_scenes = [s for s in test_scenes if next(m["scene_group"] for m in metate if m["scene_id"] == s) == group]
            vals = []
            for cov in (.75, .90):
                vals.extend(scene_cell[("COUNTEREVIDENCE_MODEL", cov, scene)]["object_motion_fpr"] -
                            scene_cell[(comparator, cov, scene)]["object_motion_fpr"] for scene in group_scenes)
            contrasts[group] = float(np.mean(vals))
        mean, ci = scene_bootstrap(contrasts, BOOT_SEED + len(primary))
        primary[f"CE_minus_{comparator}_high_coverage_object_motion_FPR"] = {
            "mean": mean, "scene_group_bootstrap_95_ci": ci, "n_test_scene_groups": len(contrasts)}
    flow_contrasts = {}
    for group in test_groups:
        group_scenes = [s for s in test_scenes if next(m["scene_group"] for m in metate if m["scene_id"] == s) == group]
        vals = []
        for cov in (.75, .90):
            vals.extend(scene_cell[("COUNTEREVIDENCE_MODEL", cov, scene)]["object_motion_fpr"] -
                        scene_cell[("FLOW_FIELD_COHERENCE", cov, scene)]["object_motion_fpr"] for scene in group_scenes)
        flow_contrasts[group] = float(np.mean(vals))
    flow_mean, flow_ci = scene_bootstrap(flow_contrasts, BOOT_SEED + 3)
    cell_means = {}
    cue_ablation = {}
    for arm in arm_names:
        cell_means[arm] = {}
        for cov in TEST_COVERAGES:
            vals = [scene_cell[(arm, cov, scene)] for scene in test_scenes]
            rr = [r for r in rows if r["arm"] == arm and r["coverage"] == cov]
            yy = np.asarray([r["label"] for r in rr]); pp = np.asarray([r["probability"] for r in rr])
            from sklearn.metrics import roc_auc_score
            auc = float(roc_auc_score(yy, pp)) if len(np.unique(yy)) == 2 else float("nan")
            cell_means[arm][str(cov)] = {**{k: float(np.mean([v[k] for v in vals])) for k in vals[0]},
                                          "roc_auc_clip_ensemble_descriptive": auc}
    for cov in TEST_COVERAGES:
        vals = [r for r in predictions if r["arm"] == "COUNTEREVIDENCE_MODEL" and r["coverage"] == cov]
        by_episode = {}
        for r in vals:
            by_episode.setdefault(r["motion_seed"], []).append(r)
        ep_rows = []
        for seed, rs in by_episode.items():
            ep_rows.append((int(rs[0]["label"]), int(np.mean([r["prediction_after_cue_ablation"] for r in rs]) >= .5)))
        ay = np.asarray([x[0] for x in ep_rows]); ap = np.asarray([x[1] for x in ep_rows])
        cue_ablation[str(cov)] = {
            "balanced_accuracy": float(.5 * (np.mean(ap[ay == 0] == 0) + np.mean(ap[ay == 1] == 1))),
            "object_motion_fpr": float(np.mean(ap[ay == 0] == 1)),
            "global_rotation_sensitivity": float(np.mean(ap[ay == 1] == 1))}
    result = {
        "experiment": EXPERIMENT,
        "status": "COMPLETED_EXPLORATORY_POST_RESULT_TRANSFER_BENCHMARK",
        "primary": primary,
        "secondary_flow_baseline": {"CE_minus_FLOW_FIELD_COHERENCE_high_coverage_object_motion_FPR": {
            "mean": flow_mean, "scene_group_bootstrap_95_ci": flow_ci,
            "n_test_scene_groups": len(flow_contrasts)}},
        "cell_means": cell_means,
        "counterevidence_channel_ablation": cue_ablation,
        "split_group_counts": {split: len({s["group"] for s in scenes if s["split"] == split}) for split in ("train", "validation", "test")},
        "split_image_counts": split_counts,
        "flow_validation_sensitivity": flow_val_sens,
        "model_info": model_info,
        "device": DEVICE,
        "task": {"train_coverages": TRAIN_COVERAGES, "validation_coverages": [.50],
                 "test_coverages": TEST_COVERAGES, "episodes_train": len(xtr),
                 "episodes_validation": len(xv), "episodes_test": len(xte),
                 "frame_shape": [T, W], "scene_cluster_is_unit": True},
        "interpretation_boundary": "Rendered one-dimensional panoramic image sequences; not real videos, not biological outcome data, and not independent biological validation.",
    }
    result_path = OUT / "summary.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n")
    manifest = {"experiment": EXPERIMENT, "contract_sha256": sha256(CONTRACT),
        "source_manifest_sha256": sha256(ACQ), "runner_sha256": sha256(Path(__file__)),
        "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "torch": torch.__version__, "device": DEVICE,
        "acquired_preview_count": len(scenes), "preview_total_bytes": sum(s["path"].stat().st_size for s in scenes),
        "all_preview_files_sha256": {s["path"].name: sha256(s["path"]) for s in scenes},
        "checkpoint_sha256": {p.name: sha256(p) for p in sorted(checkpoint_dir.glob("*.pt"))},
        "output_sha256": {p.name: sha256(p) for p in (OUT / "per_example_predictions.csv", OUT / "scene_metrics_long.csv", OUT / "scene_split_manifest.csv", result_path)}}
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
