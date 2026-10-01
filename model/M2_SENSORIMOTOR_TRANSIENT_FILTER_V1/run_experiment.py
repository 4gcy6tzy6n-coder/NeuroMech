#!/usr/bin/env python3
"""Train and evaluate M2-inspired motor-feedback placement under transient input conflicts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_SENSORIMOTOR_TRANSIENT_FILTER_V1"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
DEFAULT_OUT = ROOT / "data/results" / NAME / "canonical"
TRAIN_BLOCKS = list(range(20))
TRAIN_SEEDS = [101_000 + i for i in TRAIN_BLOCKS]
TEST_EPISODES = 64
T = 96
BATCH = 32
UPDATES = 100
LR = 0.01
RHO = 0.70
PLANT_GAIN = 1.0 - RHO
OBS_SD = 0.25
MOTOR_SD = 0.03
PULSE_DURATIONS_TRAIN = (1, 2)
LEARNED_ARMS = ("SENSORY_SITE_1D", "OUTPUT_SITE_1D", "NO_FEEDBACK_1D", "GENERIC_RNN_1D", "GRU_8")
ARMS = LEARNED_ARMS + ("DIRECT_SENSOR", "TARGET_ORACLE")
PARAM_COUNTS = {"SENSORY_SITE_1D": 4, "OUTPUT_SITE_1D": 4, "NO_FEEDBACK_1D": 3,
                "GENERIC_RNN_1D": 6, "GRU_8": sum(p.numel() for p in nn.Sequential(nn.GRUCell(2, 8), nn.Linear(8, 1)).parameters())}
CONDITIONS = {
    "CLEAN_STABLE": {"hazard": 0.01, "pulse_rate": 0.0, "pulse_durations": ()},
    "TRANSIENT_PULSE": {"hazard": 0.01, "pulse_rate": 0.06, "pulse_durations": (2,)},
    "LONG_PULSE": {"hazard": 0.01, "pulse_rate": 0.03, "pulse_durations": (4,)},
    "SUSTAINED_SWITCH": {"hazard": 0.05, "pulse_rate": 0.02, "pulse_durations": (2,)},
    "COMBINED_STRESS": {"hazard": 0.05, "pulse_rate": 0.06, "pulse_durations": (4,)},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_batch(rng: np.random.Generator, batch: int, steps: int,
               hazard: float, pulse_rate: float, durations: tuple[int, ...]) -> tuple[np.ndarray, ...]:
    z = np.empty((batch, steps), dtype=np.float32)
    y = np.empty_like(z)
    motor_noise = rng.normal(0.0, MOTOR_SD, size=(batch, steps)).astype(np.float32)
    pulse = np.zeros((batch, steps), dtype=bool)
    for b in range(batch):
        state = int(rng.choice((-1, 1)))
        remaining = 0
        for t in range(steps):
            if t and rng.random() < hazard:
                state = -state
            if remaining == 0 and durations and rng.random() < pulse_rate:
                remaining = int(rng.choice(durations))
            active = remaining > 0
            if active:
                remaining -= 1
            z[b, t] = state
            pulse[b, t] = active
            center = -state if active else state
            y[b, t] = center + rng.normal(0.0, OBS_SD)
    return z, y, motor_noise, pulse


class ScalarSite(nn.Module):
    def __init__(self, arm: str):
        super().__init__()
        self.arm = arm
        self.w_y = nn.Parameter(torch.randn(()) * 0.2)
        self.w_h = nn.Parameter(torch.randn(()) * 0.2)
        self.w_u = nn.Parameter(torch.randn(()) * 0.2)
        self.w_m = nn.Parameter(torch.randn(()) * 0.2) if arm != "NO_FEEDBACK_1D" else None

    def initial(self, batch: int):
        return torch.zeros(batch)

    def step(self, y: torch.Tensor, motor: torch.Tensor, h: torch.Tensor):
        if self.arm == "SENSORY_SITE_1D":
            h = torch.tanh(self.w_y * y + self.w_h * h + self.w_m * motor)
            u = torch.tanh(self.w_u * h)
        elif self.arm == "OUTPUT_SITE_1D":
            h = torch.tanh(self.w_y * y + self.w_h * h)
            u = torch.tanh(self.w_u * h + self.w_m * motor)
        else:
            h = torch.tanh(self.w_y * y + self.w_h * h)
            u = torch.tanh(self.w_u * h)
        return u, h


class GenericRNN1D(nn.Module):
    def __init__(self):
        super().__init__()
        self.w_y = nn.Parameter(torch.randn(()) * 0.2)
        self.w_h = nn.Parameter(torch.randn(()) * 0.2)
        self.w_m = nn.Parameter(torch.randn(()) * 0.2)
        self.b_h = nn.Parameter(torch.zeros(()))
        self.w_u = nn.Parameter(torch.randn(()) * 0.2)
        self.b_u = nn.Parameter(torch.zeros(()))

    def initial(self, batch: int):
        return torch.zeros(batch)

    def step(self, y: torch.Tensor, motor: torch.Tensor, h: torch.Tensor):
        h = torch.tanh(self.w_y * y + self.w_h * h + self.w_m * motor + self.b_h)
        u = torch.tanh(self.w_u * h + self.b_u)
        return u, h


class GRU8(nn.Module):
    def __init__(self):
        super().__init__()
        self.cell = nn.GRUCell(2, 8)
        self.readout = nn.Linear(8, 1)

    def initial(self, batch: int):
        return torch.zeros(batch, 8)

    def step(self, y: torch.Tensor, motor: torch.Tensor, h: torch.Tensor):
        h = self.cell(torch.stack((y, motor), dim=-1), h)
        u = torch.tanh(self.readout(h).squeeze(-1))
        return u, h


def make_model(arm: str, seed: int) -> nn.Module:
    torch.manual_seed(seed)
    if arm == "GENERIC_RNN_1D":
        return GenericRNN1D()
    if arm == "GRU_8":
        return GRU8()
    return ScalarSite(arm)


def train_one(model: nn.Module, seed: int) -> tuple[float, float]:
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    start = time.perf_counter()
    final_loss = float("nan")
    model.train()
    for update in range(UPDATES):
        rng = np.random.default_rng(seed + update * 7919)
        z_np, y_np, noise_np, _ = make_batch(rng, BATCH, T, 0.02, 0.02, PULSE_DURATIONS_TRAIN)
        z = torch.from_numpy(z_np)
        y = torch.from_numpy(y_np)
        noise = torch.from_numpy(noise_np)
        h = model.initial(BATCH)
        motor = torch.zeros(BATCH)
        previous_u = torch.zeros(BATCH)
        losses = []
        for t in range(T):
            motor = RHO * motor + PLANT_GAIN * previous_u + noise[:, t]
            u, h = model.step(y[:, t], motor, h)
            losses.append((motor - z[:, t]).square())
            previous_u = u
        loss = torch.stack(losses, dim=1).mean()
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        final_loss = float(loss.detach())
    return final_loss, time.perf_counter() - start


def episode_metrics(model: nn.Module | None, arm: str, z: np.ndarray, y: np.ndarray,
                    noise: np.ndarray, pulse: np.ndarray) -> dict[str, float | int]:
    if model is not None:
        model.eval()
    with torch.no_grad():
        h = model.initial(1) if model is not None else None
        motor = torch.zeros(1)
        previous_u = torch.zeros(1)
        motors = np.empty(len(z), dtype=np.float64)
        commands = np.empty(len(z), dtype=np.float64)
        for t in range(len(z)):
            motor = RHO * motor + PLANT_GAIN * previous_u + torch.tensor([noise[t]], dtype=torch.float32)
            if arm == "TARGET_ORACLE":
                target = torch.tensor([z[t]], dtype=torch.float32)
                u = ((target - RHO * motor) / PLANT_GAIN).clamp(-1.0, 1.0)
            elif arm == "DIRECT_SENSOR":
                u = torch.tanh(2.0 * torch.tensor([y[t]], dtype=torch.float32))
            else:
                u, h = model.step(torch.tensor([y[t]], dtype=torch.float32), motor, h)
            motors[t] = float(motor.item())
            commands[t] = float(u.item())
            previous_u = u
    sign_match = (np.sign(motors) == np.sign(z)).astype(float)
    errors = np.abs(motors - z)
    switch_ix = np.flatnonzero(z[1:] != z[:-1]) + 1
    pulse_events = []
    t = 0
    while t < len(pulse):
        if not pulse[t]:
            t += 1
            continue
        end = t + 1
        while end < len(pulse) and pulse[end]:
            end += 1
        near = max(0, t - 3)
        far = min(len(z), end + 2)
        if not np.any(z[near + 1:far] != z[near:far - 1]):
            pulse_events.append((t, far))
        t = end
    pulse_window_indices = sorted({i for a, b in pulse_events for i in range(a, b)})
    latency = []
    for ix in switch_ix:
        next_switch = int(switch_ix[switch_ix > ix][0]) if np.any(switch_ix > ix) else len(z)
        stop = min(next_switch, ix + 24, len(z))
        found = None
        for start in range(int(ix), max(int(ix), stop - 2)):
            if np.all(np.sign(motors[start:start + 3]) == np.sign(z[ix])):
                found = start - int(ix)
                break
        latency.append(float(found if found is not None else min(24, next_switch - int(ix))))
    return {
        "movement_mse": float(np.mean((motors - z) ** 2)),
        "movement_mae": float(errors.mean()),
        "state_accuracy": float(sign_match.mean()),
        "command_energy": float(np.mean(commands ** 2)),
        "pulse_window_mae": float(errors[pulse_window_indices].mean()) if pulse_window_indices else float("nan"),
        "n_eligible_pulses": len(pulse_events),
        "mean_switch_latency_steps": float(np.mean(latency)) if latency else float("nan"),
        "n_target_switches": int(len(switch_ix)),
    }


def mean_ci(values: list[float], seed: int) -> dict[str, float]:
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    boot = np.mean(v[rng.integers(0, len(v), size=(20_000, len(v)))], axis=1)
    return {"mean": float(v.mean()), "median": float(np.median(v)),
            "ci95_low": float(np.quantile(boot, 0.025)), "ci95_high": float(np.quantile(boot, 0.975)),
            "n_seed_blocks": int(len(v))}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def run(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    torch.set_num_threads(1)
    random.seed(20261002)
    fit_rows: list[dict[str, object]] = []
    episode_rows: list[dict[str, object]] = []
    start_all = time.time()
    for block, train_seed in zip(TRAIN_BLOCKS, TRAIN_SEEDS):
        print(f"seed block {block + 1}/{len(TRAIN_BLOCKS)}", flush=True)
        fitted = {}
        for arm_ix, arm in enumerate(LEARNED_ARMS):
            model = make_model(arm, train_seed + arm_ix * 101)
            final_loss, seconds = train_one(model, train_seed + 10_000)
            fitted[arm] = model
            fit_rows.append({"seed_block": block, "training_seed": train_seed, "arm": arm,
                             "parameter_count": sum(p.numel() for p in model.parameters()),
                             "updates": UPDATES, "batch_size": BATCH, "sequence_length": T,
                             "final_training_loss": final_loss, "training_seconds": seconds})
        fitted["DIRECT_SENSOR"] = None
        fitted["TARGET_ORACLE"] = None
        for condition_ix, (condition, cfg) in enumerate(CONDITIONS.items()):
            for episode in range(TEST_EPISODES):
                episode_seed = 3_000_000 + block * 100_000 + condition_ix * 1_000 + episode
                rng = np.random.default_rng(episode_seed)
                z, y, noise, pulse = make_batch(rng, 1, T, cfg["hazard"], cfg["pulse_rate"], cfg["pulse_durations"])
                z, y, noise, pulse = z[0], y[0], noise[0], pulse[0]
                for arm in ARMS:
                    metrics = episode_metrics(fitted[arm], arm, z, y, noise, pulse)
                    episode_rows.append({"seed_block": block, "training_seed": train_seed, "condition": condition,
                                         "episode": episode, "episode_seed": episode_seed, "arm": arm, **metrics})
    fit_summary: list[dict[str, object]] = []
    grouped: dict[tuple[int, str, str], list[dict[str, object]]] = {}
    for row in episode_rows:
        key = (int(row["seed_block"]), str(row["arm"]), str(row["condition"]))
        grouped.setdefault(key, []).append(row)
    seed_rows = []
    metric_keys = ("movement_mse", "movement_mae", "state_accuracy", "command_energy",
                   "pulse_window_mae", "mean_switch_latency_steps")
    for (block, arm, condition), items in sorted(grouped.items()):
        summary = {}
        for metric in metric_keys:
            values = np.asarray([float(r[metric]) for r in items], dtype=np.float64)
            finite = values[np.isfinite(values)]
            summary[metric] = float(finite.mean()) if len(finite) else None
        seed_rows.append({"seed_block": block, "arm": arm, "condition": condition,
                          "n_episodes": len(items), **summary,
                          "eligible_pulse_events": sum(int(r["n_eligible_pulses"]) for r in items),
                          "target_switches": sum(int(r["n_target_switches"]) for r in items)})
    metric_summary = {}
    for condition in CONDITIONS:
        metric_summary[condition] = {}
        for arm in ARMS:
            rows = [r for r in seed_rows if r["condition"] == condition and r["arm"] == arm]
            metric_summary[condition][arm] = {}
            for mi, metric in enumerate(metric_keys):
                values = [float(r[metric]) for r in rows if r[metric] is not None and math.isfinite(float(r[metric]))]
                metric_summary[condition][arm][metric] = (mean_ci(values, 909090 + list(CONDITIONS).index(condition) * 100 + list(ARMS).index(arm) * 10 + mi)
                                                            if values else None)
    primary_values = {}
    for block in TRAIN_BLOCKS:
        sensory = next(r for r in seed_rows if r["seed_block"] == block and r["arm"] == "SENSORY_SITE_1D" and r["condition"] == "TRANSIENT_PULSE")
        output = next(r for r in seed_rows if r["seed_block"] == block and r["arm"] == "OUTPUT_SITE_1D" and r["condition"] == "TRANSIENT_PULSE")
        primary_values[block] = float(output["pulse_window_mae"]) - float(sensory["pulse_window_mae"])
    primary = mean_ci(list(primary_values.values()), 8_888_888)
    summary_json = {
        "experiment": NAME,
        "classification": "post-result exploratory artificial mechanism-transfer test",
        "training_seed_blocks": len(TRAIN_BLOCKS), "test_episodes_per_seed_arm_condition": TEST_EPISODES,
        "episodes_per_model": len(TRAIN_BLOCKS) * TEST_EPISODES * len(CONDITIONS),
        "total_episode_arm_rows": len(episode_rows), "fit_records": len(fit_rows),
        "primary_condition": "TRANSIENT_PULSE", "primary_metric": "pulse_window_mae",
        "primary_contrast": "OUTPUT_SITE_1D minus SENSORY_SITE_1D; positive favors sensory-site feedback",
        "primary_seed_block_contrast": primary,
        "primary_seed_block_values": primary_values,
        "metric_summary": metric_summary,
        "scope": "synthetic task only; no biological validation, animal-level inference, or general AI claim",
    }
    write_csv(out / "episode_metrics.csv", episode_rows)
    write_csv(out / "seed_summary.csv", seed_rows)
    write_csv(out / "fit_manifest.csv", fit_rows)
    (out / "summary.json").write_text(json.dumps(summary_json, indent=2, allow_nan=False) + "\n")
    outputs = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(out.iterdir()) if p.is_file()}
    manifest = {"experiment": NAME, "contract_sha256": sha256(CONTRACT), "runner_sha256": sha256(Path(__file__)),
                "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
                "training_seeds": TRAIN_SEEDS, "test_seed_rule": "3000000 + block*100000 + condition_index*1000 + episode",
                "conditions": CONDITIONS, "updates": UPDATES, "batch_size": BATCH, "sequence_length": T,
                "episodes_per_seed_arm_condition": TEST_EPISODES, "duration_seconds": time.time() - start_all,
                "outputs": outputs}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": "COMPLETE", "output": str(out), "primary": primary,
                      "episode_rows": len(episode_rows), "fits": len(fit_rows)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
