#!/usr/bin/env python3
"""Run a post-result memory-frontier transfer on the delayed-reward bandit."""
from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "results" / "M5_DELAYED_REWARD_MEMORY_FRONTIER_V1" / "canonical"
MASTER_SEED = 20260930
N_CONTEXT, N_ACTIONS, N_TRAIN, N_TEST = 16, 2, 6000, 2000
DELAYS = (1, 4, 16, 64)
TASK_SEEDS = tuple(range(30, 60))
LEARNING_RATE, GAMMA, BASELINE = 0.01, 0.98, 0.5
N_BOOTSTRAPS = 20_000
FIFO_CAPACITY = {
    "EXACT_FIFO_32": 1,
    "EXACT_FIFO_128": 4,
    "EXACT_FIFO_512": 16,
    "EXACT_FIFO_2048": 64,
}
ARMS = ("ELIGIBILITY_TRACE_32", *FIFO_CAPACITY, "NO_TRACE_CURRENT_32", "EXACT_REPLAY")


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def softmax(logits: np.ndarray) -> np.ndarray:
    z = logits - np.max(logits)
    p = np.exp(z)
    return p / p.sum()


def make_task(seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, seed, 811]))
    theta = rng.normal(size=(N_CONTEXT, N_ACTIONS))
    train_contexts = rng.normal(size=(N_TRAIN, N_CONTEXT))
    train_contexts /= np.maximum(np.linalg.norm(train_contexts, axis=1, keepdims=True), 1e-12)
    test_contexts = rng.normal(size=(N_TEST, N_CONTEXT))
    test_contexts /= np.maximum(np.linalg.norm(test_contexts, axis=1, keepdims=True), 1e-12)
    return {
        "train_contexts": train_contexts,
        "test_contexts": test_contexts,
        "train_reward_probabilities": sigmoid(train_contexts @ theta),
        "test_reward_probabilities": sigmoid(test_contexts @ theta),
        "choice_uniforms": rng.random(N_TRAIN),
        "reward_uniforms": rng.random((N_TRAIN, N_ACTIONS)),
    }


def unit_score(context: np.ndarray, action: int, policy: np.ndarray) -> np.ndarray:
    one_hot = np.zeros(N_ACTIONS, dtype=np.float64)
    one_hot[action] = 1.0
    score = np.outer(context, one_hot - policy)
    return score / max(float(np.linalg.norm(score)), 1e-12)


def expected_reward(weights: np.ndarray, contexts: np.ndarray, reward_probs: np.ndarray) -> float:
    logits = contexts @ weights
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    probs /= probs.sum(axis=1, keepdims=True)
    return float(np.mean(np.sum(probs * reward_probs, axis=1)))


