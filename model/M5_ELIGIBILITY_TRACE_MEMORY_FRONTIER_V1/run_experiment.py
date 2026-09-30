#!/usr/bin/env python3
"""Compare eligibility traces with truncated histories and exact delayed replay."""
from __future__ import annotations

import csv
import argparse
import hashlib
import json
import platform
from collections import deque
from pathlib import Path

import numpy as np

from task_generator import MASTER_SEED, N_FEATURES, N_OUTPUT, N_TRAIN, N_TEST, make_task

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "summery/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/CONTRACT.md"
MODEL_DIR = Path(__file__).resolve().parent
OUT = ROOT / "data/results/M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1/canonical"
RHOS, DELAYS, HORIZONS = (0.0, 0.5, 0.9), (4, 16, 64), (1, 2, 4, 8, 16, 32, 64)
SEEDS = range(30, 60)  # Disjoint from the 0–29 M8 task seeds.
GAMMA, LEARNING_RATE = 0.98, 0.01
BOOTSTRAPS, BOOTSTRAP_SEED = 20_000, 20261008
TRACE, REPLAY = "ELIGIBILITY_TRACE", "EXACT_REPLAY"
HORIZON_ARMS = tuple(f"HORIZON_{h}" for h in HORIZONS)
ARMS = HORIZON_ARMS + (TRACE, REPLAY)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def softmax(logits: np.ndarray) -> np.ndarray:
    exp = np.exp(logits - np.max(logits))
    return exp / exp.sum()


def evaluate(weights: np.ndarray, features: np.ndarray, labels: np.ndarray) -> float:
    return float(np.mean(np.argmax(features @ weights, axis=1) == labels))


def train_one(phi, labels, phi_test, labels_test, delay):
    weights = {arm: np.zeros((N_FEATURES, N_OUTPUT), dtype=np.float64) for arm in ARMS}
    predictions = {arm: [] for arm in ARMS}
    horizons = {h: deque(maxlen=h) for h in HORIZONS if h > 1}
    eligibility = np.zeros(N_FEATURES, dtype=np.float64)
    replay = deque()

    for step in range(N_TRAIN + delay):
        has_input = step < N_TRAIN
        feature = phi[step] if has_input else np.zeros(N_FEATURES, dtype=np.float64)
        if has_input:
            for horizon, buffer in horizons.items():
                buffer.append((step, feature.copy()))
            for arm in ARMS:
                predictions[arm].append(softmax(feature @ weights[arm]))

        eligibility = GAMMA * eligibility + feature
        target_index = step - delay
        if 0 <= target_index < N_TRAIN:
            one_hot = np.zeros(N_OUTPUT, dtype=np.float64)
            one_hot[int(labels[target_index])] = 1.0
            exact_feature = None
            if step >= delay:
                if not replay or replay[0][0] != target_index:
                    raise RuntimeError("exact replay buffer does not contain the delayed target")
                exact_feature = replay[0][1]
            for arm in ARMS:
                error = one_hot - predictions[arm][target_index]
                if arm == REPLAY:
                    update_feature = exact_feature
                elif arm == TRACE:
                    update_feature = eligibility / max(np.linalg.norm(eligibility), 1e-12)
                else:
                    horizon = int(arm.split("_")[1])
                    if horizon == 1:
                        update_feature = feature
                    else:
                        buffer = horizons[horizon]
                        update_feature = sum(
                            (GAMMA ** (step - index)) * vector for index, vector in buffer
                        ) if buffer else np.zeros(N_FEATURES)
                        update_feature = update_feature / max(np.linalg.norm(update_feature), 1e-12)
                weights[arm] += LEARNING_RATE * np.outer(update_feature, error)

            if step >= delay:
                replay.popleft()

        # Keep only past features needed by an exact D-step delayed update. The
        # current observation is appended after using the D previous features.
        if has_input:
            replay.append((step, feature.copy()))
            if len(replay) > delay:
                replay.popleft()

    if any(not np.isfinite(weight).all() for weight in weights.values()):
        raise FloatingPointError("non-finite model weights")
    if any(not np.isfinite(weight).all() for weight in weights.values()):
        raise FloatingPointError("non-finite model weights")
    return {arm: evaluate(weights[arm], phi_test, labels_test) for arm in ARMS}


