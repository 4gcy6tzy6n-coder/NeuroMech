#!/usr/bin/env python3
"""Run an outcome-informed delayed-reward contextual-bandit transfer test."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "results" / "M5_DELAYED_REWARD_BANDIT" / f"rerun_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
MASTER_SEED = 20260930
N_CONTEXT = 16
N_ACTIONS = 2
N_TRAIN = 6000
N_TEST = 2000
DELAYS = (1, 4, 16, 64)
N_SEEDS = 30
LEARNING_RATE = 0.01
GAMMA = 0.98
BASELINE = 0.5
N_BOOTSTRAPS = 20_000
ARMS = ("EXACT_REPLAY", "ELIGIBILITY_TRACE_NORM_MATCHED", "NO_TRACE")


def sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    return exp / exp.sum()


def unit_score(context: np.ndarray, action: int, policy: np.ndarray) -> np.ndarray:
    one_hot = np.zeros(N_ACTIONS, dtype=np.float64)
    one_hot[action] = 1.0
    score = np.outer(context, one_hot - policy)
    norm = float(np.linalg.norm(score))
    return score / max(norm, 1e-12)


def make_task(seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, seed, 811]))
    theta = rng.normal(size=(N_CONTEXT, N_ACTIONS))
    train_contexts = rng.normal(size=(N_TRAIN, N_CONTEXT))
    train_contexts /= np.maximum(np.linalg.norm(train_contexts, axis=1, keepdims=True), 1e-12)
    test_contexts = rng.normal(size=(N_TEST, N_CONTEXT))
    test_contexts /= np.maximum(np.linalg.norm(test_contexts, axis=1, keepdims=True), 1e-12)
    return {
        "theta": theta,
        "train_contexts": train_contexts,
        "test_contexts": test_contexts,
        "train_reward_probabilities": sigmoid(train_contexts @ theta),
        "test_reward_probabilities": sigmoid(test_contexts @ theta),
        "choice_uniforms": rng.random(N_TRAIN),
        "reward_uniforms": rng.random((N_TRAIN, N_ACTIONS)),
    }


def evaluate_policy(weights: np.ndarray, contexts: np.ndarray,
                    reward_probabilities: np.ndarray) -> float:
    logits = contexts @ weights
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    probs /= probs.sum(axis=1, keepdims=True)
    return float(np.mean(np.sum(probs * reward_probabilities, axis=1)))


def train_one(task: dict[str, np.ndarray], delay: int, seed: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    weights = {arm: np.zeros((N_CONTEXT, N_ACTIONS), dtype=np.float64) for arm in ARMS}
    eligibility = {arm: np.zeros((N_CONTEXT, N_ACTIONS), dtype=np.float64) for arm in ARMS}
    score_buffers = {
        arm: [np.zeros((N_CONTEXT, N_ACTIONS), dtype=np.float64) for _ in range(delay + 1)]
        for arm in ARMS
    }
    delayed_rewards = {arm: np.zeros(N_TRAIN, dtype=np.float64) for arm in ARMS}
    train_reward_rows: list[dict[str, object]] = []
    reward_history = {arm: np.zeros(N_TRAIN, dtype=np.float64) for arm in ARMS}

    for step in range(N_TRAIN + delay):
        has_context = step < N_TRAIN
        if has_context:
            context = task["train_contexts"][step]
            current_scores = {}
            current_actions = {}
            for arm in ARMS:
                policy = softmax(context @ weights[arm])
                action = int(task["choice_uniforms"][step] >= policy[0])
                score = unit_score(context, action, policy)
                reward = float(task["reward_uniforms"][step, action] < task["train_reward_probabilities"][step, action])
                current_scores[arm] = score
                current_actions[arm] = action
                delayed_rewards[arm][step] = reward
                reward_history[arm][step] = reward
                score_buffers[arm][step % (delay + 1)] = score
        else:
            current_scores = {arm: np.zeros((N_CONTEXT, N_ACTIONS), dtype=np.float64) for arm in ARMS}

        for arm in ARMS:
            eligibility[arm] = GAMMA * eligibility[arm] + current_scores[arm]

        labeled_index = step - delay
        if 0 <= labeled_index < N_TRAIN:
            for arm in ARMS:
                advantage = delayed_rewards[arm][labeled_index] - BASELINE
                if arm == "EXACT_REPLAY":
                    update_score = score_buffers[arm][labeled_index % (delay + 1)]
                elif arm == "ELIGIBILITY_TRACE_NORM_MATCHED":
                    trace = eligibility[arm]
                    update_score = trace / max(float(np.linalg.norm(trace)), 1e-12)
                else:
                    update_score = current_scores[arm]
                weights[arm] += LEARNING_RATE * advantage * update_score

        if has_context and (step + 1) % 500 == 0:
            start = step + 1 - 500
            for arm in ARMS:
                train_reward_rows.append({
                    "seed": seed,
                    "delay": delay,
                    "arm": arm,
                    "block_start_step": start,
                    "block_end_step": step + 1,
                    "mean_realized_reward": float(reward_history[arm][start:step + 1].mean()),
                })

    metric_rows = []
    for arm in ARMS:
        expected_reward = evaluate_policy(weights[arm], task["test_contexts"], task["test_reward_probabilities"])
        metric_rows.append({
            "seed": seed,
            "delay": delay,
            "arm": arm,
            "heldout_expected_reward": expected_reward,
            "mean_train_realized_reward": float(reward_history[arm].mean()),
            "n_train": N_TRAIN,
            "n_test": N_TEST,
        })
    return metric_rows, train_reward_rows


def paired_bootstrap(seed_effects: np.ndarray) -> list[float]:
    rng = np.random.default_rng(MASTER_SEED + 991)
    indices = rng.integers(0, len(seed_effects), size=(N_BOOTSTRAPS, len(seed_effects)))
    means = seed_effects[indices].mean(axis=1)
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    metric_rows: list[dict[str, object]] = []
    train_rows: list[dict[str, object]] = []
    for seed in range(N_SEEDS):
        task = make_task(seed)
        for delay in DELAYS:
            metrics, trajectory = train_one(task, delay, seed)
            metric_rows.extend(metrics)
            train_rows.extend(trajectory)

    for filename, rows in [("task_metrics.csv", metric_rows), ("training_reward_trajectory.csv", train_rows)]:
        with (OUT / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    lookup = {(int(row["seed"]), int(row["delay"]), row["arm"]): row for row in metric_rows}
    seed_effects = np.empty(N_SEEDS, dtype=np.float64)
    delay_effects = []
    for seed in range(N_SEEDS):
        contrasts = []
        for delay in DELAYS:
            trace = float(lookup[(seed, delay, "ELIGIBILITY_TRACE_NORM_MATCHED")]["heldout_expected_reward"])
            no_trace = float(lookup[(seed, delay, "NO_TRACE")]["heldout_expected_reward"])
            replay = float(lookup[(seed, delay, "EXACT_REPLAY")]["heldout_expected_reward"])
            contrasts.append(trace - no_trace)
            delay_effects.append({"seed": seed, "delay": delay, "trace_minus_no_trace": trace - no_trace, "trace_minus_exact_replay": trace - replay})
        seed_effects[seed] = float(np.mean(contrasts))

    primary_mean = float(seed_effects.mean())
    primary_ci = paired_bootstrap(seed_effects)
    decision = "TRACE_ADVANTAGE_OVER_NO_TRACE_IN_THIS_BANDIT" if primary_ci[0] > 0 else "TRACE_DISADVANTAGE_IN_THIS_BANDIT" if primary_ci[1] < 0 else "INCONCLUSIVE_IN_THIS_BANDIT"
    delay_summary = []
    for delay in DELAYS:
        trace = np.array([float(lookup[(seed, delay, "ELIGIBILITY_TRACE_NORM_MATCHED")]["heldout_expected_reward"]) for seed in range(N_SEEDS)])
        no_trace = np.array([float(lookup[(seed, delay, "NO_TRACE")]["heldout_expected_reward"]) for seed in range(N_SEEDS)])
        replay = np.array([float(lookup[(seed, delay, "EXACT_REPLAY")]["heldout_expected_reward"]) for seed in range(N_SEEDS)])
        delay_summary.append({"delay": delay, "trace_mean_expected_reward": float(trace.mean()), "no_trace_mean_expected_reward": float(no_trace.mean()), "exact_replay_mean_expected_reward": float(replay.mean()), "trace_minus_no_trace": float((trace - no_trace).mean()), "trace_minus_exact_replay": float((trace - replay).mean())})

    result = {
        "status": "POST_RESULT_CONTEXTUAL_BANDIT_TRANSFER_TEST_COMPLETE",
        "primary_estimand": "mean task-seed contrast after equal averaging over four delays: eligibility trace minus no-trace held-out expected reward",
        "primary_mean_difference": primary_mean,
        "task_seed_bootstrap_95ci": primary_ci,
        "decision": decision,
        "positive_seed_count": int(np.sum(seed_effects > 0)),
        "task_seeds": N_SEEDS,
        "delay_summary": delay_summary,
        "arm_mean_heldout_expected_reward": {arm: float(np.mean([float(r["heldout_expected_reward"]) for r in metric_rows if r["arm"] == arm])) for arm in ARMS},
        "interpretation_scope": "A different synthetic objective (contextual bandit with delayed scalar reward); not biological validation or general AI-task superiority.",
    }
    (OUT / "primary_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "M5_DELAYED_REWARD_CONTEXTUAL_BANDIT",
        "contract": "M5_DELAYED_REWARD_BANDIT_CONTRACT.md",
        "master_seed": MASTER_SEED,
        "task_seeds": N_SEEDS,
        "delays": list(DELAYS),
        "arms": list(ARMS),
        "fixed_parameters": {"learning_rate": LEARNING_RATE, "eligibility_decay": GAMMA, "advantage_baseline": BASELINE},
        "task": {"context_dimension": N_CONTEXT, "actions": N_ACTIONS, "training_decisions": N_TRAIN, "heldout_contexts": N_TEST},
        "common_random_numbers": "Same task, contexts, action-choice uniforms and action-specific reward uniforms across arms and delays within task seed.",
        "independent_unit": "task seed; delays/arms paired within seed; decision steps nested",
        "post_result_status": "Outcome-informed distinct-objective follow-up; no hyperparameter search.",
        "outputs": ["task_metrics.csv", "training_reward_trajectory.csv", "primary_result.json"],
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with (OUT / "per_seed_delay_contrasts.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(delay_effects[0]))
        writer.writeheader()
        writer.writerows(delay_effects)
    print(json.dumps({"decision": decision, "primary_mean_difference": primary_mean, "ci95": primary_ci, "positive_seeds": int(np.sum(seed_effects > 0)), "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
