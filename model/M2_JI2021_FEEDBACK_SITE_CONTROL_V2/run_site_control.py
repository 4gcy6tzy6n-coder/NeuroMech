#!/usr/bin/env python3
"""Compare sensory-site corollary feedback with run-duration-matched motor inertia."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "summery/M2_JI2021_FEEDBACK_SITE_CONTROL_V2/M2_JI2021_FEEDBACK_SITE_CONTROL_V2_CONTRACT.md"
SOURCE = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/elife-68848-fig7-data1.zip"
OUT = ROOT / "data/results/M2_JI2021_FEEDBACK_SITE_CONTROL_V2"

N_STEPS = 1500
T_MAX = 200.0
DT = T_MAX / N_STEPS
N_AGENTS = 50
DEV_SEEDS = tuple(range(204000, 204030))
TEST_SEEDS = tuple(range(204100, 204200))
MOTOR_GRID = tuple(round(x / 1000, 3) for x in range(700, 801))
N_BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 20261002


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def centered_smooth(values: np.ndarray) -> np.ndarray:
    smoothed = np.empty_like(values)
    for t in range(values.shape[0]):
        smoothed[t] = values[max(0, t - 1) : min(values.shape[0], t + 3)].mean(axis=0)
    return smoothed


def run(seed: int, conditions: list[tuple[str, float, float]]) -> list[dict[str, float | int | str]]:
    rng = np.random.default_rng(seed)
    n_cond = len(conditions)
    sensory_fb = np.asarray([x[1] for x in conditions], dtype=float)[:, None]
    motor_fb = np.asarray([x[2] for x in conditions], dtype=float)[:, None]
    z = rng.standard_normal((N_STEPS, N_AGENTS))
    heading_reset = rng.random((N_STEPS, N_AGENTS)) * (2.0 * math.pi)
    heading0 = rng.random(N_AGENTS) * (2.0 * math.pi)

    a = np.ones((n_cond, N_AGENTS), dtype=float)
    m = np.ones_like(a)
    theta = np.broadcast_to(heading0, (n_cond, N_AGENTS)).copy()
    m_hist = np.empty((N_STEPS, n_cond, N_AGENTS), dtype=float)
    x_hist = np.empty_like(m_hist)
    theta_hist = np.empty_like(m_hist)
    m_hist[0] = m
    x_hist[0] = 0.0
    theta_hist[0] = theta
    delay_steps = round(0.5 * N_STEPS / T_MAX)

    for t in range(1, N_STEPS):
        old_forward = m_hist[max(0, t - 2)] >= 0.0
        previous_forward = m_hist[t - 1] >= 0.0
        f_to_r = old_forward & ~previous_forward
        r_to_f = ~old_forward & previous_forward
        theta = np.where(f_to_r, np.mod(theta + math.pi, 2.0 * math.pi), theta)
        theta = np.where(r_to_f, heading_reset[t][None, :], theta)

        x_now = x_hist[t - 1]
        x_then = x_hist[max(0, t - 1 - delay_steps)]
        sensory = ((x_now - x_then) * -1.5) * (m > 0.0)
        noise = 2.0 * z[t][None, :]
        da = 1.5 * (sensory + 0.5 + noise + sensory_fb * sigmoid(15.0 * m) - a) * DT
        dm = 1.5 * (
            sigmoid(5.0 * (a - 1.5))
            - 0.7 * sigmoid(-5.0 * (a - 1.5))
            + motor_fb * sigmoid(15.0 * m)
            - m
        ) * DT
        a += da
        m += dm
        x_hist[t] = x_now + np.cos(theta) * DT
        m_hist[t] = m
        theta_hist[t] = theta

    smoothed = centered_smooth(m_hist)
    forward = smoothed > 0.0
    records: list[dict[str, float | int | str]] = []
    for i, (name, fba, fbm) in enumerate(conditions):
        durations = []
        weighted_index = 0.0
        forward_samples = 0
        for agent in range(N_AGENTS):
            mask = forward[:, i, agent]
            changes = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
            starts = np.flatnonzero(changes == 1)
            ends = np.flatnonzero(changes == -1)
            durations.extend((ends - starts).tolist())
            forward_samples += int(mask.sum())
            weighted_index += float((-np.cos(theta_hist[:, i, agent]) * mask).sum())
        direction = weighted_index / forward_samples if forward_samples else math.nan
        records.append(
            {
                "seed_block": seed,
                "arm": name,
                "sensory_site_feedback": fba,
                "motor_only_feedback": fbm,
                "warm_direction_index": direction,
                "mean_forward_run_s": float(np.mean(durations) * DT) if durations else math.nan,
                "mean_final_warm_displacement": float(-x_hist[-1, i].mean()),
                "n_agents": N_AGENTS,
                "n_forward_runs": len(durations),
            }
        )
    return records


def mean_ci(values: np.ndarray, rng: np.random.Generator) -> list[float]:
    ids = rng.integers(0, values.size, size=(N_BOOTSTRAPS, values.size))
    boot = values[ids].mean(axis=1)
    return [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dev_conditions = [("SENSORY_SITE_FB", 1.0, 0.0)] + [(f"MOTOR_ONLY_{v:.3f}", 0.0, v) for v in MOTOR_GRID]
    dev_rows: list[dict[str, float | int | str]] = []
    for seed in DEV_SEEDS:
        dev_rows.extend(run(seed, dev_conditions))
    dev_duration = {
        str(v): float(np.mean([r["mean_forward_run_s"] for r in dev_rows if r["arm"] == f"MOTOR_ONLY_{v:.3f}"]))
        for v in MOTOR_GRID
    }
    sensory_duration = float(np.mean([r["mean_forward_run_s"] for r in dev_rows if r["arm"] == "SENSORY_SITE_FB"]))
    selected_motor_fb = min(MOTOR_GRID, key=lambda v: (abs(dev_duration[str(v)] - sensory_duration), v))

    test_conditions = [
        ("SENSORY_SITE_FB", 1.0, 0.0),
        ("MOTOR_ONLY_MATCHED", 0.0, selected_motor_fb),
        ("NO_FEEDBACK", 0.0, 0.0),
    ]
    test_rows: list[dict[str, float | int | str]] = []
    for seed in TEST_SEEDS:
        test_rows.extend(run(seed, test_conditions))

    metrics_path = OUT / "heldout_simulation_metrics.csv"
    with metrics_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(test_rows[0]))
        writer.writeheader()
        writer.writerows(test_rows)
    dev_path = OUT / "development_calibration.csv"
    with dev_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(dev_rows[0]))
        writer.writeheader()
        writer.writerows(dev_rows)

    lookup = {(int(r["seed_block"]), str(r["arm"])): r for r in test_rows}
    d_direction = np.asarray(
        [lookup[(s, "SENSORY_SITE_FB")]["warm_direction_index"] - lookup[(s, "MOTOR_ONLY_MATCHED")]["warm_direction_index"] for s in TEST_SEEDS],
        dtype=float,
    )
    d_duration = np.asarray(
        [lookup[(s, "SENSORY_SITE_FB")]["mean_forward_run_s"] - lookup[(s, "MOTOR_ONLY_MATCHED")]["mean_forward_run_s"] for s in TEST_SEEDS],
        dtype=float,
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    summary = {
        "status": "COMPLETED_POST_RESULT_MECHANISTIC_COUNTERFACTUAL",
        "calibration": {
            "development_seed_blocks": len(DEV_SEEDS),
            "sensory_site_mean_forward_run_s": sensory_duration,
            "motor_only_grid_mean_forward_run_s": dev_duration,
            "selected_motor_only_feedback": selected_motor_fb,
            "selected_motor_only_mean_forward_run_s": dev_duration[str(selected_motor_fb)],
        },
        "heldout": {
            "seed_blocks": len(TEST_SEEDS),
            "arms": {
                arm: {
                    "mean_warm_direction_index": float(np.mean([r["warm_direction_index"] for r in test_rows if r["arm"] == arm])),
                    "mean_forward_run_s": float(np.mean([r["mean_forward_run_s"] for r in test_rows if r["arm"] == arm])),
                    "mean_final_warm_displacement": float(np.mean([r["mean_final_warm_displacement"] for r in test_rows if r["arm"] == arm])),
                }
                for arm in ("SENSORY_SITE_FB", "MOTOR_ONLY_MATCHED", "NO_FEEDBACK")
            },
            "sensory_site_minus_motor_only_direction_index_mean": float(d_direction.mean()),
            "sensory_site_minus_motor_only_direction_index_95_ci": mean_ci(d_direction, rng),
            "sensory_site_minus_motor_only_duration_s_mean": float(d_duration.mean()),
            "sensory_site_minus_motor_only_duration_s_95_ci": mean_ci(d_duration, rng),
            "direction_index_positive_seed_count": int((d_direction > 0).sum()),
        },
        "analysis_unit": "simulation seed block; 50 agents clustered within each seed block",
        "biological_inference": "none; this is a source-model counterfactual, not a biological experiment",
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    arms = ("SENSORY_SITE_FB", "MOTOR_ONLY_MATCHED", "NO_FEEDBACK")
    labels = {"SENSORY_SITE_FB": "Feedback to sensory node", "MOTOR_ONLY_MATCHED": "Motor-only persistence (dev-calibrated)", "NO_FEEDBACK": "No feedback"}
    colors = {"SENSORY_SITE_FB": "#4C78A8", "MOTOR_ONLY_MATCHED": "#F58518", "NO_FEEDBACK": "#777777"}
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for arm in arms:
        xs = [float(r["mean_forward_run_s"]) for r in test_rows if r["arm"] == arm]
        ys = [float(r["warm_direction_index"]) for r in test_rows if r["arm"] == arm]
        ax.scatter(xs, ys, s=16, alpha=0.32, label=labels[arm], color=colors[arm])
        ax.scatter([np.mean(xs)], [np.mean(ys)], s=95, marker="D", color=colors[arm], edgecolor="white", linewidth=0.7, zorder=5)
    ax.set_xlabel("Mean forward-run duration per simulation seed block (s)")
    ax.set_ylabel("Warm-direction index (−cos heading)")
    ax.set_title("Feedback placement under a development-calibrated control")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig_path = OUT / "feedback_site_control.png"
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)

    manifest = {
        "experiment": "M2_JI2021_FEEDBACK_SITE_CONTROL_V2",
        "development_seeds": [DEV_SEEDS[0], DEV_SEEDS[-1]],
        "test_seeds": [TEST_SEEDS[0], TEST_SEEDS[-1]],
        "agents_per_block": N_AGENTS,
        "steps_per_trajectory": N_STEPS,
        "motor_only_calibration_grid": list(MOTOR_GRID),
        "selected_motor_only_feedback": selected_motor_fb,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": N_BOOTSTRAPS,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": matplotlib.__version__},
        "contract_sha256": sha256(CONTRACT),
        "source_archive_sha256": sha256(SOURCE),
        "runner_sha256": sha256(Path(__file__)),
        "output_sha256": {p.name: sha256(p) for p in (metrics_path, dev_path, summary_path, fig_path)},
        "heldout_rows": len(test_rows),
        "development_rows": len(dev_rows),
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
