#!/usr/bin/env python3
"""Test a state-conditioned sensory update on a new synthetic latent-state task family."""
from __future__ import annotations

import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "summery/M2_CROSS_TASK_STATE_FEEDBACK_V1/CONTRACT.md"
OUT_DEFAULT = ROOT / "data/results/M2_CROSS_TASK_STATE_FEEDBACK_V1"

TRAIN_SEEDS = tuple(range(42000, 42020))
N_TRAIN_EPISODES = 256
N_TEST_EPISODES = 512
HORIZON = 160
TRAIN_STEPS = 120
LR = 0.025
BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 20261005
PHI = 0.97
PROCESS_SD = float(np.sqrt(0.05))
SIGMA_LOW = 0.25
SIGMA_HIGH = 1.40
MODE_SWITCH_PROB = 0.05
CONDITIONS = ("ALIGNED", "INDEPENDENT", "REVERSED")
POLICIES = ("MODE_GAIN_FILTER", "GENERIC_RNN_1D", "CONSTANT_GAIN_FILTER", "CURRENT_OBSERVATION", "KALMAN_LINEAR_REFERENCE")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sigmoid(x: torch.Tensor) -> torch.Tensor:
    return torch.sigmoid(torch.clamp(x, -20.0, 20.0))


def generate_data(seed: int, n: int, condition: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    target = np.empty((n, HORIZON), dtype=np.float32)
    context = np.empty((n, HORIZON), dtype=np.int8)
    high_noise = np.empty((n, HORIZON), dtype=bool)
    observation_noise = rng.standard_normal((n, HORIZON)).astype(np.float32)
    x = np.zeros(n, dtype=np.float32)
    q = rng.choice(np.asarray([-1, 1], dtype=np.int8), size=n)
    for t in range(HORIZON):
        if t:
            x = PHI * x + rng.normal(0.0, PROCESS_SD, size=n).astype(np.float32)
            q = np.where(rng.random(n) < MODE_SWITCH_PROB, -q, q).astype(np.int8)
        target[:, t] = x
        context[:, t] = q
        if condition == "ALIGNED":
            p_high = np.where(q == 1, 0.90, 0.10)
        elif condition == "INDEPENDENT":
            p_high = np.full(n, 0.50)
        elif condition == "REVERSED":
            p_high = np.where(q == 1, 0.10, 0.90)
        else:
            raise ValueError(condition)
        high_noise[:, t] = rng.random(n) < p_high
    sigma = np.where(high_noise, SIGMA_HIGH, SIGMA_LOW).astype(np.float32)
    observation = target + sigma * observation_noise
    return target, context, observation.astype(np.float32), high_noise


def model_rollout(raw: torch.Tensor, obs: torch.Tensor, q: torch.Tensor, family: str) -> torch.Tensor:
    n, horizon = obs.shape
    state = torch.zeros(n, dtype=obs.dtype, device=obs.device)
    outputs = []
    if family == "MODE_GAIN_FILTER":
        rho = 0.999 * sigmoid(raw[0])
        gain_plus = sigmoid(raw[1] + raw[2])
        gain_minus = sigmoid(raw[1] - raw[2])
        bias = 0.2 * torch.tanh(raw[3])
        gain_table = torch.where(q > 0, gain_plus, gain_minus)
        for t in range(horizon):
            prior = rho * state
            state = prior + gain_table[:, t] * (obs[:, t] - prior) + bias
            outputs.append(state)
    elif family == "GENERIC_RNN_1D":
        for t in range(horizon):
            state = torch.tanh(raw[0] * obs[:, t] + raw[1] * q[:, t] + raw[2] * state + raw[3])
            outputs.append(state)
    elif family == "CONSTANT_GAIN_FILTER":
        rho = 0.999 * sigmoid(raw[0])
        gain = sigmoid(raw[1])
        bias = 0.2 * torch.tanh(raw[2])
        for t in range(horizon):
            prior = rho * state
            state = prior + gain * (obs[:, t] - prior) + bias
            outputs.append(state)
    else:
        raise ValueError(f"unknown trainable family: {family}")
    return torch.stack(outputs, dim=1)


def train(seed: int, target: np.ndarray, context: np.ndarray, observation: np.ndarray) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    torch.set_num_threads(1)
    x = torch.from_numpy(observation)
    q = torch.from_numpy(context.astype(np.float32))
    y = torch.from_numpy(target)
    fitted: dict[str, np.ndarray] = {}
    curves: dict[str, float] = {}
    starts = {
        "MODE_GAIN_FILTER": np.asarray([3.0, 0.0, 0.0, 0.0], dtype=np.float32),
        "GENERIC_RNN_1D": np.asarray([0.7, 0.0, 0.6, 0.0], dtype=np.float32),
        "CONSTANT_GAIN_FILTER": np.asarray([3.0, 0.0, 0.0], dtype=np.float32),
    }
    for j, family in enumerate(starts):
        torch.manual_seed(seed + 101 * (j + 1))
        raw = torch.nn.Parameter(torch.from_numpy(starts[family].copy()))
        opt = torch.optim.Adam([raw], lr=LR)
        first, last = [], []
        for step in range(TRAIN_STEPS):
            pred = model_rollout(raw, x, q, family)
            loss = torch.mean((pred - y) ** 2)
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_([raw], 5.0); opt.step()
            if step < 10:
                first.append(float(loss.detach()))
            if step >= TRAIN_STEPS - 10:
                last.append(float(loss.detach()))
        fitted[family] = raw.detach().numpy().astype(float)
        curves[f"{family}_initial_train_mse"] = float(np.mean(first))
        curves[f"{family}_final_train_mse"] = float(np.mean(last))
    return fitted, curves


def predict(raw: np.ndarray, obs: np.ndarray, context: np.ndarray, family: str) -> np.ndarray:
    with torch.no_grad():
        pred = model_rollout(torch.from_numpy(raw.astype(np.float32)), torch.from_numpy(obs),
                             torch.from_numpy(context.astype(np.float32)), family)
    return pred.numpy()


def kalman_reference(obs: np.ndarray, context: np.ndarray, condition: str) -> np.ndarray:
    n, horizon = obs.shape
    state = np.zeros(n, dtype=np.float64)
    variance = np.full(n, PROCESS_SD**2 / (1.0 - PHI**2), dtype=np.float64)
    pred = np.empty_like(obs, dtype=np.float64)
    for t in range(horizon):
        if condition == "ALIGNED":
            p_high = np.where(context[:, t] > 0, .90, .10)
        elif condition == "REVERSED":
            p_high = np.where(context[:, t] > 0, .10, .90)
        else:
            p_high = np.full(n, .50)
        obs_var = p_high * SIGMA_HIGH**2 + (1.0 - p_high) * SIGMA_LOW**2
        pred_var = PHI**2 * variance + PROCESS_SD**2
        gain = pred_var / (pred_var + obs_var)
        prior = PHI * state
        state = prior + gain * (obs[:, t] - prior)
        variance = (1.0 - gain) * pred_var
        pred[:, t] = state
    return pred.astype(np.float32)


def crossed_bootstrap_ci(matrix: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n_seed, n_episode = matrix.shape
    means = np.empty(BOOTSTRAPS, dtype=np.float64)
    chunk = 100
    for start in range(0, BOOTSTRAPS, chunk):
        count = min(chunk, BOOTSTRAPS - start)
        si = rng.integers(0, n_seed, size=(count, n_seed))
        ei = rng.integers(0, n_episode, size=(count, n_episode))
        for k in range(count):
            means[start + k] = matrix[np.ix_(si[k], ei[k])].mean()
    return [float(x) for x in np.quantile(means, [.025, .975])]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    out = args.output_dir.expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory {out}")
    out.mkdir(parents=True, exist_ok=True)

    metrics_rows: list[dict[str, object]] = []
    parameter_rows: list[dict[str, object]] = []
    training_rows: list[dict[str, object]] = []
    test_data = {
        condition: generate_data(520000 + i, N_TEST_EPISODES, condition)
        for i, condition in enumerate(CONDITIONS)
    }

    for seed in TRAIN_SEEDS:
        target, context, observation, _ = generate_data(421000 + seed, N_TRAIN_EPISODES, "ALIGNED")
        fitted, curves = train(seed, target, context, observation)
        for key, value in curves.items():
            training_rows.append({"train_seed": seed, "measure": key, "value": value})
        for family, raw in fitted.items():
            parameter_rows.append({"train_seed": seed, "policy": family,
                                   "n_trainable_parameters": len(raw), "raw_parameters": json.dumps(raw.tolist())})
        for condition in CONDITIONS:
            y, q, obs, high_noise = test_data[condition]
            for policy in POLICIES:
                if policy in fitted:
                    pred = predict(fitted[policy], obs, q, policy)
                elif policy == "CURRENT_OBSERVATION":
                    pred = obs
                else:
                    pred = kalman_reference(obs, q, condition)
                squared = (pred - y) ** 2
                absolute = np.abs(pred - y)
                episode_mse = squared.mean(axis=1)
                episode_mae = absolute.mean(axis=1)
                for ep in range(N_TEST_EPISODES):
                    metrics_rows.append({
                        "train_seed": seed, "condition": condition, "episode_id": ep, "policy": policy,
                        "episode_mse": float(episode_mse[ep]), "episode_mae": float(episode_mae[ep]),
                        "high_noise_fraction": float(high_noise[ep].mean()),
                    })
        print(f"trained and evaluated seed {seed}/{TRAIN_SEEDS[-1]}", flush=True)

    metrics_path = out / "episode_metrics.csv"
    params_path = out / "learned_parameters.csv"
    training_path = out / "training_curves.csv"
    write_csv(metrics_path, metrics_rows); write_csv(params_path, parameter_rows); write_csv(training_path, training_rows)

    summaries: dict[str, object] = {}
    diff_aligned = None
    for condition in CONDITIONS:
        by_policy: dict[str, object] = {}
        mats = {}
        for policy in POLICIES:
            rows = [r for r in metrics_rows if r["condition"] == condition and r["policy"] == policy]
            matrix = np.empty((len(TRAIN_SEEDS), N_TEST_EPISODES), dtype=np.float64)
            for r in rows:
                matrix[int(r["train_seed"]) - TRAIN_SEEDS[0], int(r["episode_id"])] = float(r["episode_mse"])
            mats[policy] = matrix
            by_policy[policy] = {"mean_episode_mse": float(matrix.mean()), "mean_episode_mae": float(np.mean([float(r["episode_mae"]) for r in rows]))}
        contrast = mats["GENERIC_RNN_1D"] - mats["MODE_GAIN_FILTER"]
        contrast_summary = {
            "generic_minus_mode_gain_mse": float(contrast.mean()),
            "crossed_95_percent_bootstrap_interval": crossed_bootstrap_ci(contrast),
            "positive_training_seed_means": int((contrast.mean(axis=1) > 0).sum()),
            "n_training_seeds": len(TRAIN_SEEDS),
            "n_test_episodes": N_TEST_EPISODES,
        }
        summaries[condition] = {"policies": by_policy, "primary_family_contrast": contrast_summary}
        if condition == "ALIGNED":
            diff_aligned = contrast

    summary = {
        "experiment": "M2_CROSS_TASK_STATE_FEEDBACK_V1",
        "classification": "EXPLORATORY_ARTIFICIAL_TRANSFER_TEST_POST_RESULT_RELATIVE_TO_PROJECT",
        "question": "Does an explicit context-conditioned sensory update improve latent-state estimation over a four-parameter generic scalar RNN when the context predicts sensor reliability?",
        "primary_condition": "ALIGNED",
        "primary_estimand": "GENERIC_RNN_1D episode MSE minus MODE_GAIN_FILTER episode MSE; positive favors mode-conditioned gain",
        "primary": {"mean": float(diff_aligned.mean()), "ci95_crossed_bootstrap": crossed_bootstrap_ci(diff_aligned),
                    "positive_seed_means": int((diff_aligned.mean(axis=1) > 0).sum()),
                    "n_train_seeds": len(TRAIN_SEEDS), "n_test_episodes": N_TEST_EPISODES},
        "by_condition": summaries,
        "analysis_unit": "crossed training seed and common held-out episode; time steps averaged within episode",
        "biological_claim": "none; this is a synthetic task and one algorithmic abstraction inspired by published cell-class evidence",
        "limitations": [
            "the observation-reliability association with context is an artificial assumption, not established by the worm source study",
            "the M2 biology and prior M2 artificial outcomes were known before this new task family; exploratory, not confirmatory",
            "the primary generic RNN has one scalar recurrent state and four parameters; it does not represent a broad neural-network baseline family",
            "the linear Kalman reference uses known task dynamics and conditional expected variance and is not capacity matched",
            "this single synthetic estimation family cannot establish broad AI benefit or biological implementation",
        ],
    }
    summary_path = out / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {
        "experiment": "M2_CROSS_TASK_STATE_FEEDBACK_V1",
        "train_seed_range": [TRAIN_SEEDS[0], TRAIN_SEEDS[-1]], "n_train_episodes_per_seed": N_TRAIN_EPISODES,
        "test_episode_count_per_condition": N_TEST_EPISODES, "horizon": HORIZON, "train_updates": TRAIN_STEPS,
        "condition_order": list(CONDITIONS), "policy_order": list(POLICIES), "primary_trainable_parameter_counts": {"MODE_GAIN_FILTER": 4, "GENERIC_RNN_1D": 4},
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_resamples": BOOTSTRAPS,
        "contract_sha256": sha256(CONTRACT), "runner_sha256": sha256(Path(__file__)),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__},
        "row_counts": {"episode_metrics": len(metrics_rows), "learned_parameters": len(parameter_rows), "training_curves": len(training_rows)},
        "output_sha256": {p.name: sha256(p) for p in (metrics_path, params_path, training_path, summary_path)},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary["primary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
