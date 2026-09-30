#!/usr/bin/env python3
"""Run the frozen synthetic delayed-teaching benchmark."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_v3_local_norm_correction"
N_INPUT = 32
N_FEATURES = 64
N_CLASSES = 4
N_TRAIN = 3000
N_TEST = 1000
DELAYS = (1, 4, 16, 64)
N_SEEDS = 30
LEARNING_RATE = 0.01
GAMMA = 0.98
BOOTSTRAPS = 20000
ARMS = ("exact_replay", "eligibility_trace_raw", "eligibility_trace_norm_matched", "no_trace")


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    return exp / exp.sum()


def make_task(seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(8813000 + seed)
    projection = rng.normal(size=(N_INPUT, N_FEATURES)) / np.sqrt(N_INPUT)
    teacher = rng.normal(size=(N_FEATURES, N_CLASSES)) / np.sqrt(N_FEATURES)
    x_train = rng.normal(size=(N_TRAIN, N_INPUT))
    x_test = rng.normal(size=(N_TEST, N_INPUT))
    phi_train = np.tanh(x_train @ projection)
    phi_test = np.tanh(x_test @ projection)
    phi_train /= np.maximum(np.linalg.norm(phi_train, axis=1, keepdims=True), 1e-12)
    phi_test /= np.maximum(np.linalg.norm(phi_test, axis=1, keepdims=True), 1e-12)
    y_train = np.argmax(phi_train @ teacher, axis=1)
    y_test = np.argmax(phi_test @ teacher, axis=1)
    return phi_train, y_train, phi_test, y_test


def evaluate(weights: np.ndarray, phi: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    logits = phi @ weights
    logits -= logits.max(axis=1, keepdims=True)
    exp = np.exp(logits)
    probs = exp / exp.sum(axis=1, keepdims=True)
    accuracy = float(np.mean(np.argmax(probs, axis=1) == labels))
    loss = float(-np.mean(np.log(np.maximum(probs[np.arange(len(labels)), labels], 1e-12))))
    return accuracy, loss


def fit_batch_logistic(phi: np.ndarray, labels: np.ndarray) -> np.ndarray:
    reg = 1e-4
    n, features = phi.shape
    classes = int(labels.max()) + 1

    def objective(flat: np.ndarray) -> tuple[float, np.ndarray]:
        weights = flat.reshape(features, classes)
        logits = phi @ weights
        loss = float(np.mean(logsumexp(logits, axis=1) - logits[np.arange(n), labels])
                     + 0.5 * reg * np.sum(weights * weights))
        probs = np.exp(logits - logsumexp(logits, axis=1, keepdims=True))
        probs[np.arange(n), labels] -= 1.0
        grad = phi.T @ probs / n + reg * weights
        return loss, grad.ravel()

    result = minimize(objective, np.zeros(features * classes), jac=True, method="L-BFGS-B",
                      options={"maxiter": 500, "ftol": 1e-10})
    return result.x.reshape(features, classes)


def train_delay(phi_train: np.ndarray, y_train: np.ndarray, phi_test: np.ndarray,
                y_test: np.ndarray, batch_weights: np.ndarray, delay: int,
                seed: int) -> list[dict[str, object]]:
    weights = {arm: np.zeros((N_FEATURES, N_CLASSES), dtype=np.float64) for arm in ARMS}
    prediction_history: dict[str, list[np.ndarray]] = {arm: [] for arm in ARMS}
    eligibility = np.zeros(N_FEATURES, dtype=np.float64)
    records: list[dict[str, object]] = []
    total_steps = N_TRAIN + delay

    for step in range(total_steps):
        has_input = step < N_TRAIN
        phi_t = phi_train[step] if has_input else np.zeros(N_FEATURES, dtype=np.float64)
        if has_input:
            label = int(y_train[step])
            target = np.zeros(N_CLASSES, dtype=np.float64)
            target[label] = 1.0
            for arm in ARMS:
                prediction_history[arm].append(softmax(phi_t @ weights[arm]))

        eligibility = GAMMA * eligibility + phi_t
        target_index = step - delay
        if 0 <= target_index < N_TRAIN:
            target_label = int(y_train[target_index])
            target_one_hot = np.zeros(N_CLASSES, dtype=np.float64)
            target_one_hot[target_label] = 1.0
            for arm in ARMS:
                prediction = prediction_history[arm][target_index]
                error = target_one_hot - prediction
                if arm == "exact_replay":
                    update_features = phi_train[target_index]
                elif arm == "eligibility_trace_raw":
                    update_features = eligibility
                elif arm == "eligibility_trace_norm_matched":
                    trace_norm = np.linalg.norm(eligibility)
                    update_features = eligibility / max(trace_norm, 1e-12)
                else:
                    update_features = phi_t
                weights[arm] += LEARNING_RATE * np.outer(update_features, error)

            if (target_index + 1) % 500 == 0 or target_index + 1 == N_TRAIN:
                n_seen = target_index + 1
                for arm in ARMS:
                    acc, loss = evaluate(weights[arm], phi_test, y_test)
                    records.append({
                        "seed": seed,
                        "delay": delay,
                        "arm": arm,
                        "training_labels_delivered": n_seen,
                        "test_accuracy": acc,
                        "test_cross_entropy": loss,
                    })

    batch_acc, batch_loss = evaluate(batch_weights, phi_test, y_test)
    records.append({
        "seed": seed,
        "delay": delay,
        "arm": "batch_logistic",
        "training_labels_delivered": N_TRAIN,
        "test_accuracy": batch_acc,
        "test_cross_entropy": batch_loss,
    })

    return records


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    draws = rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))
    means = values[draws].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    learning_rows: list[dict[str, object]] = []
    final_by_seed: dict[int, dict[int, dict[str, float]]] = {}
    for seed in range(N_SEEDS):
        phi_train, y_train, phi_test, y_test = make_task(seed)
        batch_weights = fit_batch_logistic(phi_train, y_train)
        for delay in DELAYS:
            rows = train_delay(phi_train, y_train, phi_test, y_test, batch_weights, delay, seed)
            learning_rows.extend(rows)
            final_by_seed.setdefault(delay, {})[seed] = {
                row["arm"]: float(row["test_accuracy"])
                for row in rows if row["training_labels_delivered"] == N_TRAIN
            }

    with (OUT / "learning_curves.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(learning_rows[0]))
        writer.writeheader()
        writer.writerows(learning_rows)

    summary_rows = []
    rng = np.random.default_rng(710230)
    per_seed_primary = []
    for delay in DELAYS:
        values = final_by_seed[delay]
        trace = np.array([values[s]["eligibility_trace_norm_matched"] for s in range(N_SEEDS)])
        raw_trace = np.array([values[s]["eligibility_trace_raw"] for s in range(N_SEEDS)])
        no_trace = np.array([values[s]["no_trace"] for s in range(N_SEEDS)])
        replay = np.array([values[s]["exact_replay"] for s in range(N_SEEDS)])
        batch = np.array([values[s]["batch_logistic"] for s in range(N_SEEDS)])
        d_trace_no = trace - no_trace
        d_trace_replay = trace - replay
        d_trace_batch = trace - batch
        ci_no = bootstrap_ci(d_trace_no, rng)
        ci_replay = bootstrap_ci(d_trace_replay, rng)
        per_seed_primary.extend(d_trace_no.tolist())
        summary_rows.append({
            "delay": delay,
            "eligibility_trace_accuracy": float(trace.mean()),
            "eligibility_trace_raw_accuracy": float(raw_trace.mean()),
            "no_trace_accuracy": float(no_trace.mean()),
            "exact_replay_accuracy": float(replay.mean()),
            "batch_logistic_accuracy": float(batch.mean()),
            "trace_minus_no_trace": float(d_trace_no.mean()),
            "trace_minus_no_trace_seed_bootstrap_95ci": list(ci_no),
            "trace_minus_replay": float(d_trace_replay.mean()),
            "trace_minus_replay_seed_bootstrap_95ci": list(ci_replay),
            "trace_minus_batch": float(d_trace_batch.mean()),
            "trace_minus_batch_seed_bootstrap_95ci": list(bootstrap_ci(d_trace_batch, rng)),
            "seeds": N_SEEDS,
        })
    per_seed_primary = np.array(per_seed_primary).reshape(len(DELAYS), N_SEEDS).mean(axis=0)
    overall_ci = bootstrap_ci(per_seed_primary, rng)
    with (OUT / "summary.json").open("w") as f:
        json.dump({
            "contract": "DELAYED_TEACHING_SIGNAL_CONTRACT.md",
            "n_input": N_INPUT,
            "n_features": N_FEATURES,
            "n_classes": N_CLASSES,
            "n_train": N_TRAIN,
            "n_test": N_TEST,
            "delays": DELAYS,
            "seeds": N_SEEDS,
            "learning_rate": LEARNING_RATE,
            "eligibility_decay": GAMMA,
            "primary_mean_trace_minus_no_trace": float(per_seed_primary.mean()),
            "primary_seed_bootstrap_95ci": list(overall_ci),
            "conditions": summary_rows,
        }, f, indent=2)
    print(f"wrote {len(learning_rows)} learning-curve rows and {len(summary_rows)} delay summaries to {OUT}")


if __name__ == "__main__":
    main()
