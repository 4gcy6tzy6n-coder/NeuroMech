#!/usr/bin/env python3
"""Independent schema, hash, parameter-count, and primary-estimand audit."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/results/M2_CROSS_TASK_STATE_FEEDBACK_V1"
SEEDS = tuple(range(42000, 42020))
EPISODES = 512
CONDITIONS = ("ALIGNED", "INDEPENDENT", "REVERSED")
POLICIES = ("MODE_GAIN_FILTER", "GENERIC_RNN_1D", "CONSTANT_GAIN_FILTER", "CURRENT_OBSERVATION", "KALMAN_LINEAR_REFERENCE")
N_BOOT = 20_000
BOOT_SEED = 20261005


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def ci(matrix: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOT_SEED)
    n_seed, n_episode = matrix.shape
    means = np.empty(N_BOOT, dtype=np.float64)
    chunk = 100
    for start in range(0, N_BOOT, chunk):
        count = min(chunk, N_BOOT - start)
        si = rng.integers(0, n_seed, size=(count, n_seed))
        ei = rng.integers(0, n_episode, size=(count, n_episode))
        for k in range(count):
            means[start + k] = matrix[np.ix_(si[k], ei[k])].mean()
    return [float(x) for x in np.quantile(means, [.025, .975])]


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    out = parser.parse_args().results_dir.expanduser().resolve()
    metrics_path = out / "episode_metrics.csv"
    params_path = out / "learned_parameters.csv"
    training_path = out / "training_curves.csv"
    summary_path = out / "summary.json"
    manifest_path = out / "run_manifest.json"
    metric_rows = read(metrics_path)
    params = read(params_path)
    curves = read(training_path)
    summary = json.loads(summary_path.read_text())
    manifest = json.loads(manifest_path.read_text())

    expected_count = len(SEEDS) * EPISODES * len(CONDITIONS) * len(POLICIES)
    assert len(metric_rows) == expected_count, f"metric rows {len(metric_rows)} != {expected_count}"
    keys = [(int(r["train_seed"]), r["condition"], int(r["episode_id"]), r["policy"]) for r in metric_rows]
    assert len(keys) == len(set(keys)), "duplicate metric keys"
    assert set(keys) == {(s, c, e, p) for s in SEEDS for c in CONDITIONS for e in range(EPISODES) for p in POLICIES}, "incomplete metric keys"
    assert len(params) == len(SEEDS) * 3
    primary_params = [r for r in params if r["policy"] in {"MODE_GAIN_FILTER", "GENERIC_RNN_1D"}]
    assert all(int(r["n_trainable_parameters"]) == 4 for r in primary_params), "primary parameter count mismatch"
    assert manifest["row_counts"]["episode_metrics"] == len(metric_rows)
    for path in (metrics_path, params_path, training_path, summary_path):
        assert manifest["output_sha256"][path.name] == sha256(path), f"hash mismatch {path.name}"

    aligned: dict[tuple[int, int, str], float] = {}
    for row in metric_rows:
        if row["condition"] == "ALIGNED":
            aligned[(int(row["train_seed"]), int(row["episode_id"]), row["policy"])] = float(row["episode_mse"])
    primary = np.array([
        [aligned[(seed, ep, "GENERIC_RNN_1D")] - aligned[(seed, ep, "MODE_GAIN_FILTER")] for ep in range(EPISODES)]
        for seed in SEEDS
    ])
    interval = ci(primary)
    assert np.isclose(summary["primary"]["mean"], primary.mean(), atol=1e-12)
    assert np.allclose(summary["primary"]["ci95_crossed_bootstrap"], interval, atol=1e-12)
    assert summary["primary"]["positive_seed_means"] == int((primary.mean(axis=1) > 0).sum())

    check = {
        "status": "PASS",
        "checks": ["row_schema_and_completeness", "primary_parameter_count", "output_hashes", "primary_estimate_and_crossed_bootstrap_recomputed"],
        "metric_rows": len(metric_rows), "training_parameter_rows": len(params), "training_curve_rows": len(curves),
        "primary_mean_recomputed": float(primary.mean()), "primary_ci95_recomputed": interval,
        "positive_train_seed_means_recomputed": int((primary.mean(axis=1) > 0).sum()),
        "episode_metrics_sha256": sha256(metrics_path),
    }
    (out / "POSTRUN_VERIFICATION.json").write_text(json.dumps(check, indent=2) + "\n")
    print(json.dumps(check, indent=2))


if __name__ == "__main__":
    main()
