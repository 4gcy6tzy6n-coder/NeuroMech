#!/usr/bin/env python3
"""Test self-contingent versus population-matched motor feedback in a tracking controller."""
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
NAME = "M2_FEEDBACK_TEMPORAL_ALIGNMENT_V1"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
DEFAULT_OUT = ROOT / "data/results" / NAME / "canonical"

BLOCKS = tuple(range(32))
TRAIN_SEEDS = tuple(820_000 + b for b in BLOCKS)
ARMS = ("SELF_SENSORY", "LAG1_SENSORY", "LAG4_SENSORY", "CROSS_AGENT_YOKED_SENSORY", "SELF_OUTPUT", "NO_FEEDBACK", "GENERIC_RNN_1D", "GRU_8")
PARAMS = {"SELF_SENSORY": 4, "LAG1_SENSORY": 4, "LAG4_SENSORY": 4, "CROSS_AGENT_YOKED_SENSORY": 4, "SELF_OUTPUT": 4,
          "NO_FEEDBACK": 3, "GENERIC_RNN_1D": 6, "GRU_8": 297}
CONDITIONS = {
    "SLOW_TRANSIENT": {"hazard": 0.01, "pulse_rate": 0.08},
    "FAST_TRANSIENT": {"hazard": 0.05, "pulse_rate": 0.08},
    "SLOW_CLEAN": {"hazard": 0.01, "pulse_rate": 0.00},
    "FAST_CLEAN": {"hazard": 0.05, "pulse_rate": 0.00},
}
T = 96
N_TRAIN = 32
N_TEST = 128
PULSE_DURATION = 2
TRAIN_HAZARD = 0.02
TRAIN_PULSE_RATE = 0.03
UPDATES = 100
BATCH = 32
LR = 0.01
MOTOR_RHO = 0.70
MOTOR_GAIN = 1.0 - MOTOR_RHO
OBS_SD = 0.25
MOTOR_SD = 0.03
FEEDBACK_SLOPE = 5.0
BOOTSTRAPS = 20_000
PRIMARY_BOOTSTRAP_SEED = 8_765_432
METRICS = ("movement_mse", "movement_mae", "state_accuracy", "command_energy", "mean_switch_latency_steps")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write an empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_batch(seed: int, n: int, hazard: float, pulse_rate: float) -> tuple[np.ndarray, ...]:
    rng = np.random.default_rng(seed)
    target = np.empty((n, T), dtype=np.float32)
    pulse = np.zeros((n, T), dtype=bool)
    observation = np.empty((n, T), dtype=np.float32)
    motor_noise = rng.normal(0.0, MOTOR_SD, size=(n, T)).astype(np.float32)
    state = rng.choice(np.asarray([-1.0, 1.0], dtype=np.float32), size=n)
    remaining = np.zeros(n, dtype=np.int8)
    for t in range(T):
        if t:
            switch = rng.random(n) < hazard
            state = np.where(switch, -state, state)
            starts = (remaining == 0) & (rng.random(n) < pulse_rate)
            remaining[starts] = PULSE_DURATION
        active = remaining > 0
        pulse[:, t] = active
        center = np.where(active, -state, state)
        target[:, t] = state
        observation[:, t] = center + rng.normal(0.0, OBS_SD, size=n).astype(np.float32)
        remaining[active] -= 1
    return target, observation, motor_noise, pulse


