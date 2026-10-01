#!/usr/bin/env python3
"""M2-inspired feedback-placement transfer in a liquid thermotaxis controller."""
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
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_LTC_THERMOTAXIS_REVERSAL_V1"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
SEEDS = tuple(range(920000, 920032))
LTC_ARMS = ("LTC_SENSORY_SITE", "LTC_OUTPUT_SITE", "LTC_NO_FEEDBACK", "LTC_DENSE_FEEDBACK", "LTC_SENSORY_YOKED")
GRU_ARMS = ("GRU_4", "GRU_8")
ARMS = (*LTC_ARMS, *GRU_ARMS, "GRADIENT_SIGN_ORACLE")
TRAIN_REVERSAL_HAZARD = 1 / 40
EVAL_REVERSAL_HAZARDS = (1 / 80, 1 / 40, 1 / 20)
OBS_TRANSITION_Q = 0.25
NTRAIN, NTEST, T = 96, 128, 128
UPDATES, BATCH, LR = 120, 8, 0.005
NBOOT, BOOT_SEED = 20_000, 20261003
HIDDEN, SENSORY_UNITS, ODE_UNFOLDS = 8, 4, 4
POSITION_SCALE, TEMP_SCALE, ACTION_SPEED = 20.0, 0.75, 0.25
ACTION_COST = 0.002


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inv_softplus(x: float) -> float:
    return float(np.log(np.expm1(x)))


def make_task(seed: int, n: int, reversal_hazard: float, steps: int = T) -> dict[str, np.ndarray]:
    rngs = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(8)]
    x0_rng, goal_rng, slope_rng, sign_rng, reversal_rng, noise_rng, vis_rng, vis_state_rng = rngs
    x0 = x0_rng.uniform(-18.0, 18.0, size=n).astype(np.float32)
    xstar = goal_rng.uniform(-8.0, 8.0, size=n).astype(np.float32)
    slope = slope_rng.uniform(0.025, 0.045, size=n).astype(np.float32)
    gradient = np.empty((n, steps), dtype=np.float32)
    gradient[:, 0] = sign_rng.choice(np.asarray([-1.0, 1.0], dtype=np.float32), size=n)
    flips = reversal_rng.random((n, steps)) < reversal_hazard
    for t in range(1, steps):
        gradient[:, t] = np.where(flips[:, t], -gradient[:, t - 1], gradient[:, t - 1])
    visible = np.empty((n, steps), dtype=np.float32)
    visible[:, 0] = vis_state_rng.integers(0, 2, size=n)
    vis_flips = vis_rng.random((n, steps)) < OBS_TRANSITION_Q
    for t in range(1, steps):
        visible[:, t] = np.where(vis_flips[:, t], 1.0 - visible[:, t - 1], visible[:, t - 1])
    noise = noise_rng.normal(0.0, 0.18, size=(n, steps)).astype(np.float32)
    return {"x0": x0, "xstar": xstar, "slope": slope, "gradient": gradient,
            "visible": visible, "noise": noise}


def as_tensors(data: dict[str, np.ndarray], indices=None, device="cpu"):
    result = {}
    for key, value in data.items():
        if indices is not None:
            value = value[indices]
        result[key] = torch.as_tensor(value, dtype=torch.float32, device=device)
    return result


