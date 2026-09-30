#!/usr/bin/env python3
"""Run frozen M5 recurrent-reservoir contextual-bandit follow-up."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "recurrent_reservoir_bandit"
MASTER_SEED = 20260930
N_CONTEXT = N_HIDDEN = 16
N_ACTIONS = 2
N_TRAIN, N_TEST, N_SEEDS = 6000, 2000, 30
DELAYS = (1, 4, 16, 64)
ARMS = ("EXACT_REPLAY", "ELIGIBILITY_TRACE_NORM_MATCHED", "NO_TRACE")
LEARNING_RATE, GAMMA, BASELINE = 0.01, 0.98, 0.5
N_BOOTSTRAPS = 20_000
ALPHA = float(np.exp(-1 / 4))


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.clip(x, -40, 40)))


def softmax(x: np.ndarray) -> np.ndarray:
    z = x - x.max()
    e = np.exp(z)
    return e / e.sum()


def make_task(seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, seed, 811]))
    theta = rng.normal(size=(N_CONTEXT, N_ACTIONS))
    train = rng.normal(size=(N_TRAIN, N_CONTEXT))
    train /= np.maximum(np.linalg.norm(train, axis=1, keepdims=True), 1e-12)
    test = rng.normal(size=(N_TEST, N_CONTEXT))
    test /= np.maximum(np.linalg.norm(test, axis=1, keepdims=True), 1e-12)
    # The fixed random reservoir is generated independently of task preferences.
    rrng = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, seed, 812]))
    win = rrng.normal(0, 4 / np.sqrt(N_CONTEXT), size=(N_HIDDEN, N_CONTEXT))
    q, _ = np.linalg.qr(rrng.normal(size=(N_HIDDEN, N_HIDDEN)))
    wrec = 0.8 * q

    def states(xs: np.ndarray) -> np.ndarray:
        h = np.zeros(N_HIDDEN)
        out = np.empty((len(xs), N_HIDDEN))
        for i, x in enumerate(xs):
            h = ALPHA * h + (1 - ALPHA) * np.tanh(win @ x + wrec @ h)
            out[i] = h
        return out

    return {
        "theta": theta, "train_contexts": train, "test_contexts": test,
        "train_features": states(train), "test_features": states(test),
        "train_prob": sigmoid(train @ theta), "test_prob": sigmoid(test @ theta),
        "choice_uniforms": rng.random(N_TRAIN),
        "reward_uniforms": rng.random((N_TRAIN, N_ACTIONS)),
        "reservoir_spectral_radius": np.array([max(abs(np.linalg.eigvals(wrec)))]),
    }


def evaluate(weights: np.ndarray, features: np.ndarray, reward_prob: np.ndarray) -> float:
    logits = features @ weights
    logits -= logits.max(axis=1, keepdims=True)
    p = np.exp(logits)
    p /= p.sum(axis=1, keepdims=True)
    return float(np.mean(np.sum(p * reward_prob, axis=1)))


def train_one(task: dict[str, np.ndarray], delay: int, seed: int):
    weights = {a: np.zeros((N_HIDDEN, N_ACTIONS)) for a in ARMS}
    eligibility = {a: np.zeros((N_HIDDEN, N_ACTIONS)) for a in ARMS}
    score_buffers = {a: [np.zeros((N_HIDDEN, N_ACTIONS)) for _ in range(delay + 1)] for a in ARMS}
    rewards = {a: np.zeros(N_TRAIN) for a in ARMS}
    trajectory = []
    for step in range(N_TRAIN + delay):
        has_context = step < N_TRAIN
        scores = {}
        if has_context:
            h = task["train_features"][step]
            for arm in ARMS:
                policy = softmax(h @ weights[arm])
                action = int(task["choice_uniforms"][step] >= policy[0])
                onehot = np.zeros(N_ACTIONS)
                onehot[action] = 1
                g = np.outer(h, onehot - policy)
                g /= max(np.linalg.norm(g), 1e-12)
                scores[arm] = g
                rewards[arm][step] = float(task["reward_uniforms"][step, action] < task["train_prob"][step, action])
                score_buffers[arm][step % (delay + 1)] = g
        else:
            scores = {a: np.zeros((N_HIDDEN, N_ACTIONS)) for a in ARMS}
        for arm in ARMS:
            eligibility[arm] = GAMMA * eligibility[arm] + scores[arm]
        labeled = step - delay
        if 0 <= labeled < N_TRAIN:
            for arm in ARMS:
                adv = rewards[arm][labeled] - BASELINE
                if arm == "EXACT_REPLAY":
                    update = score_buffers[arm][labeled % (delay + 1)]
                elif arm == "ELIGIBILITY_TRACE_NORM_MATCHED":
                    e = eligibility[arm]
                    update = e / max(np.linalg.norm(e), 1e-12)
                else:
                    update = scores[arm]
                weights[arm] += LEARNING_RATE * adv * update
        if has_context and (step + 1) % 500 == 0:
            for arm in ARMS:
                start = step + 1 - 500
                trajectory.append({"seed": seed, "delay": delay, "arm": arm,
                                   "block_start_step": start, "block_end_step": step + 1,
                                   "mean_realized_reward": float(rewards[arm][start:step + 1].mean())})
    metrics = [{"seed": seed, "delay": delay, "arm": a,
                "heldout_expected_reward": evaluate(weights[a], task["test_features"], task["test_prob"]),
                "mean_train_realized_reward": float(rewards[a].mean()),
                "n_train": N_TRAIN, "n_test": N_TEST,
                "reservoir_spectral_radius": float(task["reservoir_spectral_radius"][0])} for a in ARMS]
    return metrics, trajectory


def bootstrap(x: np.ndarray) -> list[float]:
    rng = np.random.default_rng(MASTER_SEED + 991)
    idx = rng.integers(0, len(x), size=(N_BOOTSTRAPS, len(x)))
    return [float(v) for v in np.quantile(x[idx].mean(axis=1), [0.025, 0.975])]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    metrics, trajectory = [], []
    for seed in range(N_SEEDS):
        task = make_task(seed)
        for delay in DELAYS:
            m, t = train_one(task, delay, seed)
            metrics.extend(m)
            trajectory.extend(t)
    for name, rows in (("task_metrics.csv", metrics), ("training_reward_trajectory.csv", trajectory)):
        with (OUT / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
    lookup = {(int(r["seed"]), int(r["delay"]), r["arm"]): r for r in metrics}
    effects, delay_rows, delay_summary = [], [], []
    for seed in range(N_SEEDS):
        contrasts = []
        for delay in DELAYS:
            v = {a: float(lookup[(seed, delay, a)]["heldout_expected_reward"]) for a in ARMS}
            contrasts.append(v["ELIGIBILITY_TRACE_NORM_MATCHED"] - v["NO_TRACE"])
            delay_rows.append({"seed": seed, "delay": delay,
                               "trace_minus_no_trace": contrasts[-1],
                               "trace_minus_exact_replay": v["ELIGIBILITY_TRACE_NORM_MATCHED"] - v["EXACT_REPLAY"]})
        effects.append(float(np.mean(contrasts)))
    effects = np.asarray(effects)
    ci = bootstrap(effects)
    decision = "TRACE_ADVANTAGE_OVER_NO_TRACE_IN_THIS_RESERVOIR_BANDIT" if ci[0] > 0 else "TRACE_DISADVANTAGE_IN_THIS_RESERVOIR_BANDIT" if ci[1] < 0 else "INCONCLUSIVE_IN_THIS_RESERVOIR_BANDIT"
    for d in DELAYS:
        means = {a: float(np.mean([float(lookup[(s, d, a)]["heldout_expected_reward"]) for s in range(N_SEEDS)])) for a in ARMS}
        delay_summary.append({"delay": d, "trace_mean_expected_reward": means["ELIGIBILITY_TRACE_NORM_MATCHED"],
                              "no_trace_mean_expected_reward": means["NO_TRACE"], "exact_replay_mean_expected_reward": means["EXACT_REPLAY"],
                              "trace_minus_no_trace": means["ELIGIBILITY_TRACE_NORM_MATCHED"] - means["NO_TRACE"],
                              "trace_minus_exact_replay": means["ELIGIBILITY_TRACE_NORM_MATCHED"] - means["EXACT_REPLAY"]})
    result = {"status": "POST_RESULT_RECURRENT_RESERVOIR_BANDIT_COMPLETE", "primary_estimand": "mean task-seed contrast after equal averaging over four delays: eligibility trace minus no-trace held-out expected reward",
              "primary_mean_difference": float(effects.mean()), "task_seed_bootstrap_95ci": ci, "decision": decision,
              "positive_seed_count": int(np.sum(effects > 0)), "task_seeds": N_SEEDS, "delay_summary": delay_summary,
              "arm_mean_heldout_expected_reward": {a: float(np.mean([float(r["heldout_expected_reward"]) for r in metrics if r["arm"] == a])) for a in ARMS},
              "interpretation_scope": "Fixed random recurrent reservoir with learned linear readout on one synthetic contextual-bandit objective; no recurrent-core training, LNN/LTC, biological validation, or connectome transfer."}
    (OUT / "primary_result.json").write_text(json.dumps(result, indent=2) + "\n")
    with (OUT / "per_seed_delay_contrasts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(delay_rows[0])); w.writeheader(); w.writerows(delay_rows)
    manifest = {"experiment": "M5_RECURRENT_RESERVOIR_BANDIT", "contract": "M5_RECURRENT_RESERVOIR_BANDIT_CONTRACT.md",
                "master_seed": MASTER_SEED, "task_seeds": N_SEEDS, "delays": list(DELAYS), "arms": list(ARMS),
                "fixed_parameters": {"learning_rate": LEARNING_RATE, "eligibility_decay": GAMMA, "baseline": BASELINE, "reservoir_leak_alpha": ALPHA, "reservoir_spectral_radius": 0.8},
                "task": {"context_dimension": N_CONTEXT, "reservoir_units": N_HIDDEN, "actions": N_ACTIONS, "training_decisions": N_TRAIN, "heldout_contexts": N_TEST},
                "reservoir_core": "Fixed seed-specific Gaussian W_in and orthogonal W_rec with radius 0.8; only readout weights trained.",
                "common_random_numbers": "Task, contexts, choice uniforms, and action-specific reward uniforms shared across arms and delays within seed.",
                "independent_unit": "Task seed; delays/arms are paired repeated measures; decision steps are nested.",
                "post_result_status": "Outcome-informed exploratory architecture follow-up; no parameter tuning.",
                "outputs": ["task_metrics.csv", "training_reward_trajectory.csv", "per_seed_delay_contrasts.csv", "primary_result.json"]}
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"decision": decision, "primary_mean_difference": result["primary_mean_difference"], "ci95": ci, "positive_seeds": result["positive_seed_count"], "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
