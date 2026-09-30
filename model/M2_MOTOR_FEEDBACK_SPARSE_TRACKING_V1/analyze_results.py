#!/usr/bin/env python3
"""Summarize the frozen M2 sparse-sensation tracking experiment."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ID = "M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1"
CONTRACT = ROOT / "summery" / ID / "CONTRACT.md"
OUT_DEFAULT = ROOT / "data" / "results" / ID / "canonical"
SEEDS = np.arange(410000, 410032)
ARMS = ("SENSORY_SITE_FEEDBACK", "OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "GENERIC_RNN_1H", "ORACLE_RELATIVE_ERROR")
HAZARDS = (1 / 240, 1 / 120, 1 / 40)
MISSING = (0.25, 0.50, 0.75)
BOOTSTRAPS, BOOT_SEED = 10_000, 20261018


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_rows(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def pair_matrix(rows, condition_hazard: float, condition_missing: float, competitor: str):
    nseed, nepisode = len(SEEDS), 256
    values = np.full((nseed, nepisode, len(ARMS)), np.nan, dtype=np.float64)
    arm_ix = {a: i for i, a in enumerate(ARMS)}
    seed_ix = {int(s): i for i, s in enumerate(SEEDS)}
    for r in rows:
        if (np.isclose(float(r["condition_hazard"]), condition_hazard, rtol=0, atol=1e-12)
                and np.isclose(float(r["condition_missing"]), condition_missing, rtol=0, atol=1e-12)):
            values[seed_ix[int(r["training_seed"])], int(r["episode_id"]), arm_ix[r["arm"]]] = float(r["tracking_mse"])
    if np.isnan(values).any():
        raise ValueError("incomplete paired test grid")
    s = values[:, :, arm_ix["SENSORY_SITE_FEEDBACK"]]
    c = values[:, :, arm_ix[competitor]]
    return c - s


def crossed_bootstrap(mat: np.ndarray):
    # Independently resample training-seed clusters and shared episode IDs.
    rng = np.random.default_rng(BOOT_SEED)
    vals = np.empty(BOOTSTRAPS, dtype=np.float64)
    chunk = 200
    for first in range(0, BOOTSTRAPS, chunk):
        b = min(chunk, BOOTSTRAPS - first)
        si = rng.integers(0, mat.shape[0], size=(b, mat.shape[0]))
        ei = rng.integers(0, mat.shape[1], size=(b, mat.shape[1]))
        picked = mat[si[:, :, None], ei[:, None, :]]
        vals[first:first+b] = picked.mean(axis=(1, 2))
    lo, hi = np.quantile(vals, [0.025, 0.975])
    seed_means = mat.mean(axis=1)
    return {"mean_competitor_minus_sensory_mse": float(mat.mean()),
            "crossed_bootstrap_ci95": [float(lo), float(hi)],
            "positive_training_seed_count": int(np.sum(seed_means > 0)),
            "training_seed_count": int(len(seed_means)),
            "per_training_seed_means": seed_means.tolist()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, default=OUT_DEFAULT)
    args = ap.parse_args()
    out = args.results_dir.resolve()
    rows = read_rows(out / "episode_results.csv")
    fits = read_rows(out / "training_results.csv")
    expected = len(SEEDS) * len(HAZARDS) * len(MISSING) * 256 * len(ARMS)
    if len(rows) != expected:
        raise ValueError(f"expected {expected} episode rows, got {len(rows)}")
    primary = crossed_bootstrap(pair_matrix(rows, 1/120, 0.5, "GENERIC_RNN_1H"))
    controls = {}
    for arm in ("OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK"):
        controls[arm] = crossed_bootstrap(pair_matrix(rows, 1/120, 0.5, arm))
    condition_means = {}
    for h in HAZARDS:
        for p in MISSING:
            key = f"hazard={h:.8g};missing={p:.2f}"
            cond = [r for r in rows if np.isclose(float(r["condition_hazard"]), h, rtol=0, atol=1e-12)
                    and np.isclose(float(r["condition_missing"]), p, rtol=0, atol=1e-12)]
            condition_means[key] = {a: {
                "tracking_mse": float(np.mean([float(r["tracking_mse"]) for r in cond if r["arm"] == a])),
                "tracking_mae": float(np.mean([float(r["tracking_mae"]) for r in cond if r["arm"] == a])),
                "action_energy": float(np.mean([float(r["action_energy"]) for r in cond if r["arm"] == a])),
                "switch_recovery_steps": float(np.mean([float(r["switch_recovery_steps"]) for r in cond if r["arm"] == a and r["switch_recovery_steps"] != ""]))
                    if any(r["arm"] == a and r["switch_recovery_steps"] != "" for r in cond) else None
            } for a in ARMS}
    training_means = {a: {
        "parameter_count": int(np.median([int(r["parameter_count"]) for r in fits if r["arm"] == a])),
        "updates": int(np.median([int(r["updates"]) for r in fits if r["arm"] == a])),
        "sequence_steps_per_fit": int(np.median([int(r["sequence_steps_per_fit"]) for r in fits if r["arm"] == a])),
        "mean_training_seconds": float(np.mean([float(r["training_seconds"]) for r in fits if r["arm"] == a])),
        "mean_initial_loss": float(np.mean([float(r["initial_loss"]) for r in fits if r["arm"] == a])),
        "mean_final_10_update_loss": float(np.mean([float(r["final_10_update_loss"]) for r in fits if r["arm"] == a]))
    } for a in ARMS[:-1]}
    summary = {
        "experiment_id": ID,
        "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_MECHANISM_TRANSFER",
        "primary_condition": {"hazard": 1/120, "missing_rate": 0.5},
        "primary_contrast": "MSE(GENERIC_RNN_1H) - MSE(SENSORY_SITE_FEEDBACK); positive favors sensory-site feedback",
        "primary_generic_control": primary,
        "direct_matched_controls": controls,
        "means_by_condition": condition_means,
        "training_summary": training_means,
        "grid": {"training_seeds": len(SEEDS), "episodes_per_seed_condition_arm": 256,
                 "condition_count": len(HAZARDS) * len(MISSING), "arms": list(ARMS),
                 "episode_rows": len(rows), "training_rows": len(fits)},
        "interpretation_rule": "A sensory-site advantage requires positive primary contrast and positive contrasts against both direct placement and no-feedback controls; even then inference is limited to this artificial task."
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {}
    for p in (out / "PREFLIGHT.json", out / "RUN_METADATA.json", out / "episode_results.csv", out / "training_results.csv", out / "summary.json", out / "REPRODUCIBILITY.json"):
        manifest[p.name] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    result_root = out.parent
    figure_names = ["M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1.svg", "M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1.pdf",
                    "M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1.png", "M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1.tiff",
                    "figure.alignment.json", "collision-audit.json", "collision-audit.pdf",
                    "source-validation.json", "pdf-text-audit.json", "QA.md"]
    artifacts = {}
    for name in figure_names:
        p = result_root / "figures" / name
        artifacts[f"figures/{name}"] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    source_files = [CONTRACT, ROOT / "model" / ID / "run_experiment.py",
                    ROOT / "model" / ID / "analyze_results.py",
                    ROOT / "model" / ID / "verify_results.py",
                    ROOT / "model" / ID / "plot_results.py"]
    (out / "MANIFEST.json").write_text(json.dumps({"experiment_id": ID, "files": manifest, "artifacts": artifacts,
        "source_files": {str(p.relative_to(ROOT)): sha(p) for p in source_files}}, indent=2) + "\n")
    print(json.dumps({"primary": primary, "direct_controls": controls, "grid": summary["grid"]}, indent=2))


if __name__ == "__main__":
    main()