class LiquidController(torch.nn.Module):
    """Equation-level LTC cell with feedback routed by a fixed pathway mask."""
    def __init__(self, arm: str):
        super().__init__()
        self.arm = arm
        self.w_rec = torch.nn.Parameter(torch.eye(HIDDEN) * 0.12 + torch.randn(HIDDEN, HIDDEN) * 0.025)
        self.w_temp = torch.nn.Parameter(torch.randn(HIDDEN) * 0.15)
        self.w_vis = torch.nn.Parameter(torch.randn(HIDDEN) * 0.10)
        self.bias = torch.nn.Parameter(torch.full((HIDDEN,), -0.8))
        self.raw_tau = torch.nn.Parameter(torch.full((HIDDEN,), inv_softplus(0.8)))
        self.reversal = torch.nn.Parameter(torch.randn(HIDDEN) * 0.12)
        self.readout = torch.nn.Parameter(torch.randn(HIDDEN) * 0.14)
        self.readout_bias = torch.nn.Parameter(torch.zeros(()))
        self.beta = torch.nn.Parameter(torch.tensor(0.25))
        if arm in ("LTC_SENSORY_SITE", "LTC_SENSORY_YOKED"):
            mask = torch.zeros(HIDDEN)
            mask[:SENSORY_UNITS] = 1.0
        elif arm == "LTC_DENSE_FEEDBACK":
            mask = torch.ones(HIDDEN)
        else:
            mask = torch.zeros(HIDDEN)
        self.register_buffer("sensory_mask", mask)

    def initial(self, n: int):
        return torch.zeros((n, HIDDEN), dtype=self.w_rec.dtype, device=self.w_rec.device)

    def step(self, temp_error, visible, h, motor_prev, sensory_context=None):
        route_motor = motor_prev if sensory_context is None else sensory_context
        dt = 1.0 / ODE_UNFOLDS
        tau = F.softplus(self.raw_tau) + 0.05
        leak = 1.0 / tau
        for _ in range(ODE_UNFOLDS):
            current = F.linear(h, self.w_rec) + temp_error[:, None] * self.w_temp + visible[:, None] * self.w_vis + self.bias
            if self.arm in ("LTC_SENSORY_SITE", "LTC_DENSE_FEEDBACK", "LTC_SENSORY_YOKED"):
                current = current + self.beta * route_motor[:, None] * self.sensory_mask
            conductance = F.softplus(current)
            h = (h + dt * conductance * self.reversal) / (1.0 + dt * (leak + conductance))
        output = F.linear(h, self.readout[None, :], self.readout_bias[None]).squeeze(-1)
        if self.arm == "LTC_OUTPUT_SITE":
            output = output + self.beta * motor_prev
        action = torch.tanh(output)
        return h, action


class GenericGRU(torch.nn.Module):
    def __init__(self, hidden: int):
        super().__init__()
        self.hidden = hidden
        self.cell = torch.nn.GRUCell(3, hidden)
        self.readout = torch.nn.Linear(hidden, 1)

    def initial(self, n: int):
        return torch.zeros((n, self.hidden), dtype=self.readout.weight.dtype, device=self.readout.weight.device)

    def step(self, temp_error, visible, h, motor_prev):
        inp = torch.stack((temp_error, visible, motor_prev), dim=-1)
        h = self.cell(inp, h)
        return h, torch.tanh(self.readout(h).squeeze(-1))


def controller(arm: str):
    if arm in LTC_ARMS:
        return LiquidController(arm)
    if arm == "GRU_4":
        return GenericGRU(4)
    if arm == "GRU_8":
        return GenericGRU(8)
    if arm == "GRADIENT_SIGN_ORACLE":
        return None
    raise ValueError(arm)


def rollout(data, model, arm: str, training=False):
    x0, xstar, slope = data["x0"], data["xstar"], data["slope"]
    gradient, visible, noise = data["gradient"], data["visible"], data["noise"]
    n, steps = gradient.shape
    x = x0.clone()
    if arm == "GRADIENT_SIGN_ORACLE":
        h = None
    else:
        h = model.initial(n)
    motor_prev = torch.zeros(n, dtype=x.dtype, device=x.device)
    distances, thermal, actions = [], [], []
    for t in range(steps):
        temp_error = gradient[:, t] * slope * (x - xstar) + noise[:, t]
        vis = visible[:, t]
        measured = torch.clamp(temp_error / TEMP_SCALE, -2.0, 2.0) * vis
        if arm == "GRADIENT_SIGN_ORACLE":
            action = torch.where(vis > 0, -torch.sign(measured * gradient[:, t]), motor_prev)
        elif arm == "LTC_SENSORY_YOKED":
            context = torch.roll(motor_prev, shifts=1, dims=0)
            h, action = model.step(measured, vis, h, motor_prev, sensory_context=context)
        else:
            h, action = model.step(measured, vis, h, motor_prev)
        x = torch.clamp(x + ACTION_SPEED * action, -25.0, 25.0)
        distances.append((x - xstar) / POSITION_SCALE)
        thermal.append(temp_error)
        actions.append(action)
        motor_prev = action
    distance = torch.stack(distances, dim=1)
    thermal_error = torch.stack(thermal, dim=1)
    action = torch.stack(actions, dim=1)
    if training:
        return (distance.square() + ACTION_COST * action.square()).mean()
    return {"distance": distance.detach().cpu().numpy() * POSITION_SCALE,
            "thermal_error": thermal_error.detach().cpu().numpy(),
            "action": action.detach().cpu().numpy(),
            "gradient": gradient.detach().cpu().numpy()}


