#!/usr/bin/env python3
"""Post-result M2 optimizer-budget frontier on bursty partial observations."""
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
EXP = "M2_BURSTY_COMPUTE_FRONTIER_V1"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
SEEDS = tuple(range(840500, 840532))
ARMS = ("SENSORY_SITE", "OUTPUT_SITE", "NO_FEEDBACK", "GENERIC_RNN", "GRU_8")
CHECKPOINTS = (60, 120, 240)
Q_VALUES = (0.50, 0.25, 0.125)
TRAIN_Q = 0.25
NTRAIN, NTEST, T = 160, 128, 160
BATCH, LR = 16, 0.01
HAZARD, OBS_SD, STEP, ACTION_GAIN, ACTION_COST = 1 / 40, 0.25, 0.08, 1.5, 0.002
NBOOT, BOOT_SEED = 20_000, 20261002


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exogenous(seed: int, n: int, q: float, steps: int = T):
    ss = np.random.SeedSequence(seed)
    target_rng, noise_rng, vis_rng = [np.random.default_rng(x) for x in ss.spawn(3)]
    target = np.empty((n, steps), dtype=np.float32)
    state = target_rng.choice(np.array([-1.0, 1.0], dtype=np.float32), size=n)
    target[:, 0] = state
    flips = target_rng.random((n, steps)) < HAZARD
    for t in range(1, steps):
        state = np.where(flips[:, t], -state, state)
        target[:, t] = state
    visible = np.empty((n, steps), dtype=np.float32)
    visible[:, 0] = vis_rng.integers(0, 2, size=n)
    trans = vis_rng.random((n, steps)) < q
    for t in range(1, steps):
        visible[:, t] = np.where(trans[:, t], 1.0 - visible[:, t - 1], visible[:, t - 1])
    noise = noise_rng.standard_normal((n, steps)).astype(np.float32)
    return target, noise, visible


def bounded_raw(x: float) -> float:
    x = float(np.clip(x, 1e-5, 1 - 1e-5))
    return float(np.log(x / (1 - x)))


class Policy(torch.nn.Module):
    def __init__(self, arm: str):
        super().__init__()
        self.arm = arm
        self.gru = None
        self.head = None
        if arm == "SENSORY_SITE":
            init = [bounded_raw(.94), bounded_raw(.55), 0.0, -0.25]
        elif arm == "OUTPUT_SITE":
            init = [bounded_raw(.94), bounded_raw(.55), 0.0, -0.25]
        elif arm == "NO_FEEDBACK":
            init = [bounded_raw(.94), bounded_raw(.55), 0.0, 0.0]
        elif arm == "GENERIC_RNN":
            init = [0.0, 0.25, 0.0, -0.2]
        elif arm == "GRU_8":
            self.gru = torch.nn.GRUCell(3, 8)
            self.head = torch.nn.Linear(8, 1)
            return
        else:
            raise ValueError(arm)
        self.raw = torch.nn.Parameter(torch.tensor(init, dtype=torch.float32))

    def initial(self, n: int):
        return torch.zeros((n, 8), dtype=torch.float32) if self.arm == "GRU_8" else torch.zeros(n, dtype=torch.float32)

    def step(self, y, visible, h, motor_prev):
        centered_v = visible - 0.5
        if self.arm == "SENSORY_SITE":
            rho = .999 * torch.sigmoid(self.raw[0])
            alpha = torch.sigmoid(self.raw[1])
            gamma = .5 * torch.tanh(self.raw[2])
            beta = .75 * torch.tanh(self.raw[3])
            h = rho * h + alpha * y + gamma * centered_v + beta * motor_prev
            motor = torch.tanh(ACTION_GAIN * h)
        elif self.arm == "OUTPUT_SITE":
            rho = .999 * torch.sigmoid(self.raw[0])
            alpha = torch.sigmoid(self.raw[1])
            gamma = .5 * torch.tanh(self.raw[2])
            beta = .75 * torch.tanh(self.raw[3])
            h = rho * h + alpha * y + gamma * centered_v
            motor = torch.tanh(ACTION_GAIN * h + beta * motor_prev)
        elif self.arm == "NO_FEEDBACK":
            rho = .999 * torch.sigmoid(self.raw[0])
            alpha = torch.sigmoid(self.raw[1])
            gamma = .5 * torch.tanh(self.raw[2])
            bias = .15 * torch.tanh(self.raw[3])
            h = rho * h + alpha * y + gamma * centered_v + bias
            motor = torch.tanh(ACTION_GAIN * h)
        elif self.arm == "GENERIC_RNN":
            wh, wy, wv, wm = .75 * torch.tanh(self.raw)
            h = torch.tanh(wh * h + wy * y + wv * centered_v + wm * motor_prev)
            motor = torch.tanh(ACTION_GAIN * h)
        else:
            inp = torch.stack((y, centered_v, motor_prev), dim=-1)
            h = self.gru(inp, h)
            motor = torch.tanh(ACTION_GAIN * self.head(h).squeeze(-1))
        return h, motor