class ScalarController(nn.Module):
    def __init__(self, arm: str):
        super().__init__()
        self.arm = arm
        self.w_y = nn.Parameter(torch.randn(()) * 0.2)
        self.w_h = nn.Parameter(torch.randn(()) * 0.2)
        self.w_u = nn.Parameter(torch.randn(()) * 0.2)
        if arm != "NO_FEEDBACK":
            self.w_f = nn.Parameter(torch.randn(()) * 0.2)
        if arm == "GENERIC_RNN_1D":
            self.b_h = nn.Parameter(torch.zeros(()))
            self.b_u = nn.Parameter(torch.zeros(()))

    def initial(self, n: int) -> torch.Tensor:
        return torch.zeros(n)

    def step(self, y: torch.Tensor, own_motor: torch.Tensor, feedback: torch.Tensor,
             h: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if self.arm in ("SELF_SENSORY", "LAG1_SENSORY", "LAG4_SENSORY", "CROSS_AGENT_YOKED_SENSORY"):
            h = torch.tanh(self.w_y * y + self.w_h * h + self.w_f * feedback)
            u = torch.tanh(self.w_u * h)
        elif self.arm == "SELF_OUTPUT":
            h = torch.tanh(self.w_y * y + self.w_h * h)
            u = torch.tanh(self.w_u * h + self.w_f * feedback)
        elif self.arm == "NO_FEEDBACK":
            h = torch.tanh(self.w_y * y + self.w_h * h)
            u = torch.tanh(self.w_u * h)
        else:
            h = torch.tanh(self.w_y * y + self.w_h * h + self.w_f * feedback + self.b_h)
            u = torch.tanh(self.w_u * h + self.b_u)
        return u, h


class GRUController(nn.Module):
    def __init__(self):
        super().__init__()
        self.cell = nn.GRUCell(2, 8)
        self.readout = nn.Linear(8, 1)

    def initial(self, n: int) -> torch.Tensor:
        return torch.zeros(n, 8)

    def step(self, y: torch.Tensor, own_motor: torch.Tensor, feedback: torch.Tensor,
             h: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.cell(torch.stack((y, feedback), dim=-1), h)
        u = torch.tanh(self.readout(h).squeeze(-1))
        return u, h


def make_model(arm: str, seed: int) -> nn.Module:
    torch.manual_seed(seed)
    if arm == "GRU_8":
        return GRUController()
    return ScalarController(arm)


def derangement(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    identity = np.arange(n)
    while True:
        mapping = rng.permutation(n)
        if np.all(mapping != identity):
            return mapping


def feedback_from_motor(motor: torch.Tensor) -> torch.Tensor:
    return torch.sigmoid(FEEDBACK_SLOPE * motor)


def rollout(model: nn.Module, arm: str, target_np: np.ndarray, obs_np: np.ndarray,
            noise_np: np.ndarray, pulse_np: np.ndarray,
            feedback_drive_np: np.ndarray | None = None) -> tuple[dict[str, np.ndarray], np.ndarray]:
    model.eval()
    target = torch.from_numpy(target_np)
    obs = torch.from_numpy(obs_np)
    noise = torch.from_numpy(noise_np)
    n = len(target_np)
    motors = torch.zeros(n)
    previous_u = torch.zeros(n)
    h = model.initial(n)
    command_history = np.empty((n, T), dtype=np.float64)
    motor_history = np.empty((n, T), dtype=np.float64)
    self_feedback_history = np.empty((n, T), dtype=np.float64)
    feedback_history = torch.zeros((n, 4))  # most recent signal first
    override = torch.from_numpy(feedback_drive_np) if feedback_drive_np is not None else None
    with torch.no_grad():
        for t in range(T):
            motors = MOTOR_RHO * motors + MOTOR_GAIN * previous_u + noise[:, t]
            own_signal = feedback_from_motor(motors)
            if arm == "CROSS_AGENT_YOKED_SENSORY":
                if override is None:
                    raise ValueError("yoked controller requires a donor feedback matrix")
                feedback = override[:, t]
            elif arm == "NO_FEEDBACK":
                feedback = torch.zeros_like(motors)
            elif arm in ("LAG1_SENSORY", "LAG4_SENSORY"):
                lag = 1 if arm == "LAG1_SENSORY" else 4
                feedback = feedback_history[:, lag - 1]
            else:
                feedback = own_signal
            u, h = model.step(obs[:, t], motors, feedback, h)
            feedback_history = torch.cat((own_signal[:, None], feedback_history[:, :-1]), dim=1)
            motor_history[:, t] = motors.numpy()
            command_history[:, t] = u.numpy()
            self_feedback_history[:, t] = own_signal.numpy()
            previous_u = u

    target = target_np.astype(np.float64)
    errors = motor_history - target
    switch_indices = [np.flatnonzero(np.diff(z) != 0) + 1 for z in target]
    latency = np.full(n, np.nan, dtype=np.float64)
    for i, switches in enumerate(switch_indices):
        found = []
        for ix in switches:
            stop = min(T, int(ix) + 24)
            settled = None
            for j in range(int(ix), max(int(ix), stop - 2)):
                if np.all(np.sign(motor_history[i, j:j + 3]) == np.sign(target[i, ix])):
                    settled = j - int(ix)
                    break
            found.append(float(settled if settled is not None else min(24, stop - int(ix))))
        if found:
            latency[i] = float(np.mean(found))
    per_episode = {
        "movement_mse": np.mean(errors ** 2, axis=1),
        "movement_mae": np.mean(np.abs(errors), axis=1),
        "state_accuracy": np.mean(np.sign(motor_history) == np.sign(target), axis=1),
        "command_energy": np.mean(command_history ** 2, axis=1),
        "mean_switch_latency_steps": latency,
        "n_target_switches": np.asarray([len(x) for x in switch_indices], dtype=np.int64),
        "n_sensor_pulse_steps": pulse_np.sum(axis=1).astype(np.int64),
    }
    return per_episode, self_feedback_history


def train_one(arm: str, train_seed: int, donor_model: nn.Module | None = None) -> tuple[nn.Module, dict[str, object]]:
    # Common random starts across the scalar placement/yoke arms isolate routing.
    init_offset = {name: 0 for name in ARMS}
    model = make_model(arm, train_seed + 100_000 + init_offset[arm])
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    fit_start = time.perf_counter()
    final_mse = float("nan")
    model.train()
    for update in range(UPDATES):
        update_seed = train_seed + 500_000 + update * 7_919
        target_np, obs_np, noise_np, pulse_np = make_batch(update_seed, BATCH, TRAIN_HAZARD, TRAIN_PULSE_RATE)
        feedback_drive_np = None
        if arm == "CROSS_AGENT_YOKED_SENSORY":
            if donor_model is None:
                raise ValueError("yoked arm must be trained after self-sensory donor")
            _, donor_signal = rollout(donor_model, "SELF_SENSORY", target_np, obs_np, noise_np, pulse_np)
            mapping = derangement(BATCH, update_seed + 33_333)
            feedback_drive_np = donor_signal[mapping]
        target = torch.from_numpy(target_np)
        obs = torch.from_numpy(obs_np)
        noise = torch.from_numpy(noise_np)
        feedback_drive = torch.from_numpy(feedback_drive_np) if feedback_drive_np is not None else None
        feedback_history = torch.zeros((BATCH, 4))
        motors = torch.zeros(BATCH)
        previous_u = torch.zeros(BATCH)
        h = model.initial(BATCH)
        squared_errors = []
        for t in range(T):
            motors = MOTOR_RHO * motors + MOTOR_GAIN * previous_u + noise[:, t]
            own_signal = feedback_from_motor(motors)
            if arm == "CROSS_AGENT_YOKED_SENSORY":
                feedback = feedback_drive[:, t]
            elif arm == "NO_FEEDBACK":
                feedback = torch.zeros_like(motors)
            elif arm in ("LAG1_SENSORY", "LAG4_SENSORY"):
                lag = 1 if arm == "LAG1_SENSORY" else 4
                feedback = feedback_history[:, lag - 1]
            else:
                feedback = own_signal
            u, h = model.step(obs[:, t], motors, feedback, h)
            feedback_history = torch.cat((own_signal[:, None], feedback_history[:, :-1]), dim=1)
            squared_errors.append((motors - target[:, t]).square())
            previous_u = u
        loss = torch.stack(squared_errors, dim=1).mean()
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        final_mse = float(loss.detach())
    model.eval()
    param_values = [float(x) for p in model.parameters() for x in p.detach().reshape(-1)]
    manifest_row = {
        "seed_block": (train_seed - TRAIN_SEEDS[0]), "training_seed": train_seed, "arm": arm,
        "parameter_count": sum(p.numel() for p in model.parameters()), "updates": UPDATES,
        "batch_size_trajectories": BATCH, "sequence_length": T,
        "final_training_mse": final_mse, "training_seconds": time.perf_counter() - fit_start,
        "trained_with_self_donor_yoke": arm == "CROSS_AGENT_YOKED_SENSORY",
        "learned_parameters": json.dumps(param_values, separators=(",", ":")),
    }
    return model, manifest_row


def bootstrap_mean(values: list[float], seed: int) -> dict[str, float | int]:
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    if not len(v):
        return {"mean": float("nan"), "median": float("nan"), "ci95_low": float("nan"),
                "ci95_high": float("nan"), "n_seed_blocks": 0}
    rng = np.random.default_rng(seed)
    sampled = v[rng.integers(0, len(v), size=(BOOTSTRAPS, len(v)))].mean(axis=1)
    return {"mean": float(v.mean()), "median": float(np.median(v)),
            "ci95_low": float(np.quantile(sampled, .025)), "ci95_high": float(np.quantile(sampled, .975)),
            "n_seed_blocks": int(len(v))}


def run(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    torch.set_num_threads(1)
    random.seed(20261004)
    fit_rows: list[dict[str, object]] = []
    episode_rows: list[dict[str, object]] = []
    feedback_checks = []
    start_all = time.time()

    for block, train_seed in zip(BLOCKS, TRAIN_SEEDS):
        print(f"training seed block {block + 1}/{len(BLOCKS)}", flush=True)
        models: dict[str, nn.Module] = {}
        model, fit_row = train_one("SELF_SENSORY", train_seed)
        models["SELF_SENSORY"] = model
        fit_rows.append(fit_row)
        model, fit_row = train_one("CROSS_AGENT_YOKED_SENSORY", train_seed, models["SELF_SENSORY"])
        models["CROSS_AGENT_YOKED_SENSORY"] = model
        fit_rows.append(fit_row)
        for arm in ("LAG1_SENSORY", "LAG4_SENSORY", "SELF_OUTPUT", "NO_FEEDBACK", "GENERIC_RNN_1D", "GRU_8"):
            model, fit_row = train_one(arm, train_seed)
            models[arm] = model
            fit_rows.append(fit_row)

        for condition_index, (condition, cfg) in enumerate(CONDITIONS.items()):
            test_seed = 9_000_000 + block * 100_000 + condition_index * 1_000
            z, y, motor_noise, pulse = make_batch(test_seed, N_TEST, cfg["hazard"], cfg["pulse_rate"])
            self_metrics, self_drive = rollout(models["SELF_SENSORY"], "SELF_SENSORY", z, y, motor_noise, pulse)
            mapping = derangement(N_TEST, test_seed + 44_444)
            yoke_drive = self_drive[mapping]
            exact_distribution = np.array_equal(np.sort(self_drive, axis=0), np.sort(yoke_drive, axis=0))
            if not exact_distribution:
                raise AssertionError("cross-agent yoke failed exact per-time population distribution check")
            feedback_checks.append({"seed_block": block, "condition": condition,
                                   "donor_mapping_has_no_fixed_points": bool(np.all(mapping != np.arange(N_TEST))),
                                   "exact_instantaneous_population_distribution_match": exact_distribution,
                                   "max_sorted_feedback_difference": float(np.max(np.abs(np.sort(self_drive, axis=0) - np.sort(yoke_drive, axis=0)))),
                                   "self_sorted_feedback_sha256_by_step": [sha256_bytes(np.sort(self_drive[:, t]).astype("<f8").tobytes()) for t in range(T)],
                                   "yoke_sorted_feedback_sha256_by_step": [sha256_bytes(np.sort(yoke_drive[:, t]).astype("<f8").tobytes()) for t in range(T)]})

            results = {"SELF_SENSORY": self_metrics}
            results["CROSS_AGENT_YOKED_SENSORY"], _ = rollout(
                models["CROSS_AGENT_YOKED_SENSORY"], "CROSS_AGENT_YOKED_SENSORY", z, y, motor_noise, pulse, yoke_drive)
            for arm in ("LAG1_SENSORY", "LAG4_SENSORY", "SELF_OUTPUT", "NO_FEEDBACK", "GENERIC_RNN_1D", "GRU_8"):
                results[arm], _ = rollout(models[arm], arm, z, y, motor_noise, pulse)
            for arm in ARMS:
                for episode in range(N_TEST):
                    row = {"seed_block": block, "training_seed": train_seed, "condition": condition,
                           "evaluation_batch_seed": test_seed, "episode_id": episode, "arm": arm,
                           "yoke_donor_episode_id": int(mapping[episode]) if arm == "CROSS_AGENT_YOKED_SENSORY" else "",
                           "n_sensor_pulse_steps": int(results[arm]["n_sensor_pulse_steps"][episode]),
                           "n_target_switches": int(results[arm]["n_target_switches"][episode])}
                    row.update({metric: float(results[arm][metric][episode]) for metric in METRICS})
                    episode_rows.append(row)

    write_csv(out / "fit_manifest.csv", fit_rows)
    write_csv(out / "test_episode_metrics.csv", episode_rows)
    (out / "feedback_distribution_check.json").write_text(json.dumps({"checks": feedback_checks}, indent=2) + "\n")

    grouped: dict[tuple[int, str, str], list[dict[str, object]]] = {}
    for row in episode_rows:
        grouped.setdefault((int(row["seed_block"]), str(row["arm"]), str(row["condition"])), []).append(row)
    seed_rows = []
    for (block, arm, condition), rows in sorted(grouped.items()):
        seed_rows.append({"seed_block": block, "arm": arm, "condition": condition,
                          "n_episodes": len(rows), **{m: float(np.nanmean([float(r[m]) for r in rows])) for m in METRICS}})
    write_csv(out / "test_seed_summary.csv", seed_rows)

    primary = []
    for block in BLOCKS:
        self_row = next(r for r in seed_rows if r["seed_block"] == block and r["arm"] == "SELF_SENSORY" and r["condition"] == "SLOW_TRANSIENT")
        lag_row = next(r for r in seed_rows if r["seed_block"] == block and r["arm"] == "LAG4_SENSORY" and r["condition"] == "SLOW_TRANSIENT")
        primary.append({"seed_block": block, "lag4_minus_self_movement_mse": float(lag_row["movement_mse"]) - float(self_row["movement_mse"])})
    primary_summary = bootstrap_mean([r["lag4_minus_self_movement_mse"] for r in primary], PRIMARY_BOOTSTRAP_SEED)

    metric_summary = {}
    for ci, condition in enumerate(CONDITIONS):
        metric_summary[condition] = {}
        for ai, arm in enumerate(ARMS):
            seed_level = [r for r in seed_rows if r["condition"] == condition and r["arm"] == arm]
            metric_summary[condition][arm] = {}
            for mi, metric in enumerate(METRICS):
                metric_summary[condition][arm][metric] = bootstrap_mean(
                    [float(r[metric]) for r in seed_level], 8_800_000 + ci * 1000 + ai * 100 + mi)

    summary = {
        "experiment": NAME,
        "classification": "exploratory, outcome-informed artificial transfer; temporal-lag contrast frozen before execution",
        "training_seed_blocks": len(BLOCKS), "fit_records": len(fit_rows),
        "test_episode_rows": len(episode_rows), "test_seed_summary_rows": len(seed_rows),
        "primary_condition": "SLOW_TRANSIENT", "primary_metric": "movement_mse",
        "primary_contrast": "LAG4_SENSORY minus SELF_SENSORY; positive favors current feedback alignment",
        "primary_seed_block_values": primary, "primary_contrast_summary": primary_summary,
        "primary_distribution_match_checks_passed": bool(all(x["exact_instantaneous_population_distribution_match"] for x in feedback_checks)),
        "metric_summary": metric_summary,
        "scope": "binary target tracking with transient sensor conflicts; synthetic only; feedback latency is an artificial perturbation, not a measured biological conduction delay",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    output_hashes = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
                     for p in sorted(out.iterdir()) if p.is_file()}
    manifest = {
        "experiment": NAME, "contract_sha256": sha256(CONTRACT),
        "runner_sha256": sha256(Path(__file__)),
        "verifier_sha256": sha256(ROOT / "model" / NAME / "verify_results.py"),
        "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
        "device": "CPU", "torch_threads": 1, "training_seeds": TRAIN_SEEDS,
        "test_batch_size": N_TEST, "test_seed_rule": "9000000 + block*100000 + condition_index*1000",
        "conditions": CONDITIONS, "arms": ARMS, "parameter_counts": PARAMS,
        "updates": UPDATES, "batch_size": BATCH, "sequence_length": T,
        "bootstrap_resamples": BOOTSTRAPS, "primary_bootstrap_seed": PRIMARY_BOOTSTRAP_SEED,
        "duration_seconds": time.time() - start_all, "outputs": output_hashes,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": "COMPLETE", "experiment": NAME,
                      "primary": primary_summary, "yoke_distribution_match": summary["primary_distribution_match_checks_passed"],
                      "test_episode_rows": len(episode_rows)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
