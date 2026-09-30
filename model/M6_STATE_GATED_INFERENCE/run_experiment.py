#!/usr/bin/env python3
"""Exploratory state-gated filtering benchmark on a new telegraph-target task."""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_v2_corrected_metric"
N_TRAIN_SEEDS = 20
N_TRAIN_EPISODES = 512
N_TEST_EPISODES = 256
T = 320
TRAIN_HAZARD_RANGE = (0.005, 0.08)
TEST_HAZARDS = (0.005, 0.04, 0.075)
PROFILES = {
    "HIGH_REVERSAL_NOISE": (0.25, 1.20),
    "EQUAL_NOISE": (0.70, 0.70),
    "REVERSED_NOISE": (1.20, 0.25),
}


def make_trajectories(seed: int, n: int, hazards: np.ndarray, sigmas: tuple[float, float]):
    rng = np.random.default_rng(seed)
    q = np.zeros((n, T), dtype=np.int8)  # 0=forward, 1=reversal
    x = np.empty((n, T), dtype=np.float64)
    y = np.empty_like(x)
    x[:, 0] = rng.choice((-3.0, 3.0), size=n)
    for t in range(1, T):
        prev = q[:, t-1]
        u = rng.random(n)
        q[:, t] = np.where(prev == 0, u < 0.03, ~(u < 0.20)).astype(np.int8)
        x[:, t] = np.where(rng.random(n) < hazards, -x[:, t-1], x[:, t-1])
    noise_sd = np.where(q == 0, sigmas[0], sigmas[1])
    y[:] = x + rng.normal(size=(n, T)) * noise_sd
    return q, x, y


def filter_policy(kind: str, params: np.ndarray, q: np.ndarray, target: np.ndarray, y: np.ndarray) -> np.ndarray:
    n, steps = y.shape
    estimate = np.zeros(n, dtype=np.float64)
    total = np.zeros(n, dtype=np.float64)
    if kind == "STATE_GATED_GAIN":
        gains = expit(params)
    elif kind == "GLOBAL_GAIN":
        gain = float(expit(params[0]))
    elif kind == "INNOVATION_ADAPTIVE":
        b0, b1 = params
    for t in range(steps):
        residual = y[:, t] - estimate
        if kind == "STATE_GATED_GAIN":
            gain_t = gains[q[:, t]]
        elif kind == "GLOBAL_GAIN":
            gain_t = gain
        elif kind == "INNOVATION_ADAPTIVE":
            gain_t = expit(b0 + b1 * np.abs(residual))
        elif kind == "NO_MEMORY":
            estimate = y[:, t].copy()
            residual = estimate
            total += np.abs(estimate) * 0.0
            continue
        else:
            raise ValueError(kind)
        estimate += gain_t * residual
        total += np.abs(estimate - target[:, t])
    return total / steps


def fit_gains(kind: str, q: np.ndarray, target: np.ndarray, y: np.ndarray) -> np.ndarray:
    if kind == "STATE_GATED_GAIN": x0 = np.array([0.0, -1.0])
    elif kind == "GLOBAL_GAIN": x0 = np.array([0.0])
    else: x0 = np.array([0.0, 0.0])
    def loss(p):
        n, steps = y.shape
        est = np.zeros(n)
        total = 0.0
        if kind == "STATE_GATED_GAIN": gains = expit(p)
        if kind == "GLOBAL_GAIN": gain = float(expit(p[0]))
        for t in range(steps):
            resid = y[:, t] - est
            if kind == "STATE_GATED_GAIN": g = gains[q[:, t]]
            elif kind == "GLOBAL_GAIN": g = gain
            else: g = expit(p[0] + p[1] * np.abs(resid))
            est += g * resid
            total += np.abs(est - target[:, t]).mean()
        return total / steps
    result = minimize(loss, x0, method="L-BFGS-B", options={"maxiter": 300, "ftol": 1e-10})
    return result.x


def oracle_hmm_errors(q: np.ndarray, target: np.ndarray, y: np.ndarray, hazards: np.ndarray, sigmas):
    n, steps = y.shape
    pplus = np.full(n, 0.5)
    total = np.zeros(n)
    sds = np.where(q == 0, sigmas[0], sigmas[1])
    for t in range(steps):
        h = hazards
        pplus = pplus * (1.0 - h) + (1.0 - pplus) * h
        sd = sds[:, t]
        lp = -0.5 * ((y[:, t] - 3.0) / sd) ** 2 - np.log(sd)
        lm = -0.5 * ((y[:, t] + 3.0) / sd) ** 2 - np.log(sd)
        z = np.maximum(lp, lm)
        a = np.exp(lp-z) * pplus
        b = np.exp(lm-z) * (1-pplus)
        pplus = a / np.maximum(a+b, 1e-300)
        total += np.abs(3.0 * (2*pplus-1) - target[:, t])
    return total / steps


def crossed_ci(matrix: np.ndarray, seed: int, draws: int = 20000):
    # Matrix is training-seed × shared test-episode paired contrasts.
    rng = np.random.default_rng(seed)
    ns, ne = matrix.shape
    si = rng.integers(0, ns, size=(draws, ns))
    ei = rng.integers(0, ne, size=(draws, ne))
    values = matrix[si[:, :, None], ei[:, None, :]].mean(axis=(1,2))
    return [float(np.quantile(values, .025)), float(np.quantile(values, .975))]


