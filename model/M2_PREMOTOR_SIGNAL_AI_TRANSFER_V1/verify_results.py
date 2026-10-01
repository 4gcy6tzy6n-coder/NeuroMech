#!/usr/bin/env python3
"""Independent completeness and contrast-arithmetic audit for the AI transfer probe."""
from __future__ import annotations

import hashlib, itertools, json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_PREMOTOR_SIGNAL_AI_TRANSFER_V1"
SEEDS = tuple(range(62000, 62020))
SIZES = (32, 128, 512)
CONDITIONS = ("ALIGNED", "UNINFORMATIVE", "REVERSED")
ARMS = ("PREMOTOR_FILTER", "NO_CUE_FILTER", "GRU_CUE", "GRU_NO_CUE", "CUE_ONLY",
        "PREMOTOR_FILTER_YOKED_CUE", "GRU_CUE_YOKED_CUE")
BOOT, BOOT_SEED = 20000, 20261014


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def recompute_effect(frame, arm_a, arm_b, size, condition):
    diffs = []
    for seed in SEEDS:
        block = frame[(frame.training_seed == seed) & (frame.train_size == size) & (frame.condition == condition)]
        means = {}
        for arm in (arm_a, arm_b):
            vals = block.loc[block.arm == arm, "auc"].dropna().to_numpy(float)
            means[arm] = float(vals.mean()) if len(vals) else np.nan
        if np.isfinite(means[arm_a]) and np.isfinite(means[arm_b]):
            diffs.append(means[arm_a] - means[arm_b])
    x = np.asarray(diffs)
    if not len(x):
        return None
    rng = np.random.default_rng(BOOT_SEED)
    boot = x[rng.integers(0, len(x), (BOOT, len(x)))].mean(axis=1)
    return {"mean": float(x.mean()), "ci": np.quantile(boot, [0.025, 0.975]).tolist(),
            "positive": int((x > 0).sum()), "n": len(x)}


def main():
    out = ROOT / "data/results" / EXP
    contract = ROOT / "summery" / EXP / "CONTRACT.md"
    runner = ROOT / "model" / EXP / "run_experiment.py"
    manifest = json.loads((out / "manifest.json").read_text())
    errors = []
    if manifest["contract_sha256"] != sha(contract): errors.append("contract hash mismatch")
    if manifest["runner_sha256"] != sha(runner): errors.append("runner hash mismatch")
    for name, expected in manifest["sha256"].items():
        if name == "POSTRUN_VERIFICATION.json":
            continue
        if sha(out / name) != expected: errors.append(f"manifest checksum mismatch: {name}")
    metrics = pd.read_csv(out / "episode_metrics.csv")
    fits = pd.read_csv(out / "training_metrics.csv")
    expected_rows = len(SEEDS) * len(SIZES) * len(CONDITIONS) * 128 * len(ARMS)
    if len(metrics) != expected_rows: errors.append(f"episode row count {len(metrics)} != {expected_rows}")
    if len(fits) != len(SEEDS) * len(SIZES) * 4: errors.append(f"fit row count {len(fits)} unexpected")
    if metrics.duplicated(["training_seed", "train_size", "condition", "episode_id", "arm"]).any():
        errors.append("duplicate episode key")
    if set(metrics.arm.unique()) != set(ARMS): errors.append("arm inventory mismatch")
    for arm, count in (("PREMOTOR_FILTER", 6), ("NO_CUE_FILTER", 6), ("GRU_CUE", 45), ("GRU_NO_CUE", 45)):
        vals = fits.loc[fits.arm == arm, "parameter_count"].unique()
        if len(vals) != 1 or int(vals[0]) != count: errors.append(f"parameter count mismatch: {arm}")
    finite_auc = metrics.auc.dropna().to_numpy(float)
    if np.any((finite_auc < 0) | (finite_auc > 1)): errors.append("AUC outside [0,1]")
    if metrics.brier.isna().any() or np.any((metrics.brier < 0) | (metrics.brier > 1)):
        errors.append("invalid Brier score")
    summary = json.loads((out / "summary.json").read_text())
    pairs = {"cue_value_structured": ("PREMOTOR_FILTER", "NO_CUE_FILTER"),
             "structured_vs_generic": ("PREMOTOR_FILTER", "GRU_CUE"),
             "cue_value_generic": ("GRU_CUE", "GRU_NO_CUE"),
             "recipient_contingency_structured": ("PREMOTOR_FILTER", "PREMOTOR_FILTER_YOKED_CUE")}
    checked = 0
    for label, (arm_a, arm_b) in pairs.items():
        actual = recompute_effect(metrics, arm_a, arm_b, 128, "ALIGNED")
        saved = summary["primary_contrasts"][label]
        if actual is None:
            errors.append(f"primary contrast not estimable: {label}")
            continue
        for key, val in (("arm_a_minus_arm_b", actual["mean"]),
                         ("seed_bootstrap_95pct_interval", actual["ci"]),
                         ("positive_seed_count", actual["positive"]), ("seed_blocks", actual["n"])):
            if not np.allclose(np.asarray(saved[key]), np.asarray(val), rtol=0, atol=1e-12):
                errors.append(f"summary contrast mismatch: {label}/{key}")
        checked += 1
    if errors:
        raise SystemExit("FAIL\n" + "\n".join(errors))
    print(json.dumps({"status": "PASS", "episode_rows": len(metrics), "fit_rows": len(fits),
                      "primary_contrasts_recomputed": checked, "finite_auc_episode_rows": int(metrics.auc.notna().sum()),
                      "output_manifest_files_verified": len(manifest["sha256"])}, indent=2))


if __name__ == "__main__": main()
