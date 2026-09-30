#!/usr/bin/env python3
"""Vectorized translation of Ji et al. (2021) Figure 7 thermotaxis model."""

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
MODEL_DIR = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3"
CONTRACT = ROOT / "summery/M2_JI2021_FEEDBACK_DYNAMICS/M2_JI2021_FEEDBACK_DYNAMICS_CONTRACT.md"
OUT = ROOT / "data/results/M2_JI2021_FEEDBACK_DYNAMICS"

N_STEPS = 1500
T_MAX = 200.0
DT = T_MAX / N_STEPS
N_AGENTS = 50
N_SEED_BLOCKS = 100
FEEDBACK = (-1.0, 0.0, 1.0)
NOISE_SCALES = (0.5, 1.0, 2.0)
N_BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 20260930
MASTER_SEED = 20261001


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def contiguous_run_lengths(mask: np.ndarray) -> list[int]:
    changes = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return (ends - starts).tolist()


def four_sample_smooth(values: np.ndarray) -> np.ndarray:
    """Centered four-sample moving average with truncated, renormalized edges."""
    # MATLAB smooth(y,4) uses a moving average. This explicit convention is
    # documented because edge treatment can differ by MATLAB release.
    n = values.shape[0]
    out = np.empty_like(values)
    for i in range(n):
        lo = max(0, i - 1)
        hi = min(n, i + 3)
        out[i] = values[lo:hi].mean(axis=0)
    return out


def simulate_seed_block(seed: int) -> list[dict[str, float | int]]:
    rng = np.random.default_rng(seed)
    n_noise, n_fb, n_agents = len(NOISE_SCALES), len(FEEDBACK), N_AGENTS
    noise_scales = np.asarray(NOISE_SCALES, dtype=np.float64)[:, None, None]
    feedback = np.asarray(FEEDBACK, dtype=np.float64)[None, :, None]

    # Shared random streams couple all intervention arms and noise scales.
    z = rng.standard_normal((N_STEPS, n_agents))
    heading_reset = rng.random((N_STEPS, n_agents)) * (2.0 * math.pi)
    heading0 = rng.random(n_agents) * (2.0 * math.pi)

    a = np.ones((n_noise, n_fb, n_agents), dtype=np.float64)
    m = np.ones_like(a)
    x = np.zeros_like(a)
    theta = np.broadcast_to(heading0, (n_noise, n_fb, n_agents)).copy()
    m_history = np.empty((N_STEPS, n_noise, n_fb, n_agents), dtype=np.float64)
    x_history = np.empty_like(m_history)
    theta_history = np.empty_like(m_history)
    m_history[0] = m
    x_history[0] = x
    theta_history[0] = theta

    sensory_delay_steps = round(0.5 * N_STEPS / T_MAX)

    for t in range(1, N_STEPS):
        # Source MATLAB logic: compare the last two motor states before updating.
        older_forward = m_history[max(0, t - 2)] >= 0.0
        previous_forward = m_history[t - 1] >= 0.0
        f_to_r = older_forward & ~previous_forward
        r_to_f = ~older_forward & previous_forward
        theta = np.where(f_to_r, np.mod(theta + math.pi, 2.0 * math.pi), theta)
        random_heading = np.broadcast_to(heading_reset[t], theta.shape)
        theta = np.where(r_to_f, random_heading, theta)

        current_x = x_history[t - 1].astype(np.float64)
        lag_index = max(0, (t - 1) - sensory_delay_steps)
        lag_x = x_history[lag_index].astype(np.float64)
        sensory = ((current_x - lag_x) * -1.5) * (m > 0.0)

        noise = 2.0 * noise_scales * z[t][None, None, :]
        da = 1.5 * (
            sensory + 0.5 + noise + feedback * sigmoid(15.0 * m) - a
        ) * DT
        dm = 1.5 * (
            sigmoid(5.0 * (a - 1.5))
            - 0.7 * sigmoid(-5.0 * (a - 1.5))
            - m
        ) * DT
        a = a + da
        m = m + dm
        x = current_x + np.cos(theta) * DT

        m_history[t] = m
        x_history[t] = x
        theta_history[t] = theta

    smoothed_m = four_sample_smooth(m_history)
    records: list[dict[str, float | int]] = []
    for noise_i, noise_scale in enumerate(NOISE_SCALES):
        for fb_i, fb in enumerate(FEEDBACK):
            run_indicator = smoothed_m[:, noise_i, fb_i, :] > 0.0
            angle_index = -np.cos(theta_history[:, noise_i, fb_i, :])
            active = run_indicator.astype(np.float64)
            denominator = active.sum()
            direction_index = float((angle_index * active).sum() / denominator) if denominator else math.nan
            run_durations: list[int] = []
            for agent_i in range(n_agents):
                run_durations.extend(contiguous_run_lengths(run_indicator[:, agent_i]))
            mean_run_s = float(np.mean(run_durations) * DT) if run_durations else math.nan
            warm_displacement = float(-np.mean(x_history[-1, noise_i, fb_i, :]))
            records.append(
                {
                    "seed_block": seed,
                    "noise_scale": noise_scale,
                    "feedback": fb,
                    "warm_direction_index": direction_index,
                    "mean_forward_run_s": mean_run_s,
                    "mean_final_warm_displacement": warm_displacement,
                    "n_agents": n_agents,
                    "n_forward_runs": len(run_durations),
                }
            )
    return records


def bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    n = values.size
    draws = rng.integers(0, n, size=(N_BOOTSTRAPS, n))
    means = values[draws].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def summarize(rows: list[dict[str, float | int]]) -> dict[str, object]:
    index = {(int(r["seed_block"]), float(r["noise_scale"]), float(r["feedback"])): r for r in rows}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    noise_summaries: list[dict[str, object]] = []
    for noise in NOISE_SCALES:
        by_seed: dict[float, dict[int, dict[str, float | int]]] = {}
        for fb in FEEDBACK:
            by_seed[fb] = {
                seed: index[(seed, noise, fb)] for seed in range(MASTER_SEED, MASTER_SEED + N_SEED_BLOCKS)
            }
        contrasts = np.asarray(
            [by_seed[1.0][s]["warm_direction_index"] - by_seed[0.0][s]["warm_direction_index"] for s in by_seed[1.0]],
            dtype=np.float64,
        )
        ci = bootstrap_mean_ci(contrasts, rng)
        arm_means = {}
        for fb in FEEDBACK:
            arm_rows = list(by_seed[fb].values())
            arm_means[str(int(fb))] = {
                "mean_warm_direction_index": float(np.mean([r["warm_direction_index"] for r in arm_rows])),
                "mean_forward_run_s": float(np.mean([r["mean_forward_run_s"] for r in arm_rows])),
                "mean_final_warm_displacement": float(np.mean([r["mean_final_warm_displacement"] for r in arm_rows])),
            }
        noise_summaries.append(
            {
                "noise_scale": noise,
                "arms": arm_means,
                "positive_minus_no_feedback_mean": float(contrasts.mean()),
                "positive_minus_no_feedback_95_ci": list(ci),
                "positive_seed_count": int((contrasts > 0).sum()),
                "seed_blocks": N_SEED_BLOCKS,
            }
        )

    return {
        "status": "COMPLETED_EXPLORATORY_SOURCE_MODEL_REPLICATION",
        "primary": noise_summaries[1],
        "noise_stress": [noise_summaries[0], noise_summaries[2]],
        "all_conditions": noise_summaries,
        "analysis_unit": "simulation_seed_block; 50 simulated agents clustered within each block",
        "interval": f"paired percentile bootstrap across seed blocks; {N_BOOTSTRAPS} resamples",
        "warm_direction_convention": "-cos(heading), following the author code's Tidx_tp definition and kt=-1.5",
        "biological_inference": "simulation output only; not biological population uncertainty",
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, float | int]] = []
    for offset in range(N_SEED_BLOCKS):
        rows.extend(simulate_seed_block(MASTER_SEED + offset))
        if (offset + 1) % 10 == 0:
            print(f"completed {offset + 1}/{N_SEED_BLOCKS} paired seed blocks", flush=True)

    metrics_path = OUT / "simulation_metrics.csv"
    with metrics_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    colors = {0.5: "#4C78A8", 1.0: "#F58518", 2.0: "#54A24B"}
    for noise in NOISE_SCALES:
        for fb in FEEDBACK:
            vals = [float(r["warm_direction_index"]) for r in rows if r["noise_scale"] == noise and r["feedback"] == fb]
            ax.errorbar(
                fb + (noise - 1.0) * 0.12,
                np.mean(vals),
                yerr=np.std(vals, ddof=1) / math.sqrt(len(vals)),
                marker="o",
                color=colors[noise],
                capsize=3,
                label=f"noise ×{noise:g}" if fb == -1.0 else None,
            )
    ax.set_xticks(FEEDBACK, ["negative (−1)", "none (0)", "positive (+1)"])
    ax.set_ylabel("Warm-direction index (−cos heading; forward samples)")
    ax.set_xlabel("Motor-to-interneuron feedback coefficient")
    ax.set_title("Source-model navigation outcome across feedback signs")
    ax.legend(frameon=False)
    ax.axhline(0.0, color="0.5", linewidth=0.8)
    fig.tight_layout()
    figure_path = OUT / "feedback_noise_sweep.png"
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    manifest = {
        "experiment": "M2_JI2021_FEEDBACK_DYNAMICS",
        "master_seed": MASTER_SEED,
        "seed_blocks": N_SEED_BLOCKS,
        "agents_per_block": N_AGENTS,
        "steps": N_STEPS,
        "feedback_coefficients": list(FEEDBACK),
        "noise_scales": list(NOISE_SCALES),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": N_BOOTSTRAPS,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": matplotlib.__version__},
        "input_sha256": sha256(RAW_DIR / "elife-68848-fig7-data1.zip"),
        "extracted_author_script_sha256": sha256(RAW_DIR / "Fig7_TtxCircuitModel.m"),
        "contract_sha256": sha256(CONTRACT),
        "runner_sha256": sha256(Path(__file__)),
        "outputs_sha256": {
            "simulation_metrics.csv": sha256(metrics_path),
            "summary.json": sha256(summary_path),
            "feedback_noise_sweep.png": sha256(figure_path),
        },
        "row_count": len(rows),
        "scope": "post-result exploratory computational replication/stress test; not biological validation or AI transfer",
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary["primary"], indent=2))


if __name__ == "__main__":
    main()