def bootstrap_ci(values: np.ndarray, salt: int = 0) -> list[float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED + salt)
    indices = rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))
    means = values[indices].mean(axis=1)
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def main() -> None:
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    OUT = parser.parse_args().output_dir.expanduser().resolve()
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for rho in RHOS:
        for seed in SEEDS:
            phi, y, phi_test, y_test = make_task(rho, seed)
            for delay in DELAYS:
                scores = train_one(phi, y, phi_test, y_test, delay)
                for arm, accuracy in scores.items():
                    if arm.startswith("HORIZON_"):
                        horizon = int(arm.split("_")[1])
                        memory = 0 if horizon == 1 else horizon * N_FEATURES
                    elif arm == TRACE:
                        horizon, memory = None, N_FEATURES
                    else:
                        horizon, memory = None, delay * N_FEATURES
                    rows.append({
                        "rho": rho, "seed": seed, "delay": delay, "arm": arm,
                        "horizon": horizon, "accuracy": accuracy,
                        "active_history_float_values": memory,
                        "n_train": N_TRAIN, "n_test": N_TEST,
                    })
    task_path = OUT / "task_metrics.csv"
    with task_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    score = {(float(r["rho"]), int(r["seed"]), int(r["delay"]), r["arm"]): float(r["accuracy"]) for r in rows}
    primary_by_seed = np.asarray([
        np.mean([
            score[(rho, seed, delay, TRACE)] - score[(rho, seed, delay, "HORIZON_1")]
            for rho in RHOS for delay in DELAYS
        ]) for seed in SEEDS
    ])
    primary = {
        "estimand": "mean across fresh task seeds of the equal-weighted ELIGIBILITY_TRACE minus HORIZON_1 accuracy over rho × delay cells",
        "mean": float(primary_by_seed.mean()), "task_seed_bootstrap_95ci": bootstrap_ci(primary_by_seed),
        "positive_seed_count": int((primary_by_seed > 0).sum()), "n_task_seeds": len(SEEDS),
        "seeds": [min(SEEDS), max(SEEDS)],
    }
    by_delay, by_rho = [], []
    for delay in DELAYS:
        vals = np.asarray([
            np.mean([score[(rho, seed, delay, TRACE)] - score[(rho, seed, delay, "HORIZON_1")] for rho in RHOS])
            for seed in SEEDS
        ])
        by_delay.append({"delay": delay, "mean_trace_minus_h1": float(vals.mean()), "task_seed_bootstrap_95ci": bootstrap_ci(vals, delay)})
    for rho in RHOS:
        vals = np.asarray([
            np.mean([score[(rho, seed, delay, TRACE)] - score[(rho, seed, delay, "HORIZON_1")] for delay in DELAYS])
            for seed in SEEDS
        ])
        by_rho.append({"rho": rho, "mean_trace_minus_h1": float(vals.mean()), "task_seed_bootstrap_95ci": bootstrap_ci(vals, int(rho * 100) + 100)})

    arm_means = {}
    for arm in ARMS:
        arm_summary = {"mean_accuracy_equal_weighted_over_all_cells": float(np.mean([float(r["accuracy"]) for r in rows if r["arm"] == arm]))}
        if arm == REPLAY:
            arm_summary["active_history_float_values_by_delay"] = {str(d): d * N_FEATURES for d in DELAYS}
            arm_summary["mean_active_history_float_values_over_delays"] = float(np.mean([d * N_FEATURES for d in DELAYS]))
        else:
            arm_summary["active_history_float_values"] = int(next(int(r["active_history_float_values"]) for r in rows if r["arm"] == arm))
        arm_means[arm] = arm_summary
    comparisons = []
    for rho in RHOS:
        for delay in DELAYS:
            cell = {arm: np.asarray([score[(rho, seed, delay, arm)] for seed in SEEDS]) for arm in ARMS}
            comparisons.append({
                "rho": rho, "delay": delay,
                "trace_minus_horizon1": float(np.mean(cell[TRACE] - cell["HORIZON_1"])),
                "trace_minus_horizon2": float(np.mean(cell[TRACE] - cell["HORIZON_2"])),
                "trace_minus_horizon4": float(np.mean(cell[TRACE] - cell["HORIZON_4"])),
                "trace_minus_exact_replay": float(np.mean(cell[TRACE] - cell[REPLAY])),
            })
    summary = {
        "experiment": "M5_ELIGIBILITY_TRACE_MEMORY_FRONTIER_V1",
        "classification": "POST_RESULT_EXPLORATORY_FRESH_TASK_SEEDS",
        "primary": primary, "trace_minus_h1_by_delay": by_delay, "trace_minus_h1_by_rho": by_rho,
        "mean_accuracy_and_active_history_state": arm_means,
        "cellwise_paired_differences_descriptive_only": comparisons,
        "n_rows": len(rows), "rho_values": RHOS, "delays": DELAYS, "horizons": HORIZONS,
        "gamma": GAMMA, "learning_rate": LEARNING_RATE,
        "limitations": [
            "the M8-family task, gamma, and learning rate were selected after earlier outcomes were known; fresh task seeds do not make this confirmatory",
            "task is an artificial random-feature classification family; no biological outcome or mechanism was validated",
            "eligibility memory accounting is 64 active float values; shared prediction histories and model weights are excluded consistently",
            "accuracy and state-size are algorithmic measures; process memory, wall-clock cost, and energy were not measured",
            "task-seed bootstrap intervals describe this task generator only and cellwise contrasts are descriptive",
        ],
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    with (OUT / "primary_seed_contrasts.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["seed", "trace_minus_h1_mean_across_cells"], lineterminator="\n")
        writer.writeheader()
        writer.writerows({"seed": seed, "trace_minus_h1_mean_across_cells": float(value)} for seed, value in zip(SEEDS, primary_by_seed))
    manifest = {
        "experiment": summary["experiment"], "classification": summary["classification"],
        "master_seed": MASTER_SEED, "task_seed_range": [min(SEEDS), max(SEEDS)],
        "rho_values": RHOS, "delays": DELAYS, "horizons": HORIZONS,
        "n_train": N_TRAIN, "n_test": N_TEST, "n_rows": len(rows),
        "gamma": GAMMA, "learning_rate": LEARNING_RATE, "python": platform.python_version(), "numpy": np.__version__,
        "input_sha256": {
            "contract": sha256(CONTRACT),
            "runner": sha256(Path(__file__).resolve()),
            "task_generator": sha256(MODEL_DIR / "task_generator.py"),
        },
        "output_sha256": {p.name: sha256(p) for p in (task_path, summary_path, OUT / "primary_seed_contrasts.csv")},
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(primary, indent=2))


if __name__ == "__main__":
    main()