def rollout(target, noise, visible, model: Policy, training=False):
    target = torch.as_tensor(target, dtype=torch.float32)
    noise = torch.as_tensor(noise, dtype=torch.float32)
    visible = torch.as_tensor(visible, dtype=torch.float32)
    n, steps = target.shape
    cursor = torch.zeros(n, dtype=torch.float32)
    h = model.initial(n)
    motor_prev = torch.zeros(n, dtype=torch.float32)
    errors, motors = [], []
    for t in range(steps):
        rel = target[:, t] - cursor
        y = visible[:, t] * (rel + OBS_SD * noise[:, t])
        h, motor = model.step(y, visible[:, t], h, motor_prev)
        cursor = torch.clamp(cursor + STEP * motor, -1.0, 1.0)
        errors.append(target[:, t] - cursor)
        motors.append(motor)
        motor_prev = motor
    err = torch.stack(errors, dim=1)
    motor = torch.stack(motors, dim=1)
    if training:
        return (err.square() + ACTION_COST * motor.square()).mean()
    return err.detach().cpu().numpy(), motor.detach().cpu().numpy()


def write_csv(path: Path, rows):
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def summarize_episode(target, visible, err, motor, seed, arm, updates, q):
    rows = []
    for e in range(len(target)):
        gaps, in_gap, start = [], False, 0
        for t, v in enumerate(visible[e]):
            if v == 0 and not in_gap:
                in_gap, start = True, t
            elif v == 1 and in_gap:
                gaps.append((start, t))
                in_gap = False
        if in_gap:
            gaps.append((start, T))
        recovery = []
        for _, end in gaps:
            if end >= T:
                continue
            stop = min(T, end + 24)
            recovery.append(next((k - end for k in range(end, max(end, stop - 3))
                                  if np.all(np.abs(err[e, k:k + 4]) <= .25)), min(24, T - end)))
        rows.append({"training_seed": seed, "optimizer_updates": updates, "arm": arm,
                     "visibility_q": q, "episode_id": e,
                     "missing_fraction": float(np.mean(visible[e] == 0)),
                     "tracking_mse": float(np.mean(err[e] ** 2)),
                     "tracking_mae": float(np.mean(np.abs(err[e]))),
                     "action_energy": float(np.mean(motor[e] ** 2)),
                     "post_gap_recovery_steps": float(np.mean(recovery)) if recovery else ""})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--preflight", action="store_true")
    args = ap.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    if args.preflight:
        if any(out.iterdir()):
            raise FileExistsError(f"preflight requires empty directory: {out}")
        checks = []
        for i, arm in enumerate(ARMS):
            torch.manual_seed(1000 + i)
            model = Policy(arm)
            loss = rollout(*(x[:3] for x in exogenous(1701, 3, TRAIN_Q, 12)), model, training=True)
            loss.backward()
            checks.append({"arm": arm, "parameters": sum(p.numel() for p in model.parameters()),
                           "finite_loss": bool(torch.isfinite(loss)),
                           "finite_gradients": all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters())})
        (out / "PREFLIGHT.json").write_text(json.dumps({
            "experiment_id": EXP, "outcomes_computed": False,
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
            "training": {"seed_first": SEEDS[0], "seed_last": SEEDS[-1], "episodes": NTRAIN, "steps": T,
                         "checkpoints": CHECKPOINTS, "batch": BATCH, "learning_rate": LR, "visibility_q": TRAIN_Q},
            "evaluation": {"episodes_per_seed_condition": NTEST, "visibility_q": Q_VALUES, "arms": ARMS},
            "checks": checks}, indent=2) + "\n")
        print(json.dumps(checks, indent=2))
        return
    pf = out / "PREFLIGHT.json"
    if not pf.is_file():
        raise FileNotFoundError("run --preflight first in a clean output directory")
    pre = json.loads(pf.read_text())
    if pre["contract_sha256"] != sha(CONTRACT) or pre["runner_sha256"] != sha(Path(__file__)):
        raise RuntimeError("contract or runner changed after preflight")
    names = ("episode_results.csv", "checkpoint_results.csv", "RUN_METADATA.json")
    if any((out / f).exists() for f in names):
        raise FileExistsError("refusing to overwrite existing outcomes")

    episodes, checkpoints = [], []
    started = time.perf_counter()
    for si, seed in enumerate(SEEDS):
        train = exogenous(seed * 31 + 701, NTRAIN, TRAIN_Q)
        for ai, arm in enumerate(ARMS):
            torch.manual_seed(seed * 17 + ai)
            model = Policy(arm)
            opt = torch.optim.Adam(model.parameters(), lr=LR)
            batch_rng = np.random.default_rng(seed * 101 + ai + 700_001)
            loss_hist, training_elapsed = [], 0.0
            for update in range(1, CHECKPOINTS[-1] + 1):
                update_started = time.perf_counter()
                idx = batch_rng.integers(0, NTRAIN, size=BATCH)
                loss = rollout(*(x[idx] for x in train), model, training=True)
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                opt.step()
                training_elapsed += time.perf_counter() - update_started
                loss_hist.append(float(loss.detach()))
                if update not in CHECKPOINTS:
                    continue
                checkpoints.append({"training_seed": seed, "arm": arm, "optimizer_updates": update,
                    "parameter_count": sum(p.numel() for p in model.parameters()),
                    "last_10_update_loss": float(np.mean(loss_hist[-10:])),
                    "training_seconds_cumulative": training_elapsed,
                    "parameters_json": json.dumps({k: v.detach().reshape(-1).tolist() for k, v in model.state_dict().items()}, separators=(",", ":"))})
                model.eval()
                with torch.no_grad():
                    for qi, q in enumerate(Q_VALUES):
                        target, noise, visible = exogenous(5_100_000 + si * 100 + qi, NTEST, q)
                        err, motor = rollout(target, noise, visible, model)
                        episodes.extend(summarize_episode(target, visible, err, motor, seed, arm, update, q))
                model.train()
        print(f"completed seed {seed} ({si + 1}/{len(SEEDS)})", flush=True)
    write_csv(out / "episode_results.csv", episodes)
    write_csv(out / "checkpoint_results.csv", checkpoints)
    (out / "RUN_METADATA.json").write_text(json.dumps({
        "experiment_id": EXP, "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
        "total_runtime_seconds": time.perf_counter() - started, "seeds": list(SEEDS), "arms": ARMS,
        "checkpoints": CHECKPOINTS, "q_values": Q_VALUES,
        "parameter_counts": {arm: int(next(r["parameter_count"] for r in checkpoints if r["arm"] == arm)) for arm in ARMS},
        "episode_rows": len(episodes), "checkpoint_rows": len(checkpoints)}, indent=2) + "\n")
    print(f"Wrote {len(episodes)} episode rows and {len(checkpoints)} checkpoint rows to {out}")


if __name__ == "__main__":
    main()