def episode_rows(data_np, result, seed: int, arm: str, reversal_hazard: float):
    rows = []
    d, thermal, actions, grad = result["distance"], result["thermal_error"], result["action"], result["gradient"]
    for i in range(len(d)):
        reversal_times = [t for t in range(1, T) if grad[i, t] != grad[i, t - 1]]
        recovery = []
        for t in reversal_times:
            stop = min(T, t + 41)
            entered = None
            for k in range(t, max(t, stop - 4)):
                if np.all(np.abs(d[i, k:k + 5]) <= 2.0):
                    entered = k - t
                    break
            recovery.append(float(entered if entered is not None else min(40, T - t)))
        rows.append({"training_seed": seed, "arm": arm, "reversal_hazard": reversal_hazard,
                     "episode_id": i, "position_mse": float(np.mean(d[i] ** 2)),
                     "position_mae": float(np.mean(np.abs(d[i]))),
                     "temperature_error_mse": float(np.mean(thermal[i] ** 2)),
                     "action_energy": float(np.mean(actions[i] ** 2)),
                     "preferred_band_occupancy": float(np.mean(np.abs(d[i]) <= 2.0)),
                     "post_reversal_band_recovery_steps": float(np.mean(recovery)) if recovery else "",
                     "reversal_count": len(reversal_times),
                     "gradient_oracle": arm == "GRADIENT_SIGN_ORACLE"})
    return rows


