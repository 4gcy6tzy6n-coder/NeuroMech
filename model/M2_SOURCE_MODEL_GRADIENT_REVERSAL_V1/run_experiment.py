#!/usr/bin/env python3
"""Run a source-derived Ji et al. thermotaxis model under gradient reversals."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(__file__).resolve().parent
CONTRACT = ROOT / "summery/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/CONTRACT.md"
SOURCE = ROOT / "model/M2_FEEDBACK_SITE_SPECIFICITY_V5/source_model.py"
AUTHOR_SOURCE = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m"
DEFAULT_OUT = ROOT / "data/results/M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1/canonical"

N_STEPS = 1500
T_MAX = 200.0
DT = T_MAX / N_STEPS
N_AGENTS = 50
SEEDS = tuple(range(20261014, 20261114))
REVERSAL_INTERVALS = (0.0, 40.0, 20.0, 10.0, 5.0)
ARMS = (
    ("SENSORY_SITE_FB", 1.0, 0.0),
    ("OUTPUT_SITE_FB", 0.0, 1.0),
    ("NO_FEEDBACK", 0.0, 0.0),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def smooth_forward(m_history: np.ndarray) -> np.ndarray:
    out = np.empty_like(m_history)
    for t in range(m_history.shape[0]):
        out[t] = m_history[max(0, t - 1):min(m_history.shape[0], t + 3)].mean(axis=0)
    return out > 0.0


def contiguous_lengths(mask: np.ndarray) -> list[int]:
    changes = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return (ends - starts).tolist()


def simulate(seed: int) -> list[dict[str, float | int | str]]:
    rng = np.random.default_rng(seed)
    conditions = [(arm, si, mi, interval)
                  for interval in REVERSAL_INTERVALS
                  for arm, si, mi in ARMS]
    n_conditions = len(conditions)
    sensory_fb = np.asarray([c[1] for c in conditions])[:, None]
    motor_fb = np.asarray([c[2] for c in conditions])[:, None]
    intervals = np.asarray([c[3] for c in conditions])[:, None]

    # Shared streams preserve paired comparisons across arms and schedules.
    z = rng.standard_normal((N_STEPS, N_AGENTS))
    heading_reset = rng.random((N_STEPS, N_AGENTS)) * (2.0 * np.pi)
    heading0 = rng.random(N_AGENTS) * (2.0 * np.pi)
    a = np.ones((n_conditions, N_AGENTS), dtype=np.float64)
    m = np.ones_like(a)
    theta = np.broadcast_to(heading0, (n_conditions, N_AGENTS)).copy()
    x_history = np.zeros((N_STEPS, n_conditions, N_AGENTS), dtype=np.float64)
    m_history = np.empty_like(x_history)
    theta_history = np.empty_like(x_history)
    m_history[0] = m
    theta_history[0] = theta
    delay_steps = round(0.5 * N_STEPS / T_MAX)
    time = np.arange(N_STEPS) * DT
    warm_sign = np.ones((N_STEPS, n_conditions), dtype=np.float64)
    for ci, interval in enumerate(np.asarray([c[3] for c in conditions])):
        if interval > 0.0:
            warm_sign[:, ci] = np.where(np.floor(time / interval).astype(int) % 2 == 0, 1.0, -1.0)

    for t in range(1, N_STEPS):
        old_forward = m_history[max(0, t - 2)] >= 0.0
        previous_forward = m_history[t - 1] >= 0.0
        f_to_r = old_forward & ~previous_forward
        r_to_f = ~old_forward & previous_forward
        theta = np.where(f_to_r, np.mod(theta + np.pi, 2.0 * np.pi), theta)
        theta = np.where(r_to_f, heading_reset[t][None, :], theta)

        x_now = x_history[t - 1]
        x_then = x_history[max(0, t - delay_steps)]
        sensory = ((x_now - x_then) * (-1.5 * warm_sign[t, :, None])) * (m > 0.0)
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
        x_history[t] = x_now + np.cos(theta) * DT
        m_history[t] = m
        theta_history[t] = theta

    forward = smooth_forward(m_history)
    delta_x = np.diff(x_history, axis=0, prepend=x_history[[0]])
    records: list[dict[str, float | int | str]] = []
    reversal_steps = {}
    for interval in REVERSAL_INTERVALS:
        if interval == 0.0:
            reversal_steps[interval] = []
        else:
            reversal_steps[interval] = [int(round(t / DT)) for t in np.arange(interval, T_MAX, interval)]

    for ci, (arm, _, _, interval) in enumerate(conditions):
        local_progress = -warm_sign[:, ci, None] * delta_x[:, ci, :]
        durations: list[int] = []
        for agent in range(N_AGENTS):
            durations.extend(contiguous_lengths(forward[:, ci, agent]))
        lag_values = []
        max_window = max(1, int(round(10.0 / DT)))
        for switch in reversal_steps[interval]:
            stop = min(N_STEPS, switch + max_window)
            for agent in range(N_AGENTS):
                segment = local_progress[switch:stop, agent]
                if len(segment) < 3:
                    continue
                recovered = None
                for offset in range(len(segment) - 2):
                    if np.all(segment[offset:offset + 3] > 0.0):
                        recovered = offset
                        break
                lag_values.append(float(recovered * DT) if recovered is not None else float("nan"))

        finite_lags = np.asarray(lag_values, dtype=np.float64)
        finite_lags = finite_lags[np.isfinite(finite_lags)]
        records.append({
            "seed_block": seed,
            "reversal_interval_s": interval,
            "arm": arm,
            "aligned_progress_rate": float(local_progress.sum() / (N_AGENTS * T_MAX)),
            "forward_occupancy": float(forward[:, ci, :].mean()),
            "mean_forward_run_s": float(np.mean(durations) * DT) if durations else float("nan"),
            "p90_forward_run_s": float(np.quantile(durations, 0.90) * DT) if durations else float("nan"),
            "mean_switch_recovery_lag_s": float(finite_lags.mean()) if finite_lags.size else float("nan"),
            "recovery_observations": int(finite_lags.size),
            "n_agents": N_AGENTS,
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.output_dir.expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, float | int | str]] = []
    for index, seed in enumerate(SEEDS, start=1):
        rows.extend(simulate(seed))
        if index % 10 == 0:
            print(f"completed gradient-reversal seed block {index}/{len(SEEDS)}", flush=True)

    csv_path = out / "seed_block_metrics.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    inputs = [
        CONTRACT, SOURCE, AUTHOR_SOURCE,
        MODEL_DIR / "run_experiment.py",
        MODEL_DIR / "analyze_results.py",
        MODEL_DIR / "verify_results.py",
    ]
    manifest = {
        "experiment_id": "M2_SOURCE_MODEL_GRADIENT_REVERSAL_V1",
        "classification": "exploratory_source_derived_computational_stress_test",
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
        "n_steps": N_STEPS,
        "t_max_s": T_MAX,
        "dt_s": DT,
        "n_agents_per_seed_block": N_AGENTS,
        "seed_blocks": [SEEDS[0], SEEDS[-1]],
        "reversal_intervals_s": list(REVERSAL_INTERVALS),
        "arms": [c[0] for c in ARMS],
        "rows": len(rows),
        "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in inputs},
        "output_sha256": {csv_path.name: sha256(csv_path)},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
