#!/usr/bin/env python3
"""Paired gamma-horizon sweep for a delayed-reward contextual bandit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M5_DELAYED_REWARD_TRACE_HORIZON_V1"
DEFAULT_OUT = ROOT / "data/results" / NAME
MASTER_SEED = 20260930
SEEDS = tuple(range(61, 91))
DELAYS = (1, 4, 16, 64)
GAMMAS = (0.50, 0.75, 0.90, 0.98)
N_CONTEXT, N_ACTIONS, N_TRAIN, N_TEST = 16, 2, 6000, 2000
LEARNING_RATE, BASELINE, N_BOOT = 0.01, 0.5, 20_000
ARMS = tuple(f"TRACE_GAMMA_{g:.2f}" for g in GAMMAS) + (
    "EXACT_REPLAY", "NO_TRACE_CURRENT_32")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def softmax(x: np.ndarray) -> np.ndarray:
    z = x - np.max(x)
    ex = np.exp(z)
    return ex / ex.sum()


def score_vector(context: np.ndarray, action: int, policy: np.ndarray) -> np.ndarray:
    one_hot = np.zeros(N_ACTIONS)
    one_hot[action] = 1.0
    score = np.outer(context, one_hot - policy)
    return score / max(float(np.linalg.norm(score)), 1e-12)


def make_task(seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, seed, 811]))
    theta = rng.normal(size=(N_CONTEXT, N_ACTIONS))
    x_train = rng.normal(size=(N_TRAIN, N_CONTEXT))
    x_test = rng.normal(size=(N_TEST, N_CONTEXT))
    x_train /= np.maximum(np.linalg.norm(x_train, axis=1, keepdims=True), 1e-12)
    x_test /= np.maximum(np.linalg.norm(x_test, axis=1, keepdims=True), 1e-12)
    return {
        "x_train": x_train, "x_test": x_test,
        "p_train": sigmoid(np.einsum("ni,ij->nj", x_train, theta, optimize=False)),
        "p_test": sigmoid(np.einsum("ni,ij->nj", x_test, theta, optimize=False)),
        "choice_u": rng.random(N_TRAIN),
        "reward_u": rng.random((N_TRAIN, N_ACTIONS)),
    }


def expected_reward(weights: np.ndarray, x: np.ndarray, p: np.ndarray) -> float:
    logits = np.einsum("ni,ij->nj", x, weights, optimize=False)
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    probs /= probs.sum(axis=1, keepdims=True)
    return float(np.mean(np.sum(probs * p, axis=1)))


def train_one(task: dict[str, np.ndarray], delay: int, seed: int) -> list[dict[str, object]]:
    weights = {a: np.zeros((N_CONTEXT, N_ACTIONS)) for a in ARMS}
    traces = {a: np.zeros((N_CONTEXT, N_ACTIONS)) for a in ARMS if a.startswith("TRACE_")}
    exact_scores = np.zeros((delay + 1, N_CONTEXT, N_ACTIONS))
    reward_history = {a: np.zeros(N_TRAIN) for a in ARMS}
    for t in range(N_TRAIN + delay):
        live = t < N_TRAIN
        if live:
            x = task["x_train"][t]
            current: dict[str, np.ndarray] = {}
            reward_by_arm: dict[str, float] = {}
            for arm in ARMS:
                p = softmax(np.einsum("i,ij->j", x, weights[arm], optimize=False))
                action = int(task["choice_u"][t] >= p[0])
                current[arm] = score_vector(x, action, p)
                reward_by_arm[arm] = float(task["reward_u"][t, action] < task["p_train"][t, action])
                reward_history[arm][t] = reward_by_arm[arm]
                if arm == "EXACT_REPLAY":
                    exact_scores[t % (delay + 1)] = current[arm]
            for arm in traces:
                gamma = float(arm.rsplit("_", 1)[1])
                traces[arm] = gamma * traces[arm] + current[arm]
        else:
            current = {a: np.zeros((N_CONTEXT, N_ACTIONS)) for a in ARMS}

        labeled = t - delay
        if 0 <= labeled < N_TRAIN:
            for arm in ARMS:
                if arm == "EXACT_REPLAY":
                    update_score = exact_scores[labeled % (delay + 1)]
                elif arm == "NO_TRACE_CURRENT_32":
                    update_score = current[arm]
                else:
                    tr = traces[arm]
                    update_score = tr / max(float(np.linalg.norm(tr)), 1e-12)
                weights[arm] += LEARNING_RATE * (reward_history[arm][labeled] - BASELINE) * update_score

    rows = []
    for arm in ARMS:
        rows.append({"seed": seed, "delay": delay, "arm": arm,
                     "gamma": float(arm.rsplit("_", 1)[1]) if arm.startswith("TRACE_") else "",
                     "heldout_expected_reward": expected_reward(weights[arm], task["x_test"], task["p_test"])})
    return rows


def paired_ci(x: np.ndarray, rng: np.random.Generator, familywise: bool) -> tuple[float, float]:
    boot = x[rng.integers(0, len(x), size=(N_BOOT, len(x)))].mean(axis=1)
    alpha = 0.05 / 16 if familywise else 0.05
    return float(np.quantile(boot, alpha / 2)), float(np.quantile(boot, 1 - alpha / 2))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"Refusing to overwrite nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    metrics: list[dict[str, object]] = []
    for seed in SEEDS:
        task = make_task(seed)
        for delay in DELAYS:
            metrics.extend(train_one(task, delay, seed))
    write_csv(out / "seed_metrics.csv", metrics)
    lookup = {(int(r["seed"]), int(r["delay"]), str(r["arm"])): float(r["heldout_expected_reward"]) for r in metrics}
    rng = np.random.default_rng(MASTER_SEED + 20261001)
    contrasts: list[dict[str, object]] = []
    for delay in DELAYS:
        for arm in ARMS:
            if not arm.startswith("TRACE_"):
                continue
            effects = {control: np.array([lookup[(s, delay, arm)] - lookup[(s, delay, control)] for s in SEEDS])
                       for control in ("NO_TRACE_CURRENT_32", "EXACT_REPLAY")}
            for control, values in effects.items():
                primary = control == "NO_TRACE_CURRENT_32"
                lo, hi = paired_ci(values, rng, primary)
                contrasts.append({"delay": delay, "trace_arm": arm, "control": control,
                                  "mean_difference": float(values.mean()), "ci95_low": lo, "ci95_high": hi,
                                  "seed_positive": int(np.sum(values > 0)), "n_seeds": len(SEEDS),
                                  "interval_type": "Bonferroni familywise 95%" if primary else "paired 95% descriptive"})
    write_csv(out / "paired_contrasts.csv", contrasts)
    arm_means = {arm: float(np.mean([r["heldout_expected_reward"] for r in metrics if r["arm"] == arm])) for arm in ARMS}
    summary = {"status": "COMPLETE_EXPLORATORY", "independent_unit": "task seed",
               "seed_range": [SEEDS[0], SEEDS[-1]], "n_seeds": len(SEEDS), "delays": list(DELAYS),
               "gammas": list(GAMMAS), "arm_mean_across_delay_cells": arm_means,
               "contrast_cells": len(contrasts),
               "interpretation": "Stationary synthetic delayed-reward contextual bandit; no biological or broad AI inference."}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {"experiment": NAME, "contract_sha256": sha256(ROOT / "summery" / NAME / "CONTRACT.md"),
                "runner_sha256": sha256(Path(__file__)), "python": platform.python_version(),
                "numpy": np.__version__, "master_seed": MASTER_SEED, "seeds": list(SEEDS),
                "delays": list(DELAYS), "gammas": list(GAMMAS), "learning_rate": LEARNING_RATE,
                "train_decisions": N_TRAIN, "test_contexts": N_TEST, "outputs": {},
                "state_accounting": {"trace": 32, "no_trace_current_score": 32, "exact_replay": "32*(delay+1)", "common_model_weights_excluded": True}}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "manifest.json":
            manifest["outputs"][p.name] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": summary["status"], "out": str(out), "n_metric_rows": len(metrics), "n_contrasts": len(contrasts), "arm_means": arm_means}, indent=2))


if __name__ == "__main__":
    # Function-local buffers are initialized at the start of each seed-delay fit.
    main()