def crossed_ci_equal_cells(matrices: list[np.ndarray], seed: int, draws: int = 20000):
    """Equal-weight cell average with seeds and test episodes resampled within cells."""
    rng = np.random.default_rng(seed)
    ns, ne = matrices[0].shape
    si = rng.integers(0, ns, size=(draws, ns))
    cell_draws = []
    for matrix in matrices:
        ei = rng.integers(0, ne, size=(draws, ne))
        cell_draws.append(matrix[si[:, :, None], ei[:, None, :]].mean(axis=(1, 2)))
    values = np.mean(cell_draws, axis=0)
    return [float(np.quantile(values, .025)), float(np.quantile(values, .975))]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    fitted = {"STATE_GATED_GAIN": [], "INNOVATION_ADAPTIVE": [], "GLOBAL_GAIN": []}
    for model_seed in range(N_TRAIN_SEEDS):
        rng = np.random.default_rng(161500 + model_seed)
        train_h = np.exp(rng.uniform(np.log(TRAIN_HAZARD_RANGE[0]), np.log(TRAIN_HAZARD_RANGE[1]), N_TRAIN_EPISODES))
        qtr, xtr, ytr = make_trajectories(550000 + model_seed, N_TRAIN_EPISODES, train_h, PROFILES["HIGH_REVERSAL_NOISE"])
        for kind in fitted:
            fitted[kind].append(fit_gains(kind, qtr, xtr, ytr))
    for hazard in TEST_HAZARDS:
        hvec = np.full(N_TEST_EPISODES, hazard)
        for profile_i, (profile, sigmas) in enumerate(PROFILES.items()):
            q, x, y = make_trajectories(770000 + profile_i * 100 + int(hazard*10000), N_TEST_EPISODES, hvec, sigmas)
            for model_seed in range(N_TRAIN_SEEDS):
                for kind, params_by_seed in fitted.items():
                    err = filter_policy(kind, params_by_seed[model_seed], q, x, y)
                    for episode, value in enumerate(err):
                        records.append({"model_seed": model_seed, "test_episode": episode, "hazard": hazard,
                                        "profile": profile, "policy": kind, "episode_mae": float(value)})
                oracle = oracle_hmm_errors(q, x, y, hvec, sigmas)
                for episode, value in enumerate(oracle):
                    records.append({"model_seed": model_seed, "test_episode": episode, "hazard": hazard,
                                    "profile": profile, "policy": "ORACLE_HMM", "episode_mae": float(value)})
                no_mem = np.abs(y - x).mean(axis=1)
                for episode, value in enumerate(no_mem):
                    records.append({"model_seed": model_seed, "test_episode": episode, "hazard": hazard,
                                    "profile": profile, "policy": "NO_MEMORY", "episode_mae": float(value)})
    with (OUT / "episode_errors.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader(); w.writerows(records)
    errors = {}
    for row in records:
        key = (row["model_seed"], row["hazard"], row["profile"], row["policy"])
        if key not in errors:
            errors[key] = np.empty(N_TEST_EPISODES, dtype=np.float64)
        errors[key][row["test_episode"]] = row["episode_mae"]
    summary = {"experiment":"M6_STATE_GATED_INFERENCE", "classification":"outcome-informed exploratory new task generator",
               "training_seeds":N_TRAIN_SEEDS,"training_episodes_per_seed":N_TRAIN_EPISODES,
               "test_episodes_per_cell":N_TEST_EPISODES,"steps":T,"policies":{},"primary":{}}
    for kind, pars in fitted.items(): summary["policies"][kind] = {"parameters_by_training_seed": [p.tolist() for p in pars]}
    primary_by_cell=[]
    for hazard in TEST_HAZARDS:
        sub=[]
        for profile in PROFILES:
            policy_vals={}
            for policy in ["STATE_GATED_GAIN","INNOVATION_ADAPTIVE","GLOBAL_GAIN","NO_MEMORY","ORACLE_HMM"]:
                vals=np.stack([errors[(s,hazard,profile,policy)] for s in range(N_TRAIN_SEEDS)])
                policy_vals[policy]=float(vals.mean())
            sub.append({"hazard":hazard,"profile":profile,"mean_mae":policy_vals})
        primary_by_cell.extend(sub)
    # build paired primary contrast matrix with seed × shared-episode factors at high reversal noise.
    matrices={}
    primary_matrices=[]
    for hazard in TEST_HAZARDS:
        mat=np.stack([errors[(s,hazard,"HIGH_REVERSAL_NOISE","STATE_GATED_GAIN")] -
                      errors[(s,hazard,"HIGH_REVERSAL_NOISE","INNOVATION_ADAPTIVE")]
                      for s in range(N_TRAIN_SEEDS)])
        primary_matrices.append(mat)
        matrices[str(hazard)]={"mean_gate_minus_adaptive":float(mat.mean()),"crossed_95ci":crossed_ci(mat,88000+int(hazard*1000))}
    summary["primary"]={"contrast":"STATE_GATED_GAIN - INNOVATION_ADAPTIVE, equal-weighted over held-out hazards under HIGH_REVERSAL_NOISE",
                         "cells":matrices,"overall_mean":float(np.mean([v["mean_gate_minus_adaptive"] for v in matrices.values()])),
                         "overall_crossed_95ci":crossed_ci_equal_cells(primary_matrices,99123)}
    summary["condition_means"]=primary_by_cell
    summary["parameter_means"]={k:np.mean(v,axis=0).tolist() for k,v in fitted.items()}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({"rows":len(records),"primary":summary["primary"],"parameter_means":summary["parameter_means"]},indent=2))

if __name__ == "__main__": main()
