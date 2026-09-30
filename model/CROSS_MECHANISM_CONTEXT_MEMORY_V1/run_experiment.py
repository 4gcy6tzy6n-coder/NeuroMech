#!/usr/bin/env python3
"""Exploratory shared-workflow comparison of M2 context gain and M5 eligibility."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

SEEDS = 32
BOOT = 10_000
BOOT_SEED = 20261001
M5_DIM = 16
M5_TRIALS = 256
M5_TEST = 512
DELAYS = (1, 4, 16, 64)
KAPPAS = (1.0, 0.0, -1.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def simulate_m2(rng: np.random.Generator, n_ep: int, length: int, kappa: float):
    """Return state, observation, context arrays; κ controls cue/noise association."""
    n = n_ep * length
    state = np.empty(n, dtype=np.float64)
    obs = np.empty(n, dtype=np.float64)
    ctx = rng.choice((-1.0, 1.0), size=n)
    s = float(rng.choice((-1.0, 1.0)))
    # A Bernoulli cue/noise relation implements matched, absent, or reversed mapping.
    same = rng.random(n) < ((1.0 + kappa) / 2.0)
    low_noise_ctx = np.where(same, ctx, -ctx)
    for i in range(n):
        if rng.random() < 0.04:
            s = -s
        state[i] = s
        sigma = 0.35 if low_noise_ctx[i] > 0 else 1.1
        obs[i] = s + rng.normal(0.0, sigma)
    return state.reshape(n_ep, length), obs.reshape(n_ep, length), ctx.reshape(n_ep, length)


def filt_gain(obs: np.ndarray, ctx: np.ndarray, p: np.ndarray) -> np.ndarray:
    g0, g1, bias = p
    out = np.zeros_like(obs)
    for t in range(obs.shape[1]):
        prev = out[:, t - 1] if t else 0.0
        g = np.clip(g0 + g1 * ctx[:, t], 0.001, 0.999)
        out[:, t] = (1.0 - g) * prev + g * obs[:, t] + bias
    return out


def filt_additive(obs: np.ndarray, ctx: np.ndarray, p: np.ndarray) -> np.ndarray:
    a, b, c = p
    out = np.zeros_like(obs)
    for t in range(obs.shape[1]):
        prev = out[:, t - 1] if t else 0.0
        out[:, t] = a * prev + b * obs[:, t] + c * ctx[:, t]
    return out


def fit_m2(state: np.ndarray, obs: np.ndarray, ctx: np.ndarray):
    target = state.ravel()
    def rg(p):
        return (filt_gain(obs, ctx, p).ravel() - target)
    def ra(p):
        return (filt_additive(obs, ctx, p).ravel() - target)
    gain = least_squares(rg, np.array([0.4, 0.0, 0.0]), bounds=([0.001, -0.49, -0.2], [0.999, 0.49, 0.2]), max_nfev=100)
    additive = least_squares(ra, np.array([0.8, 0.15, 0.0]), bounds=([0.0, 0.0, -0.3], [0.999, 1.0, 0.3]), max_nfev=100)
    return gain.x, additive.x


def run_m2(seed: int):
    rng = np.random.default_rng(810_000 + seed)
    train_s, train_y, train_c = simulate_m2(rng, 24, 300, 1.0)
    pg, pa = fit_m2(train_s, train_y, train_c)
    rows = []
    for kappa in KAPPAS:
        s, y, c = simulate_m2(rng, 64, 300, kappa)
        eg = filt_gain(y, c, pg) - s
        ea = filt_additive(y, c, pa) - s
        rows.append({"seed": seed, "kappa": kappa,
                     "context_gain_mse": float(np.mean(eg * eg)),
                     "additive_control_mse": float(np.mean(ea * ea)),
                     "control_minus_gain": float(np.mean(ea * ea) - np.mean(eg * eg)),
                     "gain_parameters": json.dumps(pg.tolist()),
                     "control_parameters": json.dumps(pa.tolist())})
    return rows


def sign(x):
    return np.where(x >= 0.0, 1.0, -1.0)


def run_m5(seed: int):
    rng = np.random.default_rng(920_000 + seed)
    teacher = rng.normal(size=M5_DIM)
    teacher /= np.linalg.norm(teacher)
    rows = []
    for delay in DELAYS:
        arms = {"eligibility": np.zeros(M5_DIM), "misassignment": np.zeros(M5_DIM), "replay": np.zeros(M5_DIM)}
        for _ in range(M5_TRIALS):
            x = rng.normal(size=M5_DIM)
            x /= np.linalg.norm(x)
            y = 1.0 if np.dot(teacher, x) + rng.normal(0, 0.15) >= 0 else -1.0
            distractors = rng.normal(size=(delay, M5_DIM))
            distractors /= np.linalg.norm(distractors, axis=1, keepdims=True)
            # Event-specific biological-style eligibility state decays during the delay.
            e = x * (0.95 ** delay)
            current = distractors[-1]
            eta = 0.08
            for name, w in arms.items():
                if name == "eligibility":
                    update = e
                elif name == "misassignment":
                    update = current
                else:
                    update = x
                pred = float(np.dot(w, x))
                # Delayed teaching signal applies a local, norm-bounded perceptron update.
                w += eta * y * update
                np.clip(w, -4.0, 4.0, out=w)
        x_test = rng.normal(size=(M5_TEST, M5_DIM))
        x_test /= np.linalg.norm(x_test, axis=1, keepdims=True)
        y_test = sign(np.sum(x_test * teacher[None, :], axis=1))
        acc = {name: float(np.mean(sign(np.sum(x_test * w[None, :], axis=1)) == y_test))
               for name, w in arms.items()}
        rows.append({"seed": seed, "delay": delay, "eligibility_accuracy": acc["eligibility"],
                     "misassignment_accuracy": acc["misassignment"], "replay_accuracy": acc["replay"],
                     "eligibility_minus_misassignment": acc["eligibility"] - acc["misassignment"],
                     "eligibility_minus_replay": acc["eligibility"] - acc["replay"],
                     "learned_parameters": M5_DIM, "eligibility_state_dimensions": M5_DIM,
                     "misassignment_state_dimensions": 0, "replay_state_dimensions": M5_DIM})
    return rows


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def bootstrap(values: np.ndarray, rng: np.random.Generator):
    means = np.mean(values[rng.integers(0, len(values), (BOOT, len(values)))], axis=1)
    return {"mean": float(np.mean(values)), "ci95": [float(np.quantile(means, .025)), float(np.quantile(means, .975))],
            "positive_seed_blocks": int(np.sum(values > 0)), "n_seed_blocks": int(len(values))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V1/canonical")
    args = ap.parse_args()
    out = Path(args.output_dir)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    m2 = [r for seed in range(SEEDS) for r in run_m2(seed)]
    m5 = [r for seed in range(SEEDS) for r in run_m5(seed)]
    write_csv(out / "m2_seed_results.csv", m2)
    write_csv(out / "m5_seed_results.csv", m5)
    rng = np.random.default_rng(BOOT_SEED)
    m2_summary = {}
    for k in KAPPAS:
        vals = np.array([r["control_minus_gain"] for r in m2 if r["kappa"] == k])
        m2_summary[str(k)] = bootstrap(vals, rng)
    m5_summary = {}
    m5_replay_summary = {}
    for d in DELAYS:
        vals = np.array([r["eligibility_minus_misassignment"] for r in m5 if r["delay"] == d])
        m5_summary[str(d)] = bootstrap(vals, rng)
        replay_vals = np.array([r["eligibility_minus_replay"] for r in m5 if r["delay"] == d])
        m5_replay_summary[str(d)] = bootstrap(replay_vals, rng)
    summary = {"experiment_id": "CROSS_MECHANISM_CONTEXT_MEMORY_V1", "classification": "EXPLORATORY_POST_RESULT",
               "seed_blocks": SEEDS, "bootstrap_resamples": BOOT, "bootstrap_seed": BOOT_SEED,
               "m2_primary_native_outcome": "control_minus_context_gain_MSE; positive favors context gain",
               "m2_by_context_mapping": m2_summary,
               "m5_primary_native_outcome": "eligibility_minus_misassignment_accuracy; positive favors eligibility",
               "m5_by_delay": m5_summary,
               "m5_eligibility_minus_capacity_matched_persistent_cue_by_delay": m5_replay_summary,
               "resource_accounting": {"m2_parameter_count_each_arm": 3, "m5_learned_parameters_each_arm": M5_DIM,
                                       "m5_trace_state_dimensions": M5_DIM,
                                       "m5_misassignment_state_dimensions": 0,
                                       "m5_replay_state_dimensions": M5_DIM,
                                       "m5_trace_total_state_dimensions_including_weights": 2 * M5_DIM,
                                       "m5_misassignment_total_state_dimensions_including_weights": M5_DIM,
                                       "m5_replay_total_state_dimensions_including_weights": 2 * M5_DIM},
               "claim_boundary": "No pooled cross-mechanism effect, biological validation, or general AI claim."}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {"python": __import__("sys").version, "numpy": np.__version__,
                "scipy": __import__("scipy").__version__, "seeds": SEEDS,
                "runner_sha256": sha256(Path(__file__).resolve()),
                "contract_sha256": sha256(Path("summery/CROSS_MECHANISM_CONTEXT_MEMORY_V1/CONTRACT.md")),
                "files": {p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file()}}
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