def write_csv(path: Path, rows):
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    if args.preflight:
        if any(out.iterdir()):
            raise FileExistsError(f"preflight requires an empty output directory: {out}")
        checks = []
        task = as_tensors(make_task(2701, 3, TRAIN_REVERSAL_HAZARD, steps=16))
        for i, arm in enumerate(ARMS):
            torch.manual_seed(7000 + i)
            model = controller(arm)
            if model is None:
                result = rollout(task, None, arm, training=False)
                checks.append({"arm": arm, "parameter_count": 0, "finite_outputs": bool(np.isfinite(result["distance"]).all())})
                continue
            loss = rollout(task, model, arm, training=True)
            loss.backward()
            grad_checks = {}
            for name, parameter in model.named_parameters():
                # The no-feedback ablation intentionally leaves beta disconnected.
                # Preserve the shared parameter tensor layout while making this
                # dormant parameter explicit instead of treating it as a failure.
                expected_dormant = arm == "LTC_NO_FEEDBACK" and name == "beta"
                grad_checks[name] = (parameter.grad is None if expected_dormant else
                                     parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()))
            checks.append({"arm": arm, "parameter_count": sum(p.numel() for p in model.parameters()),
                           "finite_loss": bool(torch.isfinite(loss)),
                           "gradient_checks_pass": all(grad_checks.values()),
                           "dormant_parameters": [name for name, parameter in model.named_parameters()
                                                   if parameter.grad is None]})
        (out / "PREFLIGHT.json").write_text(json.dumps({
            "experiment_id": EXP, "outcomes_computed": False,
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
            "training": {"seed_first": SEEDS[0], "seed_last": SEEDS[-1], "episodes": NTRAIN, "steps": T,
                         "updates": UPDATES, "batch": BATCH, "learning_rate": LR,
                         "reversal_hazard": TRAIN_REVERSAL_HAZARD, "observation_transition_q": OBS_TRANSITION_Q},
            "evaluation": {"episodes_per_seed_condition": NTEST, "reversal_hazards": EVAL_REVERSAL_HAZARDS,
                           "arms": ARMS}, "checks": checks}, indent=2) + "\n")
        print(json.dumps(checks, indent=2))
        return
    preflight = out / "PREFLIGHT.json"
    if not preflight.is_file():
        raise FileNotFoundError("run --preflight first in an empty output directory")
    pre = json.loads(preflight.read_text())
    if pre["contract_sha256"] != sha(CONTRACT) or pre["runner_sha256"] != sha(Path(__file__)):
        raise RuntimeError("contract or runner changed after preflight")
    output_names = ("episode_results.csv", "training_results.csv", "RUN_METADATA.json")
    if any((out / name).exists() for name in output_names):
        raise FileExistsError("refusing to overwrite existing outcome files")

    episode_data, fit_data = [], []
    run_started = time.perf_counter()
    for seed_i, seed in enumerate(SEEDS):
        train_np = make_task(seed * 97 + 501, NTRAIN, TRAIN_REVERSAL_HAZARD)
        batch_schedule = np.random.default_rng(seed + 610_003).integers(0, NTRAIN, size=(UPDATES, BATCH))
        train_tensors = as_tensors(train_np)
        for arm_i, arm in enumerate((*LTC_ARMS, *GRU_ARMS)):
            torch.manual_seed(seed * 19 + arm_i)
            model = controller(arm)
            opt = torch.optim.Adam(model.parameters(), lr=LR)
            started = time.perf_counter()
            losses = []
            for update in range(UPDATES):
                batch_idx = batch_schedule[update]
                batch = {key: value[batch_idx] for key, value in train_tensors.items()}
                loss = rollout(batch, model, arm, training=True)
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 3.0)
                opt.step()
                losses.append(float(loss.detach()))
            training_seconds = time.perf_counter() - started
            fit_data.append({"training_seed": seed, "arm": arm,
                "parameter_count": sum(p.numel() for p in model.parameters()), "updates": UPDATES,
                "batch_size": BATCH, "sequence_steps_per_fit": UPDATES * BATCH * T,
                "training_seconds": training_seconds,
                "initial_loss": losses[0], "final_10_update_loss": float(np.mean(losses[-10:])),
                "parameters_json": json.dumps({k: v.detach().reshape(-1).tolist() for k, v in model.state_dict().items()}, separators=(",", ":"))})
            model.eval()
            with torch.no_grad():
                for qi, hazard in enumerate(EVAL_REVERSAL_HAZARDS):
                    test_np = make_task(8_200_000 + seed_i * 100 + qi, NTEST, hazard)
                    test_data = as_tensors(test_np)
                    result = rollout(test_data, model, arm, training=False)
                    episode_data.extend(episode_rows(test_np, result, seed, arm, hazard))
        with torch.no_grad():
            for qi, hazard in enumerate(EVAL_REVERSAL_HAZARDS):
                test_np = make_task(8_200_000 + seed_i * 100 + qi, NTEST, hazard)
                result = rollout(as_tensors(test_np), None, "GRADIENT_SIGN_ORACLE", training=False)
                episode_data.extend(episode_rows(test_np, result, seed, "GRADIENT_SIGN_ORACLE", hazard))
        print(f"completed seed {seed} ({seed_i + 1}/{len(SEEDS)})", flush=True)

    write_csv(out / "episode_results.csv", episode_data)
    write_csv(out / "training_results.csv", fit_data)
    (out / "RUN_METADATA.json").write_text(json.dumps({
        "experiment_id": EXP, "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
        "total_runtime_seconds": time.perf_counter() - run_started, "seeds": list(SEEDS),
        "learned_arms": (*LTC_ARMS, *GRU_ARMS), "all_arms": ARMS,
        "evaluation_reversal_hazards": EVAL_REVERSAL_HAZARDS,
        "parameter_counts": {arm: int(next(r["parameter_count"] for r in fit_data if r["arm"] == arm))
                              for arm in (*LTC_ARMS, *GRU_ARMS)},
        "episode_rows": len(episode_data), "training_rows": len(fit_data)}, indent=2) + "\n")
    print(f"Wrote {len(episode_data)} episode rows and {len(fit_data)} fitted models to {out}")


if __name__ == "__main__":
    main()