def train_task(task: dict[str, np.ndarray], seed: int, delay: int):
    weights = {a: np.zeros((N_CONTEXT, N_ACTIONS), dtype=np.float64) for a in ARMS}
    traces = {a: np.zeros((N_CONTEXT, N_ACTIONS), dtype=np.float64) for a in ARMS}
    reward_history = {a: np.zeros(N_TRAIN, dtype=np.float64) for a in ARMS}
    # Exact replay retains only scores whose delayed reward is still pending.
    exact_replay = {}
    fifo = {a: {} for a in FIFO_CAPACITY}
    applied = {a: 0 for a in ARMS}
    trajectory_rows = []

    for step in range(N_TRAIN + delay):
        has_context = step < N_TRAIN
        current_scores: dict[str, np.ndarray] = {}

        if has_context:
            x = task["train_contexts"][step]
            for arm in ARMS:
                policy = softmax(x @ weights[arm])
                action = int(task["choice_uniforms"][step] >= policy[0])
                score = unit_score(x, action, policy)
                reward = float(task["reward_uniforms"][step, action]
                               < task["train_reward_probabilities"][step, action])
                current_scores[arm] = score
                reward_history[arm][step] = reward
            for arm in ARMS:
                traces[arm] = GAMMA * traces[arm] + current_scores[arm]
        else:
            current_scores = {arm: np.zeros((N_CONTEXT, N_ACTIONS), dtype=np.float64) for arm in ARMS}
            for arm in ARMS:
                traces[arm] *= GAMMA

        labeled_index = step - delay
        if 0 <= labeled_index < N_TRAIN:
            for arm in ARMS:
                advantage = reward_history[arm][labeled_index] - BASELINE
                if arm == "ELIGIBILITY_TRACE_32":
                    state = traces[arm]
                    update_score = state / max(float(np.linalg.norm(state)), 1e-12)
                    available = True
                elif arm in FIFO_CAPACITY:
                    update_score = fifo[arm].get(labeled_index)
                    available = update_score is not None
                elif arm == "NO_TRACE_CURRENT_32":
                    update_score = current_scores[arm]
                    available = bool(has_context)
                else:
                    update_score = exact_replay.get(labeled_index)
                    available = True
                    if update_score is None:
                        raise RuntimeError(f"exact replay score missing for decision {labeled_index}")
                if available:
                    weights[arm] += LEARNING_RATE * advantage * update_score
                    applied[arm] += 1

            exact_replay.pop(labeled_index, None)

        # Insert after delivering the due reward, so a capacity-1 FIFO can use
        # the immediately preceding score at delay 1 before it is replaced.
        if has_context:
            exact_replay[step] = current_scores["EXACT_REPLAY"].copy()
            for arm, capacity in FIFO_CAPACITY.items():
                effective_capacity = min(capacity, delay)
                fifo[arm][step] = current_scores[arm].copy()
                while len(fifo[arm]) > effective_capacity:
                    del fifo[arm][min(fifo[arm])]

        if has_context and (step + 1) % 500 == 0:
            lo = step + 1 - 500
            for arm in ARMS:
                trajectory_rows.append({
                    "seed": seed, "delay": delay, "arm": arm,
                    "block_start_step": lo, "block_end_step": step + 1,
                    "mean_realized_reward": float(reward_history[arm][lo:step + 1].mean()),
                })

    metrics = []
    coverage = []
    for arm in ARMS:
        extra_state = (32 if arm in {"ELIGIBILITY_TRACE_32", "EXACT_FIFO_32", "NO_TRACE_CURRENT_32"}
                       else min(FIFO_CAPACITY[arm], delay) * 32 if arm in FIFO_CAPACITY
                       else delay * 32 if arm == "EXACT_REPLAY" else 0)
        metrics.append({
            "seed": seed, "delay": delay, "arm": arm,
            "heldout_expected_reward": expected_reward(weights[arm], task["test_contexts"], task["test_reward_probabilities"]),
            "mean_train_realized_reward": float(reward_history[arm].mean()),
            "active_credit_state_values": extra_state,
            "n_train": N_TRAIN, "n_test": N_TEST,
        })
        coverage.append({
            "seed": seed, "delay": delay, "arm": arm,
            "updates_applied": applied[arm], "updates_possible": N_TRAIN,
            "update_coverage": applied[arm] / N_TRAIN,
        })
    return metrics, coverage, trajectory_rows


