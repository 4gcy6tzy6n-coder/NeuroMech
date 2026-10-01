#!/usr/bin/env python3
"""Test realized motor-state feedback in continuous 2D target tracking."""
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
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_CONTINUOUS_TRACKING_MOTOR_STATE_TRANSFER_V1"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
ARMS = ("GRU_SELF_MOTOR", "GRU_ZERO_MOTOR", "GRU_ACTION_COPY", "GRU_YOKED_MOTOR")
BLOCKS = tuple(range(32))
TRAIN_SEEDS = tuple(850_000 + i for i in BLOCKS)
T = 64
BATCH = 32
UPDATES = 100
N_TEST = 128
LR = 0.003
MOTOR_RHO = 0.65
MOTOR_GAIN = 1.0 - MOTOR_RHO
MOTOR_SD = 0.035
OBS_SD = 0.16
TARGET_VELOCITY_SD = 0.075
BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 8_765_501
PROFILES = {
    "TRAIN_LIKE": {"alpha": 0.91, "missing_fraction": 0.50, "mean_missing_burst": 4.0},
    "LONG_MISSING_BURSTS": {"alpha": 0.91, "missing_fraction": 0.50, "mean_missing_burst": 8.0},
    "LOW_MISSING": {"alpha": 0.91, "missing_fraction": 0.25, "mean_missing_burst": 4.0},
    "FAST_TARGET": {"alpha": 0.76, "missing_fraction": 0.50, "mean_missing_burst": 4.0},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_batch(seed: int, n: int, alpha: float | None, missing_fraction: float,
               mean_missing_burst: float) -> tuple[np.ndarray, ...]:
    rng = np.random.default_rng(seed)
    if alpha is None:
        alphas = rng.uniform(0.84, 0.97, size=n)
    else:
        alphas = np.full(n, alpha)
    target = np.zeros((n, T, 2), dtype=np.float32)
    target[:, 0] = rng.uniform(-1.0, 1.0, size=(n, 2))
    velocity = rng.normal(0.0, TARGET_VELOCITY_SD, size=(n, 2))
    for t in range(1, T):
        velocity = alphas[:, None] * velocity + rng.normal(0.0, TARGET_VELOCITY_SD, size=(n, 2))
        target[:, t] = target[:, t - 1] + velocity

    measurement_noise = rng.normal(0.0, OBS_SD, size=(n, T, 2)).astype(np.float32)
    motor_noise = rng.normal(0.0, MOTOR_SD, size=(n, T, 2)).astype(np.float32)
    available = np.ones((n, T), dtype=bool)
    if missing_fraction > 0:
        p_leave_missing = min(1.0, 1.0 / mean_missing_burst)
        p_enter_missing = min(1.0, missing_fraction / (1.0 - missing_fraction) * p_leave_missing)
        missing = rng.random(n) < missing_fraction
        for t in range(T):
            if t:
                u = rng.random(n)
                missing = np.where(missing, u >= p_leave_missing, u < p_enter_missing)
            available[:, t] = ~missing
    return target, measurement_noise, motor_noise, available


class Controller(nn.Module):
    def __init__(self):
        super().__init__()
        self.cell = nn.GRUCell(5, 8)
        self.readout = nn.Linear(8, 2)

    def initial(self, n: int) -> torch.Tensor:
        return torch.zeros(n, 8)

    def step(self, x: torch.Tensor, h: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.cell(x, h)
        return torch.tanh(self.readout(h)), h


def make_model(seed: int) -> Controller:
    torch.manual_seed(seed)
    return Controller()


def derangement(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    identity = np.arange(n)
    while True:
        mapping = rng.permutation(n)
        if np.all(mapping != identity):
            return mapping


def rollout(model: Controller, arm: str, target_np: np.ndarray, measurement_noise_np: np.ndarray,
            motor_noise_np: np.ndarray, available_np: np.ndarray,
            yoke_drive_np: np.ndarray | None = None) -> tuple[dict[str, np.ndarray], np.ndarray]:
    target = torch.from_numpy(target_np)
    measurement_noise = torch.from_numpy(measurement_noise_np)
    motor_noise = torch.from_numpy(motor_noise_np)
    available = torch.from_numpy(available_np)
    n = len(target_np)
    position = torch.zeros(n, 2)
    velocity = torch.zeros(n, 2)
    previous_command = torch.zeros(n, 2)
    h = model.initial(n)
    yoke = torch.from_numpy(yoke_drive_np) if yoke_drive_np is not None else None
    squared_distance = np.empty((n, T), dtype=np.float64)
    action_energy = np.empty((n, T), dtype=np.float64)
    motor_history = np.empty((n, T, 2), dtype=np.float32)
    model.eval()
    with torch.no_grad():
        for t in range(T):
            velocity = MOTOR_RHO * velocity + MOTOR_GAIN * previous_command + motor_noise[:, t]
            position = position + velocity
            relative = target[:, t] - position
            is_available = available[:, t]
            observation = relative + measurement_noise[:, t]
            observation = torch.where(is_available[:, None], observation, torch.zeros_like(observation))
            if arm == "GRU_SELF_MOTOR":
                feedback = velocity
            elif arm == "GRU_ZERO_MOTOR":
                feedback = torch.zeros_like(velocity)
            elif arm == "GRU_ACTION_COPY":
                feedback = previous_command
            elif arm == "GRU_YOKED_MOTOR":
                if yoke is None:
                    raise ValueError("yoked arm requires donor motor-state traces")
                feedback = yoke[:, t]
            else:
                raise ValueError(f"unknown arm: {arm}")
            x = torch.cat((observation, is_available[:, None].float(), feedback), dim=-1)
            command, h = model.step(x, h)
            squared_distance[:, t] = relative.square().mean(dim=-1).numpy()
            action_energy[:, t] = command.square().mean(dim=-1).numpy()
            motor_history[:, t] = velocity.numpy()
            previous_command = command
    metrics = {"tracking_mse": squared_distance.mean(axis=1),
               "tracking_rmse": np.sqrt(squared_distance.mean(axis=1)),
               "command_energy": action_energy.mean(axis=1),
               "missing_fraction": 1.0 - available_np.mean(axis=1)}
    return metrics, motor_history


def train_one(arm: str, seed: int, donor: Controller | None = None) -> tuple[Controller, dict[str, object]]:
    model = make_model(seed + 100_000)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    started = time.perf_counter()
    loss_value = float("nan")
    for update in range(UPDATES):
        batch_seed = seed + 500_000 + update * 7_919
        target_np, measurement_noise_np, motor_noise_np, available_np = make_batch(
            batch_seed, BATCH, None, 0.50, 4.0)
        donor_drive = None
        if arm == "GRU_YOKED_MOTOR":
            if donor is None:
                raise ValueError("yoked training requires the fitted self-motor donor")
            _, donor_drive = rollout(donor, "GRU_SELF_MOTOR", target_np, measurement_noise_np,
                                     motor_noise_np, available_np)
            donor_drive = donor_drive[derangement(BATCH, batch_seed + 33_333)]

        target = torch.from_numpy(target_np)
        measurement_noise = torch.from_numpy(measurement_noise_np)
        motor_noise = torch.from_numpy(motor_noise_np)
        available = torch.from_numpy(available_np)
        donor_t = torch.from_numpy(donor_drive) if donor_drive is not None else None
        position = torch.zeros(BATCH, 2)
        velocity = torch.zeros(BATCH, 2)
        previous_command = torch.zeros(BATCH, 2)
        h = model.initial(BATCH)
        losses = []
        for t in range(T):
            velocity = MOTOR_RHO * velocity + MOTOR_GAIN * previous_command + motor_noise[:, t]
            position = position + velocity
            relative = target[:, t] - position
            is_available = available[:, t]
            observation = relative + measurement_noise[:, t]
            observation = torch.where(is_available[:, None], observation, torch.zeros_like(observation))
            if arm == "GRU_SELF_MOTOR":
                feedback = velocity
            elif arm == "GRU_ZERO_MOTOR":
                feedback = torch.zeros_like(velocity)
            elif arm == "GRU_ACTION_COPY":
                feedback = previous_command
            elif arm == "GRU_YOKED_MOTOR":
                feedback = donor_t[:, t]
            x = torch.cat((observation, is_available[:, None].float(), feedback), dim=-1)
            command, h = model.step(x, h)
            losses.append(relative.square().mean(dim=-1) + 0.002 * command.square().mean(dim=-1))
            previous_command = command
        loss = torch.stack(losses, dim=1).mean()
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        loss_value = float(loss.detach())

    params = [float(x) for p in model.parameters() for x in p.detach().reshape(-1)]
    row = {"seed_block": seed - TRAIN_SEEDS[0], "training_seed": seed, "arm": arm,
           "parameter_count": sum(p.numel() for p in model.parameters()), "updates": UPDATES,
           "batch_size_trajectories": BATCH, "sequence_length": T,
           "final_training_loss": loss_value, "training_seconds": time.perf_counter() - started,
           "learned_parameters": json.dumps(params, separators=(",", ":"))}
    return model.eval(), row


def bootstrap(values: list[float]) -> dict[str, float | int]:
    x = np.asarray(values, dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    sample = x[rng.integers(0, len(x), size=(BOOTSTRAPS, len(x)))].mean(axis=1)
    return {"mean": float(x.mean()), "median": float(np.median(x)),
            "ci95_low": float(np.quantile(sample, .025)), "ci95_high": float(np.quantile(sample, .975)),
            "n_seed_blocks": int(len(x))}


def run(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    torch.set_num_threads(1)
    fit_rows: list[dict[str, object]] = []
    episode_rows: list[dict[str, object]] = []
    yoke_checks = []
    started = time.time()

    for block, seed in zip(BLOCKS, TRAIN_SEEDS):
        print(f"training seed block {block + 1}/{len(BLOCKS)}", flush=True)
        self_model, row = train_one("GRU_SELF_MOTOR", seed)
        fit_rows.append(row)
        zero_model, row = train_one("GRU_ZERO_MOTOR", seed)
        fit_rows.append(row)
        action_model, row = train_one("GRU_ACTION_COPY", seed)
        fit_rows.append(row)
        yoke_model, row = train_one("GRU_YOKED_MOTOR", seed, donor=self_model)
        fit_rows.append(row)
        models = {"GRU_SELF_MOTOR": self_model, "GRU_ZERO_MOTOR": zero_model,
                  "GRU_ACTION_COPY": action_model, "GRU_YOKED_MOTOR": yoke_model}

        for ci, (profile, cfg) in enumerate(PROFILES.items()):
            test_seed = 20_000_000 + block * 100_000 + ci * 1_000
            target, measurement_noise, motor_noise, available = make_batch(
                test_seed, N_TEST, cfg["alpha"], cfg["missing_fraction"], cfg["mean_missing_burst"])
            _, self_drive = rollout(self_model, "GRU_SELF_MOTOR", target, measurement_noise, motor_noise, available)
            mapping = derangement(N_TEST, test_seed + 44_444)
            yoke_drive = self_drive[mapping]
            yoke_match = np.array_equal(np.sort(self_drive, axis=0), np.sort(yoke_drive, axis=0))
            if not yoke_match:
                raise AssertionError("yoke signal failed exact population-distribution match")
            yoke_checks.append({"seed_block": block, "profile": profile,
                                "no_fixed_points": bool(np.all(mapping != np.arange(N_TEST))),
                                "exact_per_time_per_coordinate_match": bool(yoke_match),
                                "max_sorted_difference": float(np.max(np.abs(np.sort(self_drive, axis=0) - np.sort(yoke_drive, axis=0))))})

            metrics = {
                "GRU_SELF_MOTOR": rollout(self_model, "GRU_SELF_MOTOR", target, measurement_noise, motor_noise, available)[0],
                "GRU_ZERO_MOTOR": rollout(zero_model, "GRU_ZERO_MOTOR", target, measurement_noise, motor_noise, available)[0],
                "GRU_ACTION_COPY": rollout(action_model, "GRU_ACTION_COPY", target, measurement_noise, motor_noise, available)[0],
                "GRU_YOKED_MOTOR": rollout(yoke_model, "GRU_YOKED_MOTOR", target, measurement_noise, motor_noise, available, yoke_drive)[0],
            }
            for arm, values in metrics.items():
                for episode in range(N_TEST):
                    episode_rows.append({"seed_block": block, "training_seed": seed, "profile": profile,
                                         "evaluation_seed": test_seed, "episode_id": episode, "arm": arm,
                                         "yoke_donor_episode_id": int(mapping[episode]) if arm == "GRU_YOKED_MOTOR" else "",
                                         "tracking_mse": float(values["tracking_mse"][episode]),
                                         "tracking_rmse": float(values["tracking_rmse"][episode]),
                                         "command_energy": float(values["command_energy"][episode]),
                                         "missing_fraction": float(values["missing_fraction"][episode])})

    write_csv(out / "fit_manifest.csv", fit_rows)
    write_csv(out / "episode_metrics.csv", episode_rows)
    (out / "yoke_distribution_check.json").write_text(json.dumps({"checks": yoke_checks}, indent=2) + "\n")

    seed_rows = []
    for block in BLOCKS:
        for profile in PROFILES:
            for arm in ARMS:
                rows = [r for r in episode_rows if r["seed_block"] == block and r["profile"] == profile and r["arm"] == arm]
                seed_rows.append({"seed_block": block, "profile": profile, "arm": arm,
                                  "n_episodes": len(rows),
                                  **{m: float(np.mean([r[m] for r in rows])) for m in ("tracking_mse", "tracking_rmse", "command_energy", "missing_fraction")}})
    write_csv(out / "seed_summary.csv", seed_rows)

    def val(block: int, arm: str, profile: str, metric: str = "tracking_mse") -> float:
        row = next(r for r in seed_rows if r["seed_block"] == block and r["arm"] == arm and r["profile"] == profile)
        return float(row[metric])

    primary_values = [val(b, "GRU_SELF_MOTOR", "LONG_MISSING_BURSTS") -
                      val(b, "GRU_ACTION_COPY", "LONG_MISSING_BURSTS") for b in BLOCKS]
    secondary_zero = [val(b, "GRU_SELF_MOTOR", "LONG_MISSING_BURSTS") -
                      val(b, "GRU_ZERO_MOTOR", "LONG_MISSING_BURSTS") for b in BLOCKS]
    secondary_yoke = [val(b, "GRU_SELF_MOTOR", "LONG_MISSING_BURSTS") -
                      val(b, "GRU_YOKED_MOTOR", "LONG_MISSING_BURSTS") for b in BLOCKS]
    summary = {"experiment": NAME, "classification": "exploratory artificial transfer; new continuous 2D task family",
               "training_seed_blocks": len(BLOCKS), "fit_records": len(fit_rows),
               "episode_rows": len(episode_rows), "seed_summary_rows": len(seed_rows),
               "parameter_count_per_arm": 378, "primary_profile": "LONG_MISSING_BURSTS",
               "primary_contrast": "GRU_SELF_MOTOR minus GRU_ACTION_COPY; negative favors realized motor state",
               "primary_seed_block_values": primary_values, "primary_contrast_summary": bootstrap(primary_values),
               "secondary_self_minus_zero": secondary_zero,
               "secondary_self_minus_zero_summary": bootstrap(secondary_zero),
               "secondary_self_minus_yoke": secondary_yoke,
               "secondary_self_minus_yoke_summary": bootstrap(secondary_yoke),
               "mean_mse_by_profile_arm": {p: {a: float(np.mean([val(b, a, p) for b in BLOCKS])) for a in ARMS} for p in PROFILES},
               "yoke_checks_passed": all(r["exact_per_time_per_coordinate_match"] for r in yoke_checks),
               "scope": "synthetic continuous 2D target tracking; realized motor-state channel only; no biological or general AI claim"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")

    files = ("fit_manifest.csv", "episode_metrics.csv", "seed_summary.csv", "yoke_distribution_check.json", "summary.json")
    manifest = {"experiment": NAME, "contract_sha256": sha256(CONTRACT),
                "runner_sha256": sha256(Path(__file__)),
                "verifier_sha256": sha256(ROOT / "model" / NAME / "verify_results.py"),
                "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
                "device": "CPU", "torch_threads": 1, "training_seeds": TRAIN_SEEDS,
                "arms": ARMS, "parameters_per_arm": 378, "updates": UPDATES,
                "batch_size": BATCH, "sequence_length": T, "profiles": PROFILES,
                "test_seed_rule": "20000000 + block*100000 + profile_index*1000",
                "bootstrap_resamples": BOOTSTRAPS, "bootstrap_seed": BOOTSTRAP_SEED,
                "duration_seconds": time.time() - started,
                "outputs": {f: {"bytes": (out / f).stat().st_size, "sha256": sha256(out / f)} for f in files}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": "COMPLETE", "primary": summary["primary_contrast_summary"],
                      "self_minus_zero": summary["secondary_self_minus_zero_summary"],
                      "self_minus_yoke": summary["secondary_self_minus_yoke_summary"],
                      "episode_rows": len(episode_rows)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/results" / NAME / "canonical")
    run(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
