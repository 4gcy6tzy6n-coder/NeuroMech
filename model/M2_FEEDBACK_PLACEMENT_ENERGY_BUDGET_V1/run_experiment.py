#!/usr/bin/env python3
"""Fresh-seed, validation-selected M2 feedback-placement test under an effort budget."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
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
NAME = "M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1"
BASE_PATH = ROOT / "model" / "M2_SENSORIMOTOR_TRANSIENT_FILTER_V1" / "run_experiment.py"
BASE_SPEC = importlib.util.spec_from_file_location("m2_transient_filter_base", BASE_PATH)
if BASE_SPEC is None or BASE_SPEC.loader is None:
    raise ImportError(f"cannot load base model runner: {BASE_PATH}")
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)

CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
DEFAULT_OUT = ROOT / "data/results" / NAME / "canonical"
BLOCKS = tuple(range(16))
TRAIN_SEEDS = tuple(501_000 + b for b in BLOCKS)
LAMBDAS = (0.0, 0.1, 0.3, 0.6)
ARMS = ("SENSORY_SITE_1D", "OUTPUT_SITE_1D", "NO_FEEDBACK_1D", "GENERIC_RNN_1D", "GRU_8")
CONDITIONS = ("TRANSIENT_PULSE", "SUSTAINED_SWITCH", "COMBINED_STRESS")
N_VALIDATION = 32
N_TEST = 64
ENERGY_BUDGET = 0.50
UPDATES, BATCH, T, LR = 100, 32, 96, 0.01
METRICS = ("movement_mse", "movement_mae", "state_accuracy", "command_energy", "pulse_window_mae", "mean_switch_latency_steps")


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


def make_episodes(base_seed: int, n: int) -> dict[tuple[int, str, int], tuple[np.ndarray, ...]]:
    episodes = {}
    for block in BLOCKS:
        for ci, condition in enumerate(CONDITIONS):
            cfg = base.CONDITIONS[condition]
            for episode in range(n):
                seed = base_seed + block * 100_000 + ci * 1_000 + episode
                rng = np.random.default_rng(seed)
                z, y, noise, pulse = base.make_batch(rng, 1, T, cfg["hazard"], cfg["pulse_rate"], cfg["pulse_durations"])
                episodes[(block, condition, episode)] = (z[0], y[0], noise[0], pulse[0])
    return episodes


def fit_one(model: nn.Module, train_seed: int, energy_penalty: float) -> tuple[float, float, float, float]:
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    model.train()
    final_loss = final_mse = final_energy = float("nan")
    start = time.perf_counter()
    for update in range(UPDATES):
        rng = np.random.default_rng(train_seed + update * 7919)
        z_np, y_np, noise_np, _ = base.make_batch(rng, BATCH, T, 0.02, 0.02, base.PULSE_DURATIONS_TRAIN)
        z, y, noise = torch.from_numpy(z_np), torch.from_numpy(y_np), torch.from_numpy(noise_np)
        h = model.initial(BATCH)
        motor = torch.zeros(BATCH)
        previous_u = torch.zeros(BATCH)
        squared_errors, squared_commands = [], []
        for t in range(T):
            motor = base.RHO * motor + base.PLANT_GAIN * previous_u + noise[:, t]
            u, h = model.step(y[:, t], motor, h)
            squared_errors.append((motor - z[:, t]).square())
            squared_commands.append(u.square())
            previous_u = u
        mse = torch.stack(squared_errors, dim=1).mean()
        energy = torch.stack(squared_commands, dim=1).mean()
        loss = mse + energy_penalty * energy
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        final_loss, final_mse, final_energy = map(float, (loss.detach(), mse.detach(), energy.detach()))
    return final_loss, final_mse, final_energy, time.perf_counter() - start


def eval_one(model: nn.Module, arm: str, episodes: dict[tuple[int, str, int], tuple[np.ndarray, ...]], n: int,
             train_seed: int, block: int) -> list[dict[str, object]]:
    output = []
    for condition in CONDITIONS:
        for episode in range(n):
            z, y, noise, pulse = episodes[(block, condition, episode)]
            metrics = base.episode_metrics(model, arm, z, y, noise, pulse)
            output.append({"seed_block": block, "training_seed": train_seed, "condition": condition,
                           "episode": episode, **metrics})
    return output


def group_mean(rows: list[dict[str, object]], metric: str) -> float:
    values = [float(r[metric]) for r in rows if math.isfinite(float(r[metric]))]
    return float(np.mean(values)) if values else float("nan")


def bootstrap_mean(values: list[float], seed: int) -> dict[str, float | int]:
    v = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    boot = v[rng.integers(0, len(v), size=(20_000, len(v)))].mean(axis=1)
    return {"mean": float(v.mean()), "median": float(np.median(v)),
            "ci95_low": float(np.quantile(boot, 0.025)), "ci95_high": float(np.quantile(boot, 0.975)),
            "n_seed_blocks": int(len(v))}


def run(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    torch.set_num_threads(1)
    random.seed(20261003)
    train_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    selection_rows: list[dict[str, object]] = []
    test_rows: list[dict[str, object]] = []
    validation_episodes = make_episodes(5_000_000, N_VALIDATION)
    test_episodes = make_episodes(6_000_000, N_TEST)
    start_all = time.time()

    for block, train_seed in zip(BLOCKS, TRAIN_SEEDS):
        print(f"seed block {block + 1}/{len(BLOCKS)}", flush=True)
        candidates: dict[tuple[str, float], nn.Module] = {}
        for ai, arm in enumerate(ARMS):
            for li, lam in enumerate(LAMBDAS):
                model_seed = train_seed + ai * 100_003
                model = base.make_model(arm, model_seed)
                loss, final_mse, final_energy, seconds = fit_one(model, train_seed + 20_000, lam)
                candidates[(arm, lam)] = model
                train_rows.append({"seed_block": block, "training_seed": train_seed, "arm": arm,
                                   "energy_penalty": lam, "parameter_count": sum(p.numel() for p in model.parameters()),
                                   "updates": UPDATES, "batch_size": BATCH, "sequence_length": T,
                                   "final_training_objective": loss, "final_training_mse": final_mse,
                                   "final_training_command_energy": final_energy, "training_seconds": seconds})

        val_candidate_summary: dict[tuple[str, float], dict[str, float]] = {}
        for arm in ARMS:
            for lam in LAMBDAS:
                model = candidates[(arm, lam)]
                rows = eval_one(model, arm, validation_episodes, N_VALIDATION, train_seed, block)
                for row in rows:
                    row["arm"] = arm
                    row["energy_penalty"] = lam
                validation_rows.extend(rows)
                cond_means = {}
                for condition in CONDITIONS:
                    group = [r for r in rows if r["condition"] == condition]
                    cond_means[condition] = {m: group_mean(group, m) for m in METRICS}
                val_candidate_summary[(arm, lam)] = {
                    metric: float(np.mean([cond_means[c][metric] for c in CONDITIONS]))
                    for metric in ("movement_mae", "command_energy")
                }

        for arm in ARMS:
            eligible = [(lam, val_candidate_summary[(arm, lam)]) for lam in LAMBDAS
                        if val_candidate_summary[(arm, lam)]["command_energy"] <= ENERGY_BUDGET]
            if eligible:
                chosen_lam, selected = min(eligible, key=lambda x: (x[1]["movement_mae"], x[0]))
                selection_status = "VALIDATION_BUDGET_MET"
            else:
                chosen_lam = min(LAMBDAS, key=lambda lam: val_candidate_summary[(arm, lam)]["command_energy"])
                selected = val_candidate_summary[(arm, chosen_lam)]
                selection_status = "NO_VALIDATION_POLICY_WITHIN_BUDGET"
            selection_rows.append({"seed_block": block, "training_seed": train_seed, "arm": arm,
                                   "selected_energy_penalty": chosen_lam, "selection_status": selection_status,
                                   "validation_mean_mae_equal_condition": selected["movement_mae"],
                                   "validation_mean_energy_equal_condition": selected["command_energy"],
                                   "energy_budget": ENERGY_BUDGET})
            model = candidates[(arm, chosen_lam)]
            chosen_test_rows = eval_one(model, arm, test_episodes, N_TEST, train_seed, block)
            for row in chosen_test_rows:
                row["arm"] = arm
                row["selected_energy_penalty"] = chosen_lam
                row["selection_status"] = selection_status
            test_rows.extend(chosen_test_rows)

    write_csv(out / "fit_manifest.csv", train_rows)
    write_csv(out / "validation_episodes.csv", validation_rows)
    write_csv(out / "selection_manifest.csv", selection_rows)
    write_csv(out / "test_episodes.csv", test_rows)

    selected_map = {(int(r["seed_block"]), r["arm"]): r for r in selection_rows}
    test_by_key: dict[tuple[int, str, str], list[dict[str, object]]] = {}
    for row in test_rows:
        test_by_key.setdefault((int(row["seed_block"]), row["arm"], row["condition"]), []).append(row)
    seed_test_rows = []
    for key, rows in sorted(test_by_key.items()):
        block, arm, condition = key
        metrics = {m: group_mean(rows, m) for m in METRICS}
        seed_test_rows.append({"seed_block": block, "arm": arm, "condition": condition,
                               "selected_energy_penalty": selected_map[(block, arm)]["selected_energy_penalty"],
                               "selection_status": selected_map[(block, arm)]["selection_status"],
                               "n_episodes": len(rows), **metrics,
                               "eligible_pulse_events": sum(int(r["n_eligible_pulses"]) for r in rows),
                               "target_switches": sum(int(r["n_target_switches"]) for r in rows)})
    write_csv(out / "test_seed_summary.csv", seed_test_rows)

    primary_blocks = []
    for block in BLOCKS:
        if (selected_map[(block, "SENSORY_SITE_1D")]["selection_status"] == "VALIDATION_BUDGET_MET" and
                selected_map[(block, "OUTPUT_SITE_1D")]["selection_status"] == "VALIDATION_BUDGET_MET"):
            s = next(r for r in seed_test_rows if r["seed_block"] == block and r["arm"] == "SENSORY_SITE_1D" and r["condition"] == "TRANSIENT_PULSE")
            o = next(r for r in seed_test_rows if r["seed_block"] == block and r["arm"] == "OUTPUT_SITE_1D" and r["condition"] == "TRANSIENT_PULSE")
            primary_blocks.append({"seed_block": block, "sensory_minus_output_mae": float(s["movement_mae"]) - float(o["movement_mae"])})
    primary = bootstrap_mean([r["sensory_minus_output_mae"] for r in primary_blocks], 8_123_456) if primary_blocks else None

    metric_summary = {}
    for ci, condition in enumerate(CONDITIONS):
        metric_summary[condition] = {}
        for ai, arm in enumerate(ARMS):
            metric_summary[condition][arm] = {}
            rows = [r for r in seed_test_rows if r["condition"] == condition and r["arm"] == arm]
            for mi, metric in enumerate(METRICS):
                values = [float(r[metric]) for r in rows if math.isfinite(float(r[metric]))]
                metric_summary[condition][arm][metric] = bootstrap_mean(values, 7_654_321 + ci * 100 + ai * 10 + mi) if values else None

    budget_summary = {}
    for arm in ("SENSORY_SITE_1D", "OUTPUT_SITE_1D"):
        vals = [float(r["command_energy"]) for r in seed_test_rows
                if r["arm"] == arm and r["condition"] == "TRANSIENT_PULSE" and
                r["selection_status"] == "VALIDATION_BUDGET_MET"]
        budget_summary[arm] = bootstrap_mean(vals, 9_100_000 + len(budget_summary)) if vals else None
    budget_status = ("BOTH_TEST_MEAN_CIS_WITHIN_BUDGET" if all(budget_summary[a] is not None and budget_summary[a]["ci95_high"] <= ENERGY_BUDGET
                                                                  for a in ("SENSORY_SITE_1D", "OUTPUT_SITE_1D"))
                     else "HELDOUT_BUDGET_NOT_ESTABLISHED")

    summary = {
        "experiment": NAME,
        "classification": "post-result exploratory artificial follow-up; validation-selected policies; fresh seed blocks",
        "training_seed_blocks": len(BLOCKS), "training_candidates": len(train_rows),
        "validation_episode_rows": len(validation_rows), "selected_test_episode_rows": len(test_rows),
        "test_seed_summary_rows": len(seed_test_rows), "energy_budget": ENERGY_BUDGET,
        "primary_condition": "TRANSIENT_PULSE", "primary_metric": "movement_mae",
        "primary_contrast": "SENSORY_SITE_1D minus OUTPUT_SITE_1D among blocks with validation-feasible policies; negative favors sensory-site",
        "primary_paired_seed_block_values": primary_blocks,
        "primary_contrast_summary": primary,
        "primary_validation_feasible_blocks": len(primary_blocks),
        "primary_budget_status": budget_status,
        "heldout_primary_energy_by_arm": budget_summary,
        "validation_feasibility_counts": {arm: sum(r["arm"] == arm and r["selection_status"] == "VALIDATION_BUDGET_MET" for r in selection_rows) for arm in ARMS},
        "metric_summary": metric_summary,
        "scope": "synthetic task only; no biological validation or general AI claim; energy budget selected after prior task outcomes",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    outputs = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(out.iterdir()) if p.is_file()}
    manifest = {
        "experiment": NAME, "contract_sha256": sha256(CONTRACT), "runner_sha256": sha256(Path(__file__)),
        "base_model_runner_sha256": sha256(Path(base.__file__)), "verifier_sha256": sha256(ROOT / "model" / NAME / "verify_results.py"),
        "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
        "training_seeds": TRAIN_SEEDS, "penalties": LAMBDAS, "conditions": CONDITIONS,
        "episodes_validation_per_condition_candidate": N_VALIDATION, "episodes_test_per_condition_selected": N_TEST,
        "updates": UPDATES, "batch_size": BATCH, "sequence_length": T, "energy_budget": ENERGY_BUDGET,
        "duration_seconds": time.time() - start_all, "outputs": outputs,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": "COMPLETE", "output": str(out), "summary": summary["primary_contrast_summary"],
                      "budget_status": budget_status, "fit_candidates": len(train_rows), "test_rows": len(test_rows)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
