#!/usr/bin/env python3
"""Independent structural, protocol, and primary-estimate verifier."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ID = "M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1"
DEFAULT = ROOT / "data" / "results" / ID / "canonical"
SEEDS = set(range(410000, 410032))
ARMS = {"SENSORY_SITE_FEEDBACK", "OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "GENERIC_RNN_1H", "ORACLE_RELATIVE_ERROR"}
HAZARDS = (1/240, 1/120, 1/40)
MISSING = (0.25, 0.50, 0.75)
BOOTSTRAPS, BOOT_SEED = 10_000, 20261018


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_csv(p):
    with p.open(newline="") as f:
        return list(csv.DictReader(f))


def build_matrix(rows, competitor):
    seed_order = sorted(SEEDS)
    mat = np.full((len(SEEDS), 256), np.nan, dtype=np.float64)
    other = np.full_like(mat, np.nan)
    si = {s: i for i, s in enumerate(seed_order)}
    for r in rows:
        if np.isclose(float(r["condition_hazard"]), 1/120, rtol=0, atol=1e-12) and np.isclose(float(r["condition_missing"]), 0.5, rtol=0, atol=1e-12):
            i, j = si[int(r["training_seed"])], int(r["episode_id"])
            if r["arm"] == "SENSORY_SITE_FEEDBACK": mat[i, j] = float(r["tracking_mse"])
            if r["arm"] == competitor: other[i, j] = float(r["tracking_mse"])
    if not np.isfinite(mat).all() or not np.isfinite(other).all():
        raise ValueError("missing primary paired values")
    return other - mat


def independent_bootstrap(mat):
    rng = np.random.default_rng(BOOT_SEED)
    vals = np.empty(BOOTSTRAPS)
    for start in range(0, BOOTSTRAPS, 200):
        b = min(200, BOOTSTRAPS-start)
        seeds = rng.integers(0, mat.shape[0], size=(b, mat.shape[0]))
        episodes = rng.integers(0, mat.shape[1], size=(b, mat.shape[1]))
        vals[start:start+b] = mat[seeds[:, :, None], episodes[:, None, :]].mean(axis=(1, 2))
    return float(mat.mean()), np.quantile(vals, [0.025, 0.975]), int((mat.mean(axis=1) > 0).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, default=DEFAULT)
    args = ap.parse_args()
    out = args.results_dir.resolve()
    contract = ROOT / "summery" / ID / "CONTRACT.md"
    runner = ROOT / "model" / ID / "run_experiment.py"
    analyzer = ROOT / "model" / ID / "analyze_results.py"
    verifier = Path(__file__).resolve()
    plotter = ROOT / "model" / ID / "plot_results.py"
    pre = json.loads((out / "PREFLIGHT.json").read_text())
    meta = json.loads((out / "RUN_METADATA.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    manifest = json.loads((out / "MANIFEST.json").read_text())
    if pre["outcomes_computed"] is not False:
        raise ValueError("preflight does not attest outcome-blind setup")
    if pre["contract_sha256"] != sha(contract) or pre["runner_sha256"] != sha(runner):
        raise ValueError("preflight source hashes do not match current contract/runner")
    expected_sources = {str(p.relative_to(ROOT)): sha(p) for p in (contract, runner, analyzer, verifier, plotter)}
    if manifest["source_files"] != expected_sources:
        raise ValueError("final source manifest mismatch")
    for name, record in manifest["files"].items():
        p = out / name
        if p.stat().st_size != record["bytes"] or sha(p) != record["sha256"]:
            raise ValueError(f"manifest mismatch: {name}")
    for name, record in manifest["artifacts"].items():
        p = out.parent / name
        if p.stat().st_size != record["bytes"] or sha(p) != record["sha256"]:
            raise ValueError(f"artifact manifest mismatch: {name}")
    rows = load_csv(out / "episode_results.csv")
    fits = load_csv(out / "training_results.csv")
    expected_episode_count = len(SEEDS) * len(HAZARDS) * len(MISSING) * 256 * len(ARMS)
    if len(rows) != expected_episode_count or len(fits) != 32 * 4:
        raise ValueError(f"row-count mismatch: episode={len(rows)}, fit={len(fits)}")
    keys = set()
    for r in rows:
        key = (int(r["training_seed"]), float(r["condition_hazard"]), float(r["condition_missing"]), int(r["episode_id"]), r["arm"])
        if key in keys: raise ValueError("duplicate episode key")
        keys.add(key)
        if key[0] not in SEEDS or key[1] not in HAZARDS or key[2] not in MISSING or not 0 <= key[3] < 256 or key[4] not in ARMS:
            raise ValueError(f"out-of-grid episode key: {key}")
        for col in ("tracking_mse", "tracking_mae", "action_energy"):
            value = float(r[col])
            if not np.isfinite(value) or value < 0: raise ValueError(f"invalid {col}")
    for f in fits:
        if int(f["training_seed"]) not in SEEDS or f["arm"] not in ARMS - {"ORACLE_RELATIVE_ERROR"}:
            raise ValueError("unexpected training row")
        if int(f["parameter_count"]) != 3 or int(f["updates"]) != 100 or int(f["batch_size"]) != 16 or int(f["sequence_steps_per_fit"]) != 100*16*240:
            raise ValueError("training budget or parameter-count mismatch")
        params = json.loads(f["parameters_json"])
        if len(params) != 3 or not np.isfinite(params).all(): raise ValueError("invalid fitted parameters")
    contrasts = {}
    for competitor in ("GENERIC_RNN_1H", "OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK"):
        mean, ci, npos = independent_bootstrap(build_matrix(rows, competitor))
        reported = summary["primary_generic_control"] if competitor == "GENERIC_RNN_1H" else summary["direct_matched_controls"][competitor]
        if not np.isclose(mean, reported["mean_competitor_minus_sensory_mse"], atol=1e-14):
            raise ValueError(f"mean contrast mismatch for {competitor}")
        if not np.allclose(ci, reported["crossed_bootstrap_ci95"], atol=1e-14):
            raise ValueError(f"bootstrap mismatch for {competitor}")
        if npos != reported["positive_training_seed_count"]:
            raise ValueError(f"positive-seed count mismatch for {competitor}")
        contrasts[competitor] = {"mean_competitor_minus_sensory_mse": mean,
                                 "crossed_bootstrap_ci95": ci.tolist(), "positive_seed_count": npos}
    grid = summary["grid"]
    if grid["episode_rows"] != expected_episode_count or grid["training_rows"] != 128:
        raise ValueError("summary grid counts mismatch")
    print(json.dumps({"status": "PASS", "verified_episode_rows": len(rows), "verified_training_fits": len(fits),
                      "contrasts": contrasts, "verified_figure_artifacts": len(manifest["artifacts"]),
                      "source_hashes": expected_sources}, indent=2))


if __name__ == "__main__":
    main()