def bootstrap_ci(seed_effects: np.ndarray) -> list[float]:
    rng = np.random.default_rng(MASTER_SEED + 992)
    indices = rng.integers(0, len(seed_effects), size=(N_BOOTSTRAPS, len(seed_effects)))
    return [float(v) for v in np.quantile(seed_effects[indices].mean(axis=1), [0.025, 0.975])]


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    t0 = time.perf_counter()
    metric_rows, coverage_rows, trajectory_rows = [], [], []
    for seed in TASK_SEEDS:
        task = make_task(seed)
        for delay in DELAYS:
            metrics, coverage, trajectory = train_task(task, seed, delay)
            metric_rows.extend(metrics)
            coverage_rows.extend(coverage)
            trajectory_rows.extend(trajectory)

    write_csv(OUT / "task_metrics.csv", metric_rows)
    write_csv(OUT / "update_coverage.csv", coverage_rows)
    write_csv(OUT / "training_reward_trajectory.csv", trajectory_rows)

    lookup = {(int(r["seed"]), int(r["delay"]), r["arm"]): r for r in metric_rows}
    seed_effects = []
    for seed in TASK_SEEDS:
        seed_effects.append(float(np.mean([
            float(lookup[(seed, d, "ELIGIBILITY_TRACE_32")]["heldout_expected_reward"])
            - float(lookup[(seed, d, "EXACT_FIFO_32")]["heldout_expected_reward"])
            for d in DELAYS
        ])))
    seed_effects_arr = np.asarray(seed_effects)
    primary_mean = float(seed_effects_arr.mean())
    primary_ci = bootstrap_ci(seed_effects_arr)

    delay_summary = []
    for delay in DELAYS:
        means = {
            arm: float(np.mean([float(lookup[(seed, delay, arm)]["heldout_expected_reward"]) for seed in TASK_SEEDS]))
            for arm in ARMS
        }
        coverage_mean = {
            arm: float(np.mean([float(next(r["update_coverage"] for r in coverage_rows
                                           if int(r["seed"]) == seed and int(r["delay"]) == delay and r["arm"] == arm))
                                for seed in TASK_SEEDS]))
            for arm in ARMS
        }
        delay_summary.append({"delay": delay, "mean_expected_reward": means, "mean_update_coverage": coverage_mean})

    contrast_rows = []
    for arm in ARMS:
        if arm == "ELIGIBILITY_TRACE_32":
            continue
        differences = np.asarray([
            np.mean([float(lookup[(seed, d, "ELIGIBILITY_TRACE_32")]["heldout_expected_reward"])
                     - float(lookup[(seed, d, arm)]["heldout_expected_reward"]) for d in DELAYS])
            for seed in TASK_SEEDS
        ])
        contrast_rows.append({
            "contrast": f"ELIGIBILITY_TRACE_32_MINUS_{arm}",
            "mean_task_seed_delay_average": float(differences.mean()),
            "paired_seed_bootstrap_95ci_low": bootstrap_ci(differences)[0],
            "paired_seed_bootstrap_95ci_high": bootstrap_ci(differences)[1],
            "positive_task_seeds": int(np.sum(differences > 0)),
            "task_seeds": len(TASK_SEEDS),
        })
    write_csv(OUT / "primary_contrasts.csv", contrast_rows)
    write_csv(OUT / "per_seed_primary.csv", [
        {"seed": seed, "trace_minus_fifo32_mean_over_delays": effect}
        for seed, effect in zip(TASK_SEEDS, seed_effects)
    ])

    summary = {
        "experiment_id": "M5_DELAYED_REWARD_MEMORY_FRONTIER_V1",
        "classification": "post-result exploratory, distinct-objective memory-frontier transfer",
        "primary_estimand": "task-seed mean of four-delay held-out expected reward: eligibility trace minus one-vector exact FIFO",
        "primary_mean_difference": primary_mean,
        "primary_paired_seed_bootstrap_95ci": primary_ci,
        "positive_task_seeds": int(np.sum(seed_effects_arr > 0)),
        "task_seeds": len(TASK_SEEDS),
        "delay_frontier": delay_summary,
        "contrasts": contrast_rows,
        "rows": {"task_metrics": len(metric_rows), "update_coverage": len(coverage_rows),
                 "training_reward_trajectory": len(trajectory_rows)},
        "elapsed_seconds": time.perf_counter() - t0,
        "scope": "one synthetic delayed-reward contextual-bandit family; active-state counts are algorithmic values, not RAM or energy measurements; no biological validation or arbitrary-task generalization",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    files = ["task_metrics.csv", "update_coverage.csv", "training_reward_trajectory.csv",
             "primary_contrasts.csv", "per_seed_primary.csv", "summary.json"]
    manifest = {
        "experiment_id": "M5_DELAYED_REWARD_MEMORY_FRONTIER_V1",
        "contract": "summery/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/CONTRACT.md",
        "runner": "model/M5_DELAYED_REWARD_MEMORY_FRONTIER_V1/run_experiment.py",
        "master_seed": MASTER_SEED,
        "task_seeds": list(TASK_SEEDS),
        "delays": list(DELAYS),
        "arms": list(ARMS),
        "fixed_parameters": {"learning_rate": LEARNING_RATE, "eligibility_decay": GAMMA,
                              "reward_baseline": BASELINE, "training_decisions": N_TRAIN,
                              "heldout_contexts": N_TEST, "bootstrap_replicates": N_BOOTSTRAPS},
        "task_seed_independent_unit": True,
        "row_counts": summary["rows"],
        "outputs_sha256": {f: sha256(OUT / f) for f in files},
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "primary_mean": primary_mean,
                      "ci95": primary_ci, "positive_seeds": summary["positive_task_seeds"],
                      "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
