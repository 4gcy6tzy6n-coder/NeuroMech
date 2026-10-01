#!/usr/bin/env python3
"""Ablate motor-state input from an otherwise identical GRU controller."""
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

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "M2_FEEDBACK_TEMPORAL_ALIGNMENT_V1"))
import run_experiment as task  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_GRU_MOTOR_FEEDBACK_ABLATION_V1"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
ARMS = ("GRU_SELF_MOTOR", "GRU_ZERO_MOTOR", "GRU_YOKED_MOTOR")
BLOCKS = tuple(range(32))
TRAIN_SEEDS = tuple(840_000 + i for i in BLOCKS)
N_TEST = 128
T = task.T
METRICS = task.METRICS
BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 8_765_440


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


class FeedbackGRU(nn.Module):
    def __init__(self, use_motor: bool):
        super().__init__()
        self.use_motor = use_motor
        self.cell = nn.GRUCell(2, 8)
        self.readout = nn.Linear(8, 1)

    def initial(self, n: int) -> torch.Tensor:
        return torch.zeros(n, 8)

    def step(self, y: torch.Tensor, own_motor: torch.Tensor, feedback: torch.Tensor,
             h: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if not self.use_motor:
            feedback = torch.zeros_like(feedback)
        h = self.cell(torch.stack((y, feedback), dim=-1), h)
        return torch.tanh(self.readout(h).squeeze(-1)), h


def make_model(use_motor: bool, seed: int) -> FeedbackGRU:
    torch.manual_seed(seed)
    return FeedbackGRU(use_motor)


def derangement(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    identity = np.arange(n)
    while True:
        mapping = rng.permutation(n)
        if np.all(mapping != identity):
            return mapping


def train_one(arm: str, train_seed: int, donor: FeedbackGRU | None = None) -> tuple[FeedbackGRU, dict[str, object]]:
    use_motor = arm != "GRU_ZERO_MOTOR"
    model = make_model(use_motor, train_seed + 100_000)
    optimizer = torch.optim.Adam(model.parameters(), lr=task.LR)
    fit_start = time.perf_counter()
    for update in range(task.UPDATES):
        update_seed = train_seed + 500_000 + update * 7_919
        target_np, obs_np, noise_np, pulse_np = task.make_batch(
            update_seed, task.BATCH, task.TRAIN_HAZARD, task.TRAIN_PULSE_RATE)
        donor_drive = None
        if arm == "GRU_YOKED_MOTOR":
            if donor is None:
                raise ValueError("yoked arm requires the fitted self-motor donor")
            _, donor_drive = task.rollout(donor, "SELF_SENSORY", target_np, obs_np, noise_np, pulse_np)
            donor_drive = donor_drive[derangement(task.BATCH, update_seed + 33_333)].astype(np.float32)

        target_t = torch.from_numpy(target_np)
        obs_t = torch.from_numpy(obs_np)
        noise_t = torch.from_numpy(noise_np)
        donor_t = torch.from_numpy(donor_drive) if donor_drive is not None else None
        motors = torch.zeros(task.BATCH)
        previous_u = torch.zeros(task.BATCH)
        h = model.initial(task.BATCH)
        squared_errors = []
        for t in range(T):
            motors = task.MOTOR_RHO * motors + task.MOTOR_GAIN * previous_u + noise_t[:, t]
            own_signal = task.feedback_from_motor(motors)
            if arm == "GRU_ZERO_MOTOR":
                feedback = torch.zeros_like(own_signal)
            elif arm == "GRU_YOKED_MOTOR":
                feedback = donor_t[:, t]
            else:
                feedback = own_signal
            u, h = model.step(obs_t[:, t], motors, feedback, h)
            squared_errors.append((motors - target_t[:, t]).square())
            previous_u = u
        loss = torch.stack(squared_errors, dim=1).mean()
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()

    row = {"seed_block": train_seed - TRAIN_SEEDS[0], "training_seed": train_seed,
           "arm": arm, "parameter_count": sum(p.numel() for p in model.parameters()),
           "updates": task.UPDATES, "batch_size_trajectories": task.BATCH,
           "sequence_length": T, "final_training_mse": float(loss.detach()),
           "training_seconds": time.perf_counter() - fit_start,
           "learned_parameters": json.dumps([float(x) for p in model.parameters() for x in p.detach().reshape(-1)], separators=(",", ":"))}
    return model.eval(), row


def bootstrap(values: list[float]) -> dict[str, float | int]:
    x = np.asarray(values, dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    sampled = x[rng.integers(0, len(x), size=(BOOTSTRAPS, len(x)))].mean(axis=1)
    return {"mean": float(x.mean()), "median": float(np.median(x)),
            "ci95_low": float(np.quantile(sampled, .025)),
            "ci95_high": float(np.quantile(sampled, .975)), "n_seed_blocks": int(len(x))}


def run(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    torch.set_num_threads(1)
    fit_rows: list[dict[str, object]] = []
    episode_rows: list[dict[str, object]] = []
    yoke_checks = []
    start = time.time()

    for block, train_seed in zip(BLOCKS, TRAIN_SEEDS):
        print(f"training seed block {block + 1}/{len(BLOCKS)}", flush=True)
        self_model, fit = train_one("GRU_SELF_MOTOR", train_seed)
        fit_rows.append(fit)
        zero_model, fit = train_one("GRU_ZERO_MOTOR", train_seed)
        fit_rows.append(fit)
        yoke_model, fit = train_one("GRU_YOKED_MOTOR", train_seed, donor=self_model)
        fit_rows.append(fit)
        models = {"GRU_SELF_MOTOR": self_model, "GRU_ZERO_MOTOR": zero_model, "GRU_YOKED_MOTOR": yoke_model}

        for ci, (condition, cfg) in enumerate(task.CONDITIONS.items()):
            test_seed = 10_000_000 + block * 100_000 + ci * 1_000
            target, obs, noise, pulse = task.make_batch(test_seed, N_TEST, cfg["hazard"], cfg["pulse_rate"])
            _, own_drive = task.rollout(self_model, "SELF_SENSORY", target, obs, noise, pulse)
            own_drive = own_drive.astype(np.float32)
            mapping = derangement(N_TEST, test_seed + 44_444)
            yoke_drive = own_drive[mapping]
            match = np.array_equal(np.sort(own_drive, axis=0), np.sort(yoke_drive, axis=0))
            if not match:
                raise AssertionError("yoked motor-signal distribution does not match")
            yoke_checks.append({"seed_block": block, "condition": condition,
                                "no_fixed_points": bool(np.all(mapping != np.arange(N_TEST))),
                                "exact_per_time_population_match": bool(match),
                                "max_sorted_difference": float(np.max(np.abs(np.sort(own_drive, axis=0) - np.sort(yoke_drive, axis=0))))})

            arm_metrics = {
                "GRU_SELF_MOTOR": task.rollout(self_model, "SELF_SENSORY", target, obs, noise, pulse)[0],
                "GRU_ZERO_MOTOR": task.rollout(zero_model, "NO_FEEDBACK", target, obs, noise, pulse)[0],
                "GRU_YOKED_MOTOR": task.rollout(yoke_model, "CROSS_AGENT_YOKED_SENSORY", target, obs, noise, pulse, yoke_drive)[0],
            }
            for arm, metrics in arm_metrics.items():
                for episode in range(N_TEST):
                    row = {"seed_block": block, "training_seed": train_seed, "condition": condition,
                           "evaluation_batch_seed": test_seed, "episode_id": episode, "arm": arm,
                           "yoke_donor_episode_id": int(mapping[episode]) if arm == "GRU_YOKED_MOTOR" else "",
                           "n_sensor_pulse_steps": int(metrics["n_sensor_pulse_steps"][episode]),
                           "n_target_switches": int(metrics["n_target_switches"][episode])}
                    row.update({m: float(metrics[m][episode]) for m in METRICS})
                    episode_rows.append(row)

    write_csv(out / "fit_manifest.csv", fit_rows)
    write_csv(out / "test_episode_metrics.csv", episode_rows)
    (out / "yoke_distribution_check.json").write_text(json.dumps({"checks": yoke_checks}, indent=2) + "\n")

    seed_rows = []
    for block in BLOCKS:
        for condition in task.CONDITIONS:
            for arm in ARMS:
                rows = [r for r in episode_rows if r["seed_block"] == block and r["condition"] == condition and r["arm"] == arm]
                seed_rows.append({"seed_block": block, "condition": condition, "arm": arm, "n_episodes": len(rows),
                                  **{m: float(np.nanmean([r[m] for r in rows])) for m in METRICS}})
    write_csv(out / "test_seed_summary.csv", seed_rows)

    def lookup(block: int, arm: str, condition: str, metric: str) -> float:
        row = next(r for r in seed_rows if r["seed_block"] == block and r["arm"] == arm and r["condition"] == condition)
        return float(row[metric])

    primary = [lookup(b, "GRU_SELF_MOTOR", "SLOW_TRANSIENT", "movement_mse") -
               lookup(b, "GRU_ZERO_MOTOR", "SLOW_TRANSIENT", "movement_mse") for b in BLOCKS]
    secondary = [lookup(b, "GRU_SELF_MOTOR", "SLOW_TRANSIENT", "movement_mse") -
                 lookup(b, "GRU_YOKED_MOTOR", "SLOW_TRANSIENT", "movement_mse") for b in BLOCKS]
    summary = {"experiment": NAME, "classification": "post-result exploratory mechanistic attribution; reused M2 task family",
               "training_seed_blocks": len(BLOCKS), "fit_records": len(fit_rows),
               "test_episode_rows": len(episode_rows), "test_seed_summary_rows": len(seed_rows),
               "primary_condition": "SLOW_TRANSIENT", "primary_contrast": "GRU_SELF_MOTOR minus GRU_ZERO_MOTOR; negative favors motor input",
               "primary_seed_block_values": primary, "primary_contrast_summary": bootstrap(primary),
               "secondary_contrast": "GRU_SELF_MOTOR minus GRU_YOKED_MOTOR; negative favors self-contingency",
               "secondary_seed_block_values": secondary, "secondary_contrast_summary": bootstrap(secondary),
               "mean_movement_mse_by_condition_arm": {
                   c: {a: float(np.mean([lookup(b, a, c, "movement_mse") for b in BLOCKS])) for a in ARMS}
                   for c in task.CONDITIONS},
               "yoke_checks_passed": all(r["exact_per_time_population_match"] for r in yoke_checks),
               "scope": "M2 target tracking with transient sensor conflict; motor-input ablation only; artificial, not biological validation"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")

    files = ("fit_manifest.csv", "test_episode_metrics.csv", "test_seed_summary.csv", "yoke_distribution_check.json", "summary.json")
    manifest = {"experiment": NAME, "contract_sha256": sha256(CONTRACT), "runner_sha256": sha256(Path(__file__)),
                "task_source_sha256": sha256(Path(task.__file__)), "python": platform.python_version(),
                "numpy": np.__version__, "torch": torch.__version__, "device": "CPU", "torch_threads": 1,
                "training_seeds": TRAIN_SEEDS, "arms": ARMS, "parameter_count_each": 297,
                "updates": task.UPDATES, "batch_size": task.BATCH, "sequence_length": T,
                "conditions": task.CONDITIONS, "test_seed_rule": "10000000 + block*100000 + condition_index*1000",
                "bootstrap_resamples": BOOTSTRAPS, "bootstrap_seed": BOOTSTRAP_SEED,
                "duration_seconds": time.time() - start,
                "outputs": {f: {"bytes": (out / f).stat().st_size, "sha256": sha256(out / f)} for f in files}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": "COMPLETE", "primary": summary["primary_contrast_summary"],
                      "secondary": summary["secondary_contrast_summary"], "rows": len(episode_rows)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/results" / NAME / "canonical")
    run(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
