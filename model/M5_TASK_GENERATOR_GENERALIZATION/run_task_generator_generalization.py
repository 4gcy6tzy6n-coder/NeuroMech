#!/usr/bin/env python3
"""Test the fixed M5 delayed-teaching update on three input generators."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "results" / "M5_TASK_GENERATOR_GENERALIZATION" / f"rerun_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
MASTER_SEED = 20260930
N_INPUT = 32
N_FEATURES = 64
N_CLASSES = 4
N_TRAIN = 3000
N_TEST = 1000
DELAYS = (1, 4, 16, 64)
N_SEEDS = 30
LEARNING_RATE = 0.01
GAMMA = 0.98
N_BOOTSTRAPS = 20_000
GENERATORS = ("IID_GAUSSIAN", "AR1_GAUSSIAN", "SPARSE_SIGN")
ARMS = ("EXACT_REPLAY", "ELIGIBILITY_TRACE_NORM_MATCHED", "NO_TRACE")


def make_stream(rng: np.random.Generator, generator: str, n: int) -> np.ndarray:
    if generator == "IID_GAUSSIAN":
        return rng.normal(size=(n, N_INPUT))
    if generator == "AR1_GAUSSIAN":
        values = np.empty((n, N_INPUT), dtype=np.float64)
        values[0] = rng.normal(size=N_INPUT)
        innovation_scale = np.sqrt(1.0 - 0.8**2)
        for t in range(1, n):
            values[t] = 0.8 * values[t - 1] + innovation_scale * rng.normal(size=N_INPUT)
        return values
    if generator == "SPARSE_SIGN":
        keep = rng.random((n, N_INPUT)) < 0.2
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=(n, N_INPUT))
        return keep * signs / np.sqrt(0.2)
    raise ValueError(f"unknown generator: {generator}")


def make_task(generator: str, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    family_index = GENERATORS.index(generator)
    rng = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, family_index, seed, 781]))
    projection = rng.normal(size=(N_INPUT, N_FEATURES)) / np.sqrt(N_INPUT)
    teacher = rng.normal(size=(N_FEATURES, N_CLASSES)) / np.sqrt(N_FEATURES)
    raw_train = make_stream(rng, generator, N_TRAIN)
    raw_test = make_stream(rng, generator, N_TEST)
    phi_train = np.tanh(raw_train @ projection)
    phi_test = np.tanh(raw_test @ projection)
    phi_train /= np.maximum(np.linalg.norm(phi_train, axis=1, keepdims=True), 1e-12)
    phi_test /= np.maximum(np.linalg.norm(phi_test, axis=1, keepdims=True), 1e-12)
    y_train = np.argmax(phi_train @ teacher, axis=1)
    y_test = np.argmax(phi_test @ teacher, axis=1)
    return phi_train, y_train, phi_test, y_test


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    return exp / exp.sum()


def evaluate(weights: np.ndarray, features: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    logits = features @ weights
    logits -= logits.max(axis=1, keepdims=True)
    exp = np.exp(logits)
    probs = exp / exp.sum(axis=1, keepdims=True)
    accuracy = float(np.mean(np.argmax(probs, axis=1) == labels))
    loss = float(-np.mean(np.log(np.maximum(probs[np.arange(len(labels)), labels], 1e-12))))
    return accuracy, loss


def train_one(phi_train: np.ndarray, y_train: np.ndarray, phi_test: np.ndarray,
              y_test: np.ndarray, delay: int, seed: int, generator: str) -> list[dict[str, object]]:
    weights = {arm: np.zeros((N_FEATURES, N_CLASSES), dtype=np.float64) for arm in ARMS}
    predictions: dict[str, list[np.ndarray]] = {arm: [] for arm in ARMS}
    eligibility = np.zeros(N_FEATURES, dtype=np.float64)
    for step in range(N_TRAIN + delay):
        has_input = step < N_TRAIN
        feature = phi_train[step] if has_input else np.zeros(N_FEATURES, dtype=np.float64)
        if has_input:
            for arm in ARMS:
                predictions[arm].append(softmax(feature @ weights[arm]))
        eligibility = GAMMA * eligibility + feature
        target_index = step - delay
        if not (0 <= target_index < N_TRAIN):
            continue
        one_hot = np.zeros(N_CLASSES, dtype=np.float64)
        one_hot[int(y_train[target_index])] = 1.0
        for arm in ARMS:
            error = one_hot - predictions[arm][target_index]
            if arm == "EXACT_REPLAY":
                update_feature = phi_train[target_index]
            elif arm == "ELIGIBILITY_TRACE_NORM_MATCHED":
                update_feature = eligibility / max(float(np.linalg.norm(eligibility)), 1e-12)
            else:
                update_feature = feature
            weights[arm] += LEARNING_RATE * np.outer(update_feature, error)

    rows = []
    for arm in ARMS:
        accuracy, loss = evaluate(weights[arm], phi_test, y_test)
        rows.append({
            "generator": generator,
            "seed": seed,
            "delay": delay,
            "arm": arm,
            "test_accuracy": accuracy,
            "test_cross_entropy": loss,
            "n_train": N_TRAIN,
            "n_test": N_TEST,
        })
    return rows


def hierarchical_bootstrap(seed_differences: np.ndarray) -> list[float]:
    """Input axes are generator × task seed; generators are fixed strata."""
    rng = np.random.default_rng(MASTER_SEED + 909)
    n_generators, n_seeds = seed_differences.shape
    draws = np.empty(N_BOOTSTRAPS, dtype=np.float64)
    for start in range(0, N_BOOTSTRAPS, 100):
        count = min(100, N_BOOTSTRAPS - start)
        sampled = np.empty((count, n_generators), dtype=np.float64)
        for gen_i in range(n_generators):
            indices = rng.integers(0, n_seeds, size=(count, n_seeds))
            sampled[:, gen_i] = seed_differences[gen_i, indices].mean(axis=1)
        draws[start:start + count] = sampled.mean(axis=1)
    return [float(x) for x in np.quantile(draws, [0.025, 0.975])]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, object]] = []
    for generator in GENERATORS:
        for seed in range(N_SEEDS):
            phi_train, y_train, phi_test, y_test = make_task(generator, seed)
            for delay in DELAYS:
                rows.extend(train_one(phi_train, y_train, phi_test, y_test, delay, seed, generator))

    metrics_path = OUT / "task_metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    indexed = {(r["generator"], int(r["seed"]), int(r["delay"]), r["arm"]): r for r in rows}
    seed_differences = np.empty((len(GENERATORS), N_SEEDS), dtype=np.float64)
    generator_summaries = []
    delay_summaries = []
    for gen_i, generator in enumerate(GENERATORS):
        per_seed_effect = np.empty(N_SEEDS, dtype=np.float64)
        for seed in range(N_SEEDS):
            effects = []
            for delay in DELAYS:
                trace = float(indexed[(generator, seed, delay, "ELIGIBILITY_TRACE_NORM_MATCHED")]["test_accuracy"])
                no_trace = float(indexed[(generator, seed, delay, "NO_TRACE")]["test_accuracy"])
                replay = float(indexed[(generator, seed, delay, "EXACT_REPLAY")]["test_accuracy"])
                effects.append(trace - no_trace)
                delay_summaries.append({
                    "generator": generator,
                    "seed": seed,
                    "delay": delay,
                    "trace_minus_no_trace": trace - no_trace,
                    "trace_minus_exact_replay": trace - replay,
                })
            per_seed_effect[seed] = float(np.mean(effects))
        seed_differences[gen_i] = per_seed_effect
        generator_summaries.append({
            "generator": generator,
            "mean_trace_minus_no_trace_accuracy": float(per_seed_effect.mean()),
            "task_seed_bootstrap_95ci": [
                float(x) for x in np.quantile(
                    np.random.default_rng(MASTER_SEED + 3000 + gen_i).choice(per_seed_effect, size=(N_BOOTSTRAPS, N_SEEDS), replace=True).mean(axis=1),
                    [0.025, 0.975],
                )
            ],
            "positive_seed_count": int(np.sum(per_seed_effect > 0)),
            "task_seeds": N_SEEDS,
        })

    primary_effect = float(seed_differences.mean())
    primary_ci = hierarchical_bootstrap(seed_differences)
    all_generator_positive = all(item["mean_trace_minus_no_trace_accuracy"] > 0 for item in generator_summaries)
    if primary_ci[0] > 0 and all_generator_positive:
        decision = "ADVANTAGE_RETAINED_ACROSS_THE_THREE_TESTED_GENERATORS"
    elif primary_ci[0] > 0:
        decision = "OVERALL_POSITIVE_WITH_GENERATOR_HETEROGENEITY"
    elif primary_ci[1] < 0:
        decision = "ADVANTAGE_NOT_RETAINED_ON_THE_FROZEN_GENERATOR_SET"
    else:
        decision = "INCONCLUSIVE_ACROSS_THE_THREE_TESTED_GENERATORS"

    delay_effects = []
    for generator in GENERATORS:
        for delay in DELAYS:
            differences = [
                float(indexed[(generator, seed, delay, "ELIGIBILITY_TRACE_NORM_MATCHED")]["test_accuracy"])
                - float(indexed[(generator, seed, delay, "NO_TRACE")]["test_accuracy"])
                for seed in range(N_SEEDS)
            ]
            delay_effects.append({"generator": generator, "delay": delay, "mean_trace_minus_no_trace": float(np.mean(differences))})

    result = {
        "status": "POST_RESULT_CROSS_GENERATOR_VALIDATION_COMPLETE",
        "primary_estimand": "equal-generator mean of per-task-seed four-delay mean test-accuracy difference (norm-matched eligibility trace minus no-trace)",
        "primary_mean_difference": primary_effect,
        "hierarchical_seed_bootstrap_95ci": primary_ci,
        "decision": decision,
        "generator_summaries": generator_summaries,
        "per_generator_per_delay_effects": delay_effects,
        "secondary": "task_metrics.csv contains paired accuracy and cross-entropy for exact replay, eligibility trace, and no-trace arms",
        "scope": "conditional on these three prespecified input generators; not arbitrary task-family generalization or biological validation",
    }
    (OUT / "primary_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "M5_TASK_GENERATOR_GENERALIZATION",
        "contract": "M5_TASK_GENERATOR_GENERALIZATION_CONTRACT.md",
        "seed": MASTER_SEED,
        "generators": list(GENERATORS),
        "task_seeds_per_generator": N_SEEDS,
        "delays": list(DELAYS),
        "arms": list(ARMS),
        "fixed_hyperparameters": {"learning_rate": LEARNING_RATE, "eligibility_decay": GAMMA},
        "task_shape": {"n_input": N_INPUT, "n_features": N_FEATURES, "n_classes": N_CLASSES, "n_train": N_TRAIN, "n_test": N_TEST},
        "outputs": ["task_metrics.csv", "primary_result.json"],
        "post_result_status": "Outcome-informed follow-up to the previously observed M5-v3 result; no hyperparameter tuning.",
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with (OUT / "per_seed_task_contrasts.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(delay_summaries[0]))
        writer.writeheader()
        writer.writerows(delay_summaries)
    print(json.dumps({"decision": decision, "primary_mean_difference": primary_effect, "ci95": primary_ci, "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
