#!/usr/bin/env python3
"""Test recipient-specific motor feedback against a distribution-preserving yoke."""
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
ID = "M2_RECIPIENT_SPECIFIC_FEEDBACK_YOKE_V1"
CONTRACT = ROOT / "summery" / ID / "CONTRACT.md"
BASE_RUNNER = ROOT / "model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1/run_experiment.py"
OUT_DEFAULT = ROOT / "data/results" / ID / "canonical"
SEEDS = tuple(range(420000, 420032))
HAZARDS = (1 / 240, 1 / 120, 1 / 40)
MISSING = (0.25, 0.50, 0.75)
TRAIN_HAZARD, TRAIN_MISSING = 1 / 120, 0.50
NTRAIN, NTEST, STEPS = 256, 256, 240
UPDATES, BATCH, LR = 100, 16, 0.01
BOOTSTRAPS, BOOT_SEED = 10_000, 20261029
ARMS = ("SENSORY_SELF", "SENSORY_CROSS_AGENT_YOKE", "OUTPUT_SITE_PERSISTENCE",
        "NO_FEEDBACK", "GENERIC_RNN_1H", "ORACLE_RELATIVE_ERROR")
BASE_ARMS = ("SENSORY_SITE_FEEDBACK", "OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "GENERIC_RNN_1H")

# Reuse the previous, already audited environment/controller implementation.
import sys
sys.path.insert(0, str(ROOT / "model/M2_MOTOR_FEEDBACK_SPARSE_TRACKING_V1"))
import run_experiment as base


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def derangement(seed: int, n: int) -> np.ndarray:
    """Make a random one-to-one cyclic derangement of episode IDs."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(n)
    donor_for_recipient = np.empty(n, dtype=np.int64)
    donor_for_recipient[order] = np.roll(order, 1)
    if np.any(donor_for_recipient == np.arange(n)) or len(np.unique(donor_for_recipient)) != n:
        raise AssertionError("donor assignment is not a derangement bijection")
    return donor_for_recipient


def rollout(arm: str, target, noise, visible, *, model=None, external_motor=None, training=False):
    with torch.set_grad_enabled(training):
        return _rollout_impl(arm, target, noise, visible, model=model,
                             external_motor=external_motor, training=training)


def _rollout_impl(arm: str, target, noise, visible, *, model=None, external_motor=None, training=False):
    target = torch.as_tensor(target, dtype=torch.float32)
    noise = torch.as_tensor(noise, dtype=torch.float32)
    visible = torch.as_tensor(visible, dtype=torch.float32)
    ext = None if external_motor is None else torch.as_tensor(external_motor, dtype=torch.float32)
    n, steps = target.shape
    cursor = torch.zeros(n, dtype=torch.float32)
    hidden = torch.zeros(n, dtype=torch.float32)
    own_motor_prev = torch.zeros(n, dtype=torch.float32)
    errors, motors = [], []
    for t in range(steps):
        relative = target[:, t] - cursor
        sensation = visible[:, t] * (relative + base.OBS_SD * noise[:, t])
        if arm == "ORACLE_RELATIVE_ERROR":
            motor = torch.tanh(base.ACTION_GAIN * relative)
        else:
            feedback = ext[:, t] if ext is not None else own_motor_prev
            hidden, motor = model.step(sensation, hidden, feedback)
        cursor = torch.clamp(cursor + base.STEP * motor, -1.0, 1.0)
        errors.append(target[:, t] - cursor)
        motors.append(motor)
        own_motor_prev = motor
    error = torch.stack(errors, dim=1)
    motor = torch.stack(motors, dim=1)
    if training:
        return (error.square() + base.ACTION_COST * motor.square()).mean()
    return error.detach().cpu().numpy(), motor.detach().cpu().numpy()


def train_models(seed: int, output_dir: Path) -> tuple[dict, list[dict]]:
    train_target, train_noise, train_visible = base.exogenous(
        seed * 17 + 101, NTRAIN, TRAIN_HAZARD, TRAIN_MISSING, STEPS
    )
    batch_rng = np.random.default_rng(seed + 990_001)
    batches = batch_rng.integers(0, NTRAIN, size=(UPDATES, BATCH))
    models, fits = {}, []
    for arm_index, arm in enumerate(BASE_ARMS):
        source_arm = "SENSORY_SITE_FEEDBACK" if arm == "SENSORY_SITE_FEEDBACK" else arm
        torch.manual_seed(seed * 100 + arm_index)
        model = base.Policy(source_arm)
        optimizer = torch.optim.Adam(model.parameters(), lr=LR)
        losses = []
        start = time.perf_counter()
        for batch_ids in batches:
            idx = torch.as_tensor(batch_ids, dtype=torch.long)
            loss = rollout(source_arm, train_target[idx], train_noise[idx], train_visible[idx], model=model, training=True)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            losses.append(float(loss.detach()))
        count = sum(parameter.numel() for parameter in model.parameters())
        fits.append({
            "training_seed": seed,
            "arm": "SENSORY_SELF" if arm == "SENSORY_SITE_FEEDBACK" else arm,
            "parameter_count": count,
            "updates": UPDATES,
            "batch_size": BATCH,
            "sequence_steps_per_fit": UPDATES * BATCH * STEPS,
            "initial_loss": losses[0],
            "final_10_update_loss": float(np.mean(losses[-10:])),
            "training_seconds": time.perf_counter() - start,
            "parameters_json": json.dumps(torch.cat([p.detach().reshape(-1) for p in model.parameters()]).tolist()),
        })
        model.eval()
        models["SENSORY_SELF" if arm == "SENSORY_SITE_FEEDBACK" else arm] = model
    output_dir.mkdir(parents=True, exist_ok=True)
    return models, fits


def episode_rows(seed: int, hazard: float, missing: float, target: np.ndarray,
                 noise: np.ndarray, visible: np.ndarray, models: dict, condition_seed: int):
    rows, audit = [], None
    self_err, self_motor = rollout("SENSORY_SITE_FEEDBACK", target, noise, visible,
                                   model=models["SENSORY_SELF"])
    donor = derangement(condition_seed + 700_001, NTEST)
    yoke_signal = np.zeros_like(self_motor)
    yoke_signal[:, 1:] = self_motor[donor, :-1]
    expected_signal = np.zeros_like(self_motor)
    expected_signal[:, 1:] = self_motor[:, :-1]
    self_hashes = [hashlib.sha256(np.sort(expected_signal[:, t]).tobytes()).hexdigest() for t in range(STEPS)]
    yoke_hashes = [hashlib.sha256(np.sort(yoke_signal[:, t]).tobytes()).hexdigest() for t in range(STEPS)]
    audit = {
        "training_seed": seed,
        "hazard": hazard,
        "missing_rate": missing,
        "steps_checked": STEPS,
        "all_timestep_marginals_match": self_hashes == yoke_hashes,
        "donor_assignment_is_derangement": bool(np.all(donor != np.arange(NTEST))),
        "donor_assignment_json": json.dumps(donor.tolist()),
        "donor_assignment_sha256": hashlib.sha256(donor.tobytes()).hexdigest(),
        "self_signal_marginal_hashes_sha256": hashlib.sha256("".join(self_hashes).encode()).hexdigest(),
        "yoke_signal_marginal_hashes_sha256": hashlib.sha256("".join(yoke_hashes).encode()).hexdigest(),
    }
    if not audit["all_timestep_marginals_match"] or not audit["donor_assignment_is_derangement"]:
        raise AssertionError("cross-agent yoke failed its distribution/identity audit")
    outputs = {"SENSORY_SELF": (self_err, self_motor)}
    yoke_err, yoke_motor = rollout("SENSORY_SITE_FEEDBACK", target, noise, visible,
                                   model=models["SENSORY_SELF"], external_motor=yoke_signal)
    outputs["SENSORY_CROSS_AGENT_YOKE"] = (yoke_err, yoke_motor)
    for arm in ("OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "GENERIC_RNN_1H"):
        outputs[arm] = rollout(arm, target, noise, visible, model=models[arm])
    outputs["ORACLE_RELATIVE_ERROR"] = rollout("ORACLE_RELATIVE_ERROR", target, noise, visible)
    for arm in ARMS:
        err, motor = outputs[arm]
        recovery = np.array([base.switch_recovery(target[i:i + 1], err[i:i + 1]) for i in range(NTEST)])
        for episode_id in range(NTEST):
            rows.append({
                "training_seed": seed,
                "hazard": hazard,
                "missing_rate": missing,
                "episode_id": episode_id,
                "arm": arm,
                "tracking_mse": float(np.mean(err[episode_id] ** 2)),
                "tracking_mae": float(np.mean(np.abs(err[episode_id]))),
                "action_energy": float(np.mean(motor[episode_id] ** 2)),
                "switch_recovery_steps": "" if np.isnan(recovery[episode_id]) else float(recovery[episode_id]),
            })
    return rows, audit


def crossed_bootstrap(matrix: np.ndarray, rng: np.random.Generator) -> dict:
    reps = np.empty(BOOTSTRAPS, dtype=np.float64)
    for start in range(0, BOOTSTRAPS, 200):
        count = min(200, BOOTSTRAPS - start)
        seed_draws = rng.integers(0, matrix.shape[0], size=(count, matrix.shape[0]))
        episode_draws = rng.integers(0, matrix.shape[1], size=(count, matrix.shape[1]))
        reps[start:start + count] = matrix[seed_draws[:, :, None], episode_draws[:, None, :]].mean(axis=(1, 2))
    return {
        "mean": float(matrix.mean()),
        "ci95": [float(x) for x in np.quantile(reps, [0.025, 0.975])],
        "positive_seed_blocks": int(np.sum(matrix.mean(axis=1) > 0)),
        "n_seed_blocks": int(matrix.shape[0]),
        "n_episodes_per_seed": int(matrix.shape[1]),
    }


def preflight(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"preflight output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    checks = []
    for index, arm in enumerate(BASE_ARMS):
        model = base.Policy(arm)
        seed = 900 + index
        torch.manual_seed(seed)
        target, noise, visible = base.exogenous(seed, 4, TRAIN_HAZARD, TRAIN_MISSING, 12)
        loss = rollout(arm, target, noise, visible, model=model, training=True)
        loss.backward()
        checks.append({
            "arm": "SENSORY_SELF" if arm == "SENSORY_SITE_FEEDBACK" else arm,
            "parameters": sum(p.numel() for p in model.parameters()),
            "finite_loss": bool(torch.isfinite(loss)),
            "finite_gradients": all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()),
        })
    rng = np.random.default_rng(82201)
    donor = derangement(82202, NTEST)
    signal = rng.normal(size=(NTEST, STEPS)).astype(np.float32)
    passed = all(np.array_equal(np.sort(signal[:, t]), np.sort(signal[donor, t])) for t in range(STEPS))
    document = {
        "experiment_id": ID,
        "outcomes_computed": False,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "contract_sha256": sha(CONTRACT),
        "runner_sha256": sha(Path(__file__).resolve()),
        "base_runner_sha256": sha(BASE_RUNNER),
        "arm_checks": checks,
        "donor_permutation_test": {"bijective_derangement": True, "marginal_preserved_all_steps": passed},
        "training": {"seeds": [SEEDS[0], SEEDS[-1]], "episodes": NTRAIN, "steps": STEPS,
                     "updates": UPDATES, "batch_size": BATCH, "learning_rate": LR},
        "evaluation": {"episodes_per_seed_condition": NTEST, "hazards": HAZARDS, "missing_rates": MISSING, "arms": ARMS},
        "primary_bootstrap": {"resamples": BOOTSTRAPS, "seed": BOOT_SEED},
    }
    if not all(x["finite_loss"] and x["finite_gradients"] for x in checks) or not passed:
        raise RuntimeError("preflight failed")
    (output / "PREFLIGHT.json").write_text(json.dumps(document, indent=2) + "\n")
    print(json.dumps(document, indent=2))


def run(output: Path) -> None:
    pre_path = output / "PREFLIGHT.json"
    if not pre_path.is_file():
        raise FileNotFoundError("run --preflight first; preflight computes no outcomes")
    pre = json.loads(pre_path.read_text())
    expected = {"contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__).resolve()),
                "base_runner_sha256": sha(BASE_RUNNER)}
    for key, value in expected.items():
        if pre.get(key) != value:
            raise RuntimeError(f"{key} changed after preflight")
    if any((output / name).exists() for name in ("episode_results.csv", "training_results.csv", "yoke_signal_audit.csv", "summary.json", "RUN_MANIFEST.json")):
        raise FileExistsError("refusing to overwrite existing experiment outputs")
    torch.set_num_threads(1)
    episode_records, training_records, audits = [], [], []
    begin = time.perf_counter()
    for seed_index, seed in enumerate(SEEDS):
        models, fits = train_models(seed, output)
        training_records.extend(fits)
        for hi, hazard in enumerate(HAZARDS):
            for mi, missing in enumerate(MISSING):
                condition_seed = base.condition_seed(seed_index, hi, mi) + 4_100_000
                target, noise, visible = base.exogenous(condition_seed, NTEST, hazard, missing, STEPS)
                rows, audit = episode_rows(seed, hazard, missing, target, noise, visible, models,
                                           condition_seed + seed_index * 31)
                episode_records.extend(rows)
                audits.append(audit)
        print(f"completed recipient-specific feedback seed {seed} ({seed_index + 1}/{len(SEEDS)})", flush=True)
    csv_write(output / "episode_results.csv", episode_records)
    csv_write(output / "training_results.csv", training_records)
    csv_write(output / "yoke_signal_audit.csv", audits)

    lookup = {(int(r["training_seed"]), float(r["hazard"]), float(r["missing_rate"]), int(r["episode_id"]), r["arm"]): float(r["tracking_mse"])
              for r in episode_records}
    seed_list = list(SEEDS)
    primary = np.array([[lookup[(seed, TRAIN_HAZARD, TRAIN_MISSING, ep, "SENSORY_CROSS_AGENT_YOKE")] -
                         lookup[(seed, TRAIN_HAZARD, TRAIN_MISSING, ep, "SENSORY_SELF")]
                         for ep in range(NTEST)] for seed in seed_list])
    rng = np.random.default_rng(BOOT_SEED)
    primary_summary = crossed_bootstrap(primary, rng)
    contrasts = {}
    for arm in ("OUTPUT_SITE_PERSISTENCE", "NO_FEEDBACK", "GENERIC_RNN_1H", "ORACLE_RELATIVE_ERROR"):
        matrix = np.array([[lookup[(seed, TRAIN_HAZARD, TRAIN_MISSING, ep, arm)] -
                            lookup[(seed, TRAIN_HAZARD, TRAIN_MISSING, ep, "SENSORY_SELF")]
                            for ep in range(NTEST)] for seed in seed_list])
        contrasts[arm] = crossed_bootstrap(matrix, rng)
    condition_means = {}
    for hazard in HAZARDS:
        for missing in MISSING:
            key = f"h={hazard:.8g}|missing={missing:.2f}"
            group = [r for r in episode_records if float(r["hazard"]) == hazard and float(r["missing_rate"]) == missing]
            condition_means[key] = {arm: float(np.mean([float(r["tracking_mse"]) for r in group if r["arm"] == arm])) for arm in ARMS}
    summary = {
        "experiment_id": ID,
        "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_MECHANISM_TRANSFER",
        "seed_blocks": len(SEEDS),
        "episodes_per_seed_condition": NTEST,
        "primary_contrast": "MSE(SENSORY_CROSS_AGENT_YOKE) - MSE(SENSORY_SELF); positive favors recipient-specific feedback",
        "primary_condition": {"hazard": TRAIN_HAZARD, "missing_rate": TRAIN_MISSING},
        "primary": primary_summary,
        "direct_control_contrasts_vs_sensory_self": contrasts,
        "condition_mean_tracking_mse": condition_means,
        "yoke_checks": {"n_seed_condition_blocks": len(audits),
                        "marginals_match_at_each_time_step": all(a["all_timestep_marginals_match"] for a in audits),
                        "all_donor_assignments_are_derangements": all(a["donor_assignment_is_derangement"] for a in audits),
                        "time_steps_checked": sum(a["steps_checked"] for a in audits)},
        "resources": {"parameters_per_learned_model": 3, "updates": UPDATES,
                      "batch_size": BATCH, "sequence_steps_per_fit": UPDATES * BATCH * STEPS},
        "claim_boundary": "Artificial action-coupled tracking result only; no biological validation or general AI benefit.",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    files = ["PREFLIGHT.json", "episode_results.csv", "training_results.csv", "yoke_signal_audit.csv", "summary.json"]
    manifest = {
        "experiment_id": ID,
        "classification": summary["classification"],
        "python": platform.python_version(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "seed_blocks": [SEEDS[0], SEEDS[-1]],
        "runner_sha256": sha(Path(__file__).resolve()),
        "base_runner_sha256": sha(BASE_RUNNER),
        "contract_sha256": sha(CONTRACT),
        "episode_rows": len(episode_records),
        "training_rows": len(training_records),
        "yoke_audit_rows": len(audits),
        "wall_seconds": time.perf_counter() - begin,
        "files": {name: {"bytes": (output / name).stat().st_size, "sha256": sha(output / name)} for name in files},
    }
    (output / "RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        preflight(args.output_dir.resolve())
    else:
        run(args.output_dir.resolve())


if __name__ == "__main__":
    main()
