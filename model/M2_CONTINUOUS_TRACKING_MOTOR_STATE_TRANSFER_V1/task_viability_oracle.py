#!/usr/bin/env python3
"""Post-run task-viability diagnostic using privileged target state."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_experiment as task  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    profiles = {}
    for ci, (name, cfg) in enumerate(task.PROFILES.items()):
        block_means = []
        reactive_means = []
        for block in task.BLOCKS:
            seed = 20_000_000 + block * 100_000 + ci * 1_000
            target, measurement_noise, motor_noise, available = task.make_batch(
                seed, task.N_TEST, cfg["alpha"], cfg["missing_fraction"], cfg["mean_missing_burst"])
            n = len(target)
            position = np.zeros((n, 2))
            velocity = np.zeros((n, 2))
            command = np.zeros((n, 2))
            errors = []
            for t in range(task.T):
                velocity = task.MOTOR_RHO * velocity + task.MOTOR_GAIN * command + motor_noise[:, t]
                position += velocity
                relative = target[:, t] - position
                errors.append(np.mean(relative ** 2, axis=1))
                target_velocity = target[:, t] - target[:, t - 1] if t else np.zeros((n, 2))
                # Privileged upper-bound controller: it sees the exact target-relative
                # position and current target velocity, bypassing the noisy/missing sensor.
                command = np.clip((relative + target_velocity - task.MOTOR_RHO * velocity) /
                                  task.MOTOR_GAIN, -1.0, 1.0)
            block_means.append(float(np.mean(np.mean(errors, axis=0))))
            # Post-run fixed proportional baseline: command toward the currently
            # observed relative target, and issue zero command while observations
            # are absent. This is a simple diagnostic, not a tuned benchmark arm.
            position = np.zeros((n, 2))
            velocity = np.zeros((n, 2))
            command = np.zeros((n, 2))
            errors = []
            for t in range(task.T):
                velocity = task.MOTOR_RHO * velocity + task.MOTOR_GAIN * command + motor_noise[:, t]
                position += velocity
                relative = target[:, t] - position
                observed = relative + measurement_noise[:, t]
                observed = np.where(available[:, t, None], observed, 0.0)
                errors.append(np.mean(relative ** 2, axis=1))
                command = np.clip(observed, -1.0, 1.0)
            reactive_means.append(float(np.mean(np.mean(errors, axis=0))))
        profiles[name] = {"mean_tracking_mse": float(np.mean(block_means)),
                          "training_seed_blocks": len(block_means),
                          "purpose": "privileged task-viability upper bound only; not a fair controller comparison",
                          "fixed_reactive_baseline_mse": float(np.mean(reactive_means)),
                          "reactive_baseline_definition": "command=clip(noisy relative-position observation,-1,+1); command=0 on missing observations; no fitting or tuning"}

    payload = {"analysis": "POSTRUN_TASK_VIABILITY_DIAGNOSTIC",
               "status": "COMPLETE",
               "method": "two post-run task diagnostics on the frozen test streams: a privileged controller sees exact target-relative position and current target velocity; a fixed proportional controller uses only the available noisy observation",
               "limitation": "the privileged controller bypasses sensor loss; the proportional baseline was not a frozen arm. Neither diagnostic enters the primary inference, and no model training was altered",
               "profiles": profiles,
               "runner_sha256": sha256(Path(__file__).with_name("run_experiment.py")),
               "diagnostic_code_sha256": sha256(Path(__file__))}
    out = ROOT / "data/results" / task.NAME / "POSTRUN_TASK_VIABILITY_ORACLE.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
