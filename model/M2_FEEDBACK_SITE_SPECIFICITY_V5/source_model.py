#!/usr/bin/env python3
"""Test sensory-site feedback robustness over noise scales in the Ji et al. source model."""

from __future__ import annotations

import csv
import argparse
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
CONTRACT = ROOT / "summery/M2_FEEDBACK_SITE_SPECIFICITY_V5/CONTRACT.md"
SOURCE = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/elife-68848-fig7-data1.zip"
OUT = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5"

N_STEPS = 1500
T_MAX = 200.0
DT = T_MAX / N_STEPS
N_AGENTS = 50
DEV_SEEDS = tuple(range(310000, 310040))
TEST_SEEDS = tuple(range(311000, 311200))
NOISE_SCALES = (0.75, 1.00, 1.25)
MOTOR_GRID = tuple(round(x / 1000, 3) for x in range(600, 851, 5))
N_BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 20261003


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


def run(seed: int, conditions: list[tuple[str, float, float, float]]) -> list[dict[str, float | int | str]]:
    rng = np.random.default_rng(seed)
    n_cond = len(conditions)
    sensory_fb = np.asarray([x[1] for x in conditions], dtype=float)[:, None]
    motor_fb = np.asarray([x[2] for x in conditions], dtype=float)[:, None]
    noise_scale = np.asarray([x[3] for x in conditions], dtype=float)[:, None]
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
        # MATLAB's `ti` is one-based and, before each update, XS contains
        # rows 1..ti-1. `lagi=max(1, ti-delay_steps)` maps to this
        # zero-based history index, max(0, t-delay_steps).
        x_then = x_hist[max(0, t - delay_steps)]
        sensory = ((x_now - x_then) * -1.5) * (m > 0.0)
        noise = 2.0 * z[t][None, :] * noise_scale
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
    for i, (name, fba, fbm, scale) in enumerate(conditions):
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
                "noise_scale": scale,
                "sensory_site_feedback": fba,
                "motor_only_feedback": fbm,
                "warm_direction_index": direction,
                "mean_forward_run_s": float(np.mean(durations) * DT) if durations else math.nan,
                "median_forward_run_s": float(np.median(durations) * DT) if durations else math.nan,
                "p90_forward_run_s": float(np.quantile(durations, 0.90) * DT) if durations else math.nan,
                "fraction_forward_runs_ge_30s": float(np.mean(np.asarray(durations) * DT >= 30.0)) if durations else math.nan,
                "forward_occupancy": float(forward_samples / (N_STEPS * N_AGENTS)),
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
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT,
                        help="new result directory; defaults to the V5 result path")
    OUT = parser.parse_args().output_dir.expanduser().resolve()
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite an existing result directory: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)

    dev_conditions = []
    for scale in NOISE_SCALES:
        dev_conditions.append(("SENSORY_SITE_FB", 1.0, 0.0, scale))
        dev_conditions.extend((f"MOTOR_ONLY_{v:.3f}", 0.0, v, scale) for v in MOTOR_GRID)
    dev_rows: list[dict[str, float | int | str]] = []
    for i, seed in enumerate(DEV_SEEDS, start=1):
        dev_rows.extend(run(seed, dev_conditions))
        if i % 10 == 0:
            print(f"development blocks {i}/{len(DEV_SEEDS)}", flush=True)

    selected_motor: dict[float, float] = {}
    calibration: dict[str, object] = {}
    for scale in NOISE_SCALES:
        sensory_duration = float(np.mean([
            r["mean_forward_run_s"] for r in dev_rows
            if r["arm"] == "SENSORY_SITE_FB" and float(r["noise_scale"]) == scale
        ]))
        motor_duration = {
            v: float(np.mean([
                r["mean_forward_run_s"] for r in dev_rows
                if r["arm"] == f"MOTOR_ONLY_{v:.3f}" and float(r["noise_scale"]) == scale
            ])) for v in MOTOR_GRID
        }
        selected = min(MOTOR_GRID, key=lambda v: (abs(motor_duration[v] - sensory_duration), v))
        selected_motor[scale] = selected
        calibration[str(scale)] = {
            "sensory_site_mean_forward_run_s": sensory_duration,
            "selected_motor_feedback": selected,
            "selected_motor_only_mean_forward_run_s": motor_duration[selected],
            "absolute_development_match_error_s": abs(motor_duration[selected] - sensory_duration),
        }

    test_conditions = []
    for scale in NOISE_SCALES:
        test_conditions.extend([
            ("SENSORY_SITE_FB", 1.0, 0.0, scale),
            ("MOTOR_ONLY_MATCHED", 0.0, selected_motor[scale], scale),
            ("NO_FEEDBACK", 0.0, 0.0, scale),
        ])
    test_rows: list[dict[str, float | int | str]] = []
    for i, seed in enumerate(TEST_SEEDS, start=1):
        test_rows.extend(run(seed, test_conditions))
        if i % 25 == 0:
            print(f"held-out blocks {i}/{len(TEST_SEEDS)}", flush=True)

    def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    metrics_path = OUT / "heldout_simulation_metrics.csv"
    write_csv(metrics_path, test_rows)
    dev_path = OUT / "development_calibration.csv"
    write_csv(dev_path, dev_rows)

    lookup = {
        (int(r["seed_block"]), float(r["noise_scale"]), str(r["arm"])): r for r in test_rows
    }
    by_scale: dict[str, object] = {}
    scale_diffs = []
    for scale in NOISE_SCALES:
        d_direction = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "MOTOR_ONLY_MATCHED")]["warm_direction_index"])
            for seed in TEST_SEEDS
        ])
        d_duration = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["mean_forward_run_s"])
            - float(lookup[(seed, scale, "MOTOR_ONLY_MATCHED")]["mean_forward_run_s"])
            for seed in TEST_SEEDS
        ])
        scale_diffs.append(d_direction)
        rng = np.random.default_rng(BOOTSTRAP_SEED + int(scale * 100))
        arm_summary = {}
        for arm in ("SENSORY_SITE_FB", "MOTOR_ONLY_MATCHED", "NO_FEEDBACK"):
            cell = [r for r in test_rows if r["arm"] == arm and float(r["noise_scale"]) == scale]
            arm_summary[arm] = {
                metric: float(np.mean([float(r[metric]) for r in cell]))
                for metric in ("warm_direction_index", "mean_forward_run_s", "median_forward_run_s",
                               "p90_forward_run_s", "fraction_forward_runs_ge_30s", "forward_occupancy",
                               "n_forward_runs", "mean_final_warm_displacement")
            }
        by_scale[str(scale)] = {
            "selected_motor_feedback": selected_motor[scale],
            "arms": arm_summary,
            "sensory_site_minus_motor_only_direction_index": {
                "mean": float(d_direction.mean()), "ci95": mean_ci(d_direction, rng),
                "positive_seed_blocks": int((d_direction > 0).sum()),
            },
            "sensory_site_minus_motor_only_mean_run_duration_s": {
                "mean": float(d_duration.mean()), "ci95": mean_ci(d_duration, rng),
            },
        }

    pooled_by_seed = np.stack(scale_diffs, axis=1).mean(axis=1)
    primary_rng = np.random.default_rng(BOOTSTRAP_SEED)
    summary = {
        "experiment": "M2_FEEDBACK_SITE_SPECIFICITY_V5",
        "status": "COMPLETED_OUTCOME_INFORMED_SOURCE_MODEL_EXPERIMENT",
        "question": "Does sensory-site feedback retain a warm-direction advantage over a mean-run-duration-calibrated motor-only control across imposed sensory-noise scales?",
        "primary": {
            "estimand": "equal-weighted mean of within-seed sensory-site minus motor-only warm-direction-index differences over noise scales",
            "mean": float(pooled_by_seed.mean()),
            "ci95": mean_ci(pooled_by_seed, primary_rng),
            "positive_seed_blocks": int((pooled_by_seed > 0).sum()),
            "n_seed_blocks": len(TEST_SEEDS),
        },
        "calibration": calibration,
        "heldout_by_noise_scale": by_scale,
        "analysis_unit": "simulation seed block; 50 agents clustered within each block",
        "biological_inference": "none; source-model counterfactual only",
        "limitations": [
            "outcome-informed follow-up because earlier M2 model results were inspected",
            "motor-only control is calibrated only on mean forward-run duration",
            "noise scales are imposed by this simulation and are not measured biological boundary conditions",
            "Python implementation parity with the author's MATLAB/Octave implementation was not separately tested",
        ],
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    colors = {"SENSORY_SITE_FB": "#4C78A8", "MOTOR_ONLY_MATCHED": "#F58518", "NO_FEEDBACK": "#777777"}
    for arm in colors:
        ys = [by_scale[str(scale)]["arms"][arm]["warm_direction_index"] for scale in NOISE_SCALES]
        ax.plot(NOISE_SCALES, ys, marker="o", linewidth=2, label=arm.replace("_", " "), color=colors[arm])
    ax.set_xlabel("Imposed sensory-noise multiplier")
    ax.set_ylabel("Warm-direction index (−cos heading)")
    ax.set_title("Feedback-site contrast across noise scales")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig_path = OUT / "feedback_site_noise_robustness.png"
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)

    manifest = {
        "experiment": "M2_FEEDBACK_SITE_SPECIFICITY_V5",
        "development_seeds": [DEV_SEEDS[0], DEV_SEEDS[-1]],
        "heldout_test_seeds": [TEST_SEEDS[0], TEST_SEEDS[-1]],
        "agents_per_block": N_AGENTS,
        "steps_per_trajectory": N_STEPS,
        "noise_scales": list(NOISE_SCALES),
        "motor_only_calibration_grid": list(MOTOR_GRID),
        "selected_motor_feedback": {str(k): v for k, v in selected_motor.items()},
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": N_BOOTSTRAPS,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": matplotlib.__version__},
        "contract_sha256": sha256(CONTRACT),
        "source_archive_sha256": sha256(SOURCE),
        "runner_sha256": sha256(Path(__file__)),
        "runner_file": Path(__file__).name,
        "output_sha256": {p.name: sha256(p) for p in (metrics_path, dev_path, summary_path, fig_path)},
        "heldout_rows": len(test_rows),
        "development_rows": len(dev_rows),
    }
    manifest_path = OUT / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
