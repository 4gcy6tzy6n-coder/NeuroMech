#!/usr/bin/env python3
"""Closed-loop tracking transfer test for sensory-site motor feedback."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
ID = "M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1"
CONTRACT = ROOT / "summery" / ID / "CONTRACT.md"
DEFAULT_OUT = ROOT / "data" / "results" / ID / "canonical"
SEEDS = tuple(range(410000, 410032))
ARMS = ("SENSORY_SITE_FEEDBACK", "OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "GENERIC_RNN_1H", "ORACLE_RELATIVE_ERROR")
HAZARDS = (1 / 240, 1 / 120, 1 / 40)
MISSING_RATES = (0.25, 0.50, 0.75)
TRAIN_HAZARD, TRAIN_MISSING = 1 / 120, 0.50
TRAIN_EPISODES, TEST_EPISODES, T = 256, 256, 240
UPDATES, BATCH, LR = 100, 16, 0.01
STEP, OBS_SD, ACTION_GAIN, ACTION_COST = 0.08, 0.25, 1.5, 0.002
BOOTSTRAPS, BOOT_SEED = 10_000, 20261018


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def target_stream(seed: int, n: int, hazard: float, t: int = T) -> np.ndarray:
    rng = np.random.default_rng(seed)
    state = rng.choice(np.array([-1.0, 1.0], dtype=np.float32), size=n)
    out = np.empty((n, t), dtype=np.float32)
    out[:, 0] = state
    flips = rng.random((n, t)) < hazard
    for k in range(1, t):
        state = np.where(flips[:, k], -state, state)
        out[:, k] = state
    return out


def exogenous(seed: int, n: int, hazard: float, missing: float, t: int = T):
    rng = np.random.default_rng(seed)
    target = target_stream(seed + 73, n, hazard, t)
    noise = rng.standard_normal((n, t)).astype(np.float32)
    visible = (rng.random((n, t)) >= missing).astype(np.float32)
    return target, noise, visible


def condition_seed(seed_i: int, hazard_i: int, missing_i: int) -> int:
    return 2_300_000 + seed_i * 1000 + hazard_i * 100 + missing_i * 10


def bounded_raw(prob: float) -> float:
    p = np.clip(prob / 0.999, 1e-5, 1 - 1e-5)
    return float(np.log(p / (1 - p)))


class Policy(torch.nn.Module):
    def __init__(self, arm: str):
        super().__init__()
        self.arm = arm
        if arm == "SENSORY_SITE_FEEDBACK":
            init = [bounded_raw(0.94), 0.4, -0.4]
        elif arm == "OUTPUT_SITE_PERSISTENCE":
            init = [bounded_raw(0.94), 0.4, 0.1]
        elif arm == "NO_FEEDBACK":
            init = [bounded_raw(0.94), 0.4, 0.0]
        elif arm == "GENERIC_RNN_1H":
            init = [0.4, 0.4, -0.2]
        else:
            raise ValueError(arm)
        self.raw = torch.nn.Parameter(torch.tensor(init, dtype=torch.float32))

    def step(self, y, h, motor_prev):
        if self.arm == "SENSORY_SITE_FEEDBACK":
            rho = 0.999 * torch.sigmoid(self.raw[0])
            alpha = torch.sigmoid(self.raw[1])
            beta = 0.75 * torch.tanh(self.raw[2])
            h = rho * h + alpha * y + beta * motor_prev
            motor = torch.tanh(ACTION_GAIN * h)
        elif self.arm == "OUTPUT_SITE_PERSISTENCE":
            rho = 0.999 * torch.sigmoid(self.raw[0])
            alpha = torch.sigmoid(self.raw[1])
            beta = 0.75 * torch.tanh(self.raw[2])
            h = rho * h + alpha * y
            motor = torch.tanh(ACTION_GAIN * h + beta * motor_prev)
        elif self.arm == "NO_FEEDBACK":
            rho = 0.999 * torch.sigmoid(self.raw[0])
            alpha = torch.sigmoid(self.raw[1])
            bias = 0.15 * torch.tanh(self.raw[2])
            h = rho * h + alpha * y + bias
            motor = torch.tanh(ACTION_GAIN * h)
        else:
            wh, wy, wm = 0.75 * torch.tanh(self.raw)
            h = torch.tanh(wh * h + wy * y + wm * motor_prev)
            motor = torch.tanh(ACTION_GAIN * h)
        return h, motor


def rollout(arm: str, target, noise, visible, *, model: Policy | None = None, training: bool = False):
    n, steps = target.shape
    dtype = torch.float32
    target = torch.as_tensor(target, dtype=dtype)
    noise = torch.as_tensor(noise, dtype=dtype)
    visible = torch.as_tensor(visible, dtype=dtype)
    cursor = torch.zeros(n, dtype=dtype)
    h = torch.zeros(n, dtype=dtype)
    motor_prev = torch.zeros(n, dtype=dtype)
    errors, motors = [], []
    for t in range(steps):
        rel = target[:, t] - cursor
        y = visible[:, t] * (rel + OBS_SD * noise[:, t])
        if arm == "ORACLE_RELATIVE_ERROR":
            motor = torch.tanh(ACTION_GAIN * rel)
        else:
            h, motor = model.step(y, h, motor_prev)
        cursor = torch.clamp(cursor + STEP * motor, -1.0, 1.0)
        errors.append(target[:, t] - cursor)
        motors.append(motor)
        motor_prev = motor
    err = torch.stack(errors, dim=1)
    motor = torch.stack(motors, dim=1)
    if training:
        return (err.square() + ACTION_COST * motor.square()).mean()
    return err.detach().cpu().numpy(), motor.detach().cpu().numpy()


def switch_recovery(target: np.ndarray, errors: np.ndarray, limit: int = 60) -> float:
    lags = []
    n, tmax = target.shape
    for i in range(n):
        switches = np.flatnonzero(target[i, 1:] != target[i, :-1]) + 1
        for start in switches:
            stop = min(start + limit, tmax)
            next_switch = np.flatnonzero(target[i, start + 1:] != target[i, start:-1])
            if len(next_switch):
                stop = min(stop, start + 1 + int(next_switch[0]))
            recovered = limit
            for k in range(start, max(start, stop - 4)):
                if np.all(np.abs(errors[i, k:k + 5]) <= 0.25):
                    recovered = k - start
                    break
            lags.append(recovered)
    return float(np.mean(lags)) if lags else float("nan")


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--preflight", action="store_true")
    args = ap.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.preflight:
        if any(out.iterdir()):
            raise FileExistsError(f"preflight output directory must be empty: {out}")
        torch.set_num_threads(1)
        checks = []
        for arm in ARMS[:-1]:
            model = Policy(arm)
            tgt, noise, vis = exogenous(17, 2, TRAIN_HAZARD, TRAIN_MISSING, 8)
            loss = rollout(arm, tgt, noise, vis, model=model, training=True)
            loss.backward()
            checks.append({"arm": arm, "parameters": sum(p.numel() for p in model.parameters()),
                           "finite_loss": bool(torch.isfinite(loss)), "finite_grad": all(torch.isfinite(p.grad).all() for p in model.parameters())})
        (out / "PREFLIGHT.json").write_text(json.dumps({
            "experiment_id": ID, "outcomes_computed": False, "python": platform.python_version(),
            "numpy": np.__version__, "torch": torch.__version__, "contract_sha256": sha(CONTRACT),
            "runner_sha256": sha(Path(__file__)), "checks": checks,
            "training": {"seeds": [SEEDS[0], SEEDS[-1]], "episodes": TRAIN_EPISODES, "steps": T,
                         "updates": UPDATES, "batch": BATCH, "learning_rate": LR},
            "evaluation": {"episodes_per_seed_condition": TEST_EPISODES, "hazards": HAZARDS,
                           "missing_rates": MISSING_RATES, "arms": ARMS},
            "primary_bootstrap": {"n": BOOTSTRAPS, "seed": BOOT_SEED}
        }, indent=2) + "\n")
        print(json.dumps(checks, indent=2))
        return
    pre = out / "PREFLIGHT.json"
    if not pre.exists():
        raise FileNotFoundError("run --preflight first in an empty output directory")
    preflight = json.loads(pre.read_text())
    if preflight["contract_sha256"] != sha(CONTRACT) or preflight["runner_sha256"] != sha(Path(__file__)):
        raise RuntimeError("contract or runner changed after preflight")
    if any((out / f).exists() for f in ("episode_results.csv", "training_results.csv", "summary.json")):
        raise FileExistsError("refusing to overwrite prior experiment results")
    torch.set_num_threads(1)
    episode_rows, fit_rows = [], []
    start_all = time.perf_counter()
    for seed_i, seed in enumerate(SEEDS):
        tr_target, tr_noise, tr_visible = exogenous(seed * 17 + 101, TRAIN_EPISODES, TRAIN_HAZARD, TRAIN_MISSING)
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed + 990_001)
        for arm_i, arm in enumerate(ARMS[:-1]):
            torch.manual_seed(seed * 100 + arm_i)
            model = Policy(arm)
            opt = torch.optim.Adam(model.parameters(), lr=LR)
            fit_start = time.perf_counter()
            losses = []
            for _ in range(UPDATES):
                idx = rng.integers(0, TRAIN_EPISODES, size=BATCH)
                batch = (tr_target[idx], tr_noise[idx], tr_visible[idx])
                loss = rollout(arm, *batch, model=model, training=True)
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                opt.step()
                losses.append(float(loss.detach()))
            fit_rows.append({"training_seed": seed, "arm": arm,
                             "parameter_count": sum(p.numel() for p in model.parameters()),
                             "updates": UPDATES, "batch_size": BATCH, "sequence_steps_per_fit": UPDATES * BATCH * T,
                             "training_seconds": time.perf_counter() - fit_start,
                             "initial_loss": losses[0], "final_10_update_loss": float(np.mean(losses[-10:])),
                             "parameters_json": json.dumps(model.raw.detach().tolist())})
            model.eval()
            with torch.no_grad():
                for hi, hazard in enumerate(HAZARDS):
                    for mi, miss in enumerate(MISSING_RATES):
                        cond_seed = condition_seed(seed_i, hi, mi)
                        target, noise, visible = exogenous(cond_seed, TEST_EPISODES, hazard, miss)
                        err, motor = rollout(arm, target, noise, visible, model=model)
                        rec = np.array([switch_recovery(target[k:k+1], err[k:k+1]) for k in range(TEST_EPISODES)])
                        for ep in range(TEST_EPISODES):
                            episode_rows.append({"training_seed": seed, "condition_hazard": hazard,
                                "condition_missing": miss, "episode_id": ep, "arm": arm,
                                "tracking_mse": float(np.mean(err[ep] ** 2)),
                                "tracking_mae": float(np.mean(np.abs(err[ep]))),
                                "action_energy": float(np.mean(motor[ep] ** 2)),
                                "switch_recovery_steps": "" if np.isnan(rec[ep]) else float(rec[ep])})
        # The oracle is evaluated once per test condition, then recorded under the same grid.
        for hi, hazard in enumerate(HAZARDS):
            for mi, miss in enumerate(MISSING_RATES):
                cond_seed = condition_seed(seed_i, hi, mi)
                target, noise, visible = exogenous(cond_seed, TEST_EPISODES, hazard, miss)
                err, motor = rollout("ORACLE_RELATIVE_ERROR", target, noise, visible)
                rec = np.array([switch_recovery(target[k:k+1], err[k:k+1]) for k in range(TEST_EPISODES)])
                for ep in range(TEST_EPISODES):
                    episode_rows.append({"training_seed": seed, "condition_hazard": hazard,
                        "condition_missing": miss, "episode_id": ep, "arm": "ORACLE_RELATIVE_ERROR",
                        "tracking_mse": float(np.mean(err[ep] ** 2)),
                        "tracking_mae": float(np.mean(np.abs(err[ep]))),
                        "action_energy": float(np.mean(motor[ep] ** 2)),
                        "switch_recovery_steps": "" if np.isnan(rec[ep]) else float(rec[ep])})
        print(f"completed training seed {seed} ({seed_i + 1}/{len(SEEDS)})", flush=True)
    write_csv(out / "episode_results.csv", episode_rows)
    write_csv(out / "training_results.csv", fit_rows)
    (out / "RUN_METADATA.json").write_text(json.dumps({
        "experiment_id": ID, "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
        "total_wall_seconds": time.perf_counter() - start_all, "episode_rows": len(episode_rows),
        "training_rows": len(fit_rows), "python": platform.python_version(), "numpy": np.__version__,
        "torch": torch.__version__
    }, indent=2) + "\n")
    print(f"wrote {len(episode_rows)} episode rows and {len(fit_rows)} fits to {out}", flush=True)


if __name__ == "__main__":
    main()
