#!/usr/bin/env python3
"""Run the source-derived M2 self-contingent versus cross-agent yoke probe."""
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
CONTRACT = ROOT / "summery/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/CONTRACT.md"
SOURCE = ROOT / "model/M2_FEEDBACK_SITE_SPECIFICITY_V5/source_model.py"
AUTHOR_SOURCE = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m"
DEFAULT_OUT = ROOT / "data/results/M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1/canonical"

N_STEPS = 1500
T_MAX = 200.0
DT = T_MAX / N_STEPS
N_AGENTS = 50
SEEDS = tuple(range(20261016, 20261116))
REVERSAL_INTERVALS = (0.0, 40.0, 20.0, 10.0, 5.0)
ARMS = ("SELF_CONTINGENT", "CROSS_AGENT_YOKED", "NO_FEEDBACK")
YOKE_OFFSET = 870_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -40.0, 40.0)))


def forward_mask(m_history: np.ndarray) -> np.ndarray:
    smoothed = np.empty_like(m_history)
    for t in range(m_history.shape[0]):
        smoothed[t] = m_history[max(0, t - 1):min(m_history.shape[0], t + 3)].mean(axis=0)
    return smoothed > 0.0


def random_derangement(seed: int, interval: float) -> np.ndarray:
    rng = np.random.default_rng(seed + YOKE_OFFSET + int(interval * 100))
    while True:
        mapping = rng.permutation(N_AGENTS)
        if np.all(mapping != np.arange(N_AGENTS)):
            return mapping


def simulate(seed: int, interval: float) -> tuple[list[dict[str, object]], dict[str, object]]:
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal((N_STEPS, N_AGENTS))
    heading_reset = rng.random((N_STEPS, N_AGENTS)) * (2.0 * np.pi)
    heading0 = rng.random(N_AGENTS) * (2.0 * np.pi)
    time = np.arange(N_STEPS) * DT
    warm_sign = (np.ones(N_STEPS) if interval == 0.0 else
                 np.where(np.floor(time / interval).astype(int) % 2 == 0, 1.0, -1.0))

    def run(feedback: np.ndarray | None, capture_feedback: bool = False):
        a = np.ones(N_AGENTS, dtype=np.float64)
        m = np.ones(N_AGENTS, dtype=np.float64)
        theta = heading0.copy()
        x_history = np.zeros((N_STEPS, N_AGENTS), dtype=np.float64)
        m_history = np.empty_like(x_history)
        m_history[0] = m
        feedback_history = np.empty_like(x_history) if capture_feedback else None
        if feedback_history is not None:
            feedback_history[0] = sigmoid(15.0 * m)
        delay_steps = round(0.5 * N_STEPS / T_MAX)

        for t in range(1, N_STEPS):
            old_forward = m_history[max(0, t - 2)] >= 0.0
            previous_forward = m_history[t - 1] >= 0.0
            f_to_r = old_forward & ~previous_forward
            r_to_f = ~old_forward & previous_forward
            theta = np.where(f_to_r, np.mod(theta + np.pi, 2.0 * np.pi), theta)
            theta = np.where(r_to_f, heading_reset[t], theta)

            own_signal = sigmoid(15.0 * m)
            if feedback_history is not None:
                feedback_history[t] = own_signal
            sensory_feedback = own_signal if feedback is None else feedback[t]
            x_now = x_history[t - 1]
            x_then = x_history[max(0, t - delay_steps)]
            sensory = ((x_now - x_then) * (-1.5 * warm_sign[t])) * (m > 0.0)
            da = 1.5 * (sensory + 0.5 + 2.0 * noise[t] + sensory_feedback - a) * DT
            dm = 1.5 * (
                sigmoid(5.0 * (a - 1.5))
                - 0.7 * sigmoid(-5.0 * (a - 1.5))
                - m
            ) * DT
            a += da
            m += dm
            x_history[t] = x_now + np.cos(theta) * DT
            m_history[t] = m

        return x_history, m_history, feedback_history

    self_x, self_m, self_feedback = run(feedback=None, capture_feedback=True)
    donor_map = random_derangement(seed, interval)
    yoke_drive = self_feedback[:, donor_map]
    yoke_x, yoke_m, _ = run(feedback=yoke_drive)
    no_x, no_m, _ = run(feedback=np.zeros((N_STEPS, N_AGENTS), dtype=np.float64))
    trajectories = {
        "SELF_CONTINGENT": (self_x, self_m),
        "CROSS_AGENT_YOKED": (yoke_x, yoke_m),
        "NO_FEEDBACK": (no_x, no_m),
    }

    rows = []
    for arm, (x_history, m_history) in trajectories.items():
        delta_x = np.diff(x_history, axis=0, prepend=x_history[[0]])
        local_progress = -warm_sign[:, None] * delta_x
        mask = forward_mask(m_history)
        run_lengths = []
        for agent in range(N_AGENTS):
            changes = np.diff(np.pad(mask[:, agent].astype(np.int8), (1, 1)))
            starts = np.flatnonzero(changes == 1)
            ends = np.flatnonzero(changes == -1)
            run_lengths.extend((ends - starts).tolist())
        rows.append({
            "seed_block": seed,
            "reversal_interval_s": interval,
            "arm": arm,
            "aligned_progress_rate": float(local_progress.sum() / (N_AGENTS * T_MAX)),
            "forward_occupancy": float(mask.mean()),
            "mean_forward_run_s": float(np.mean(run_lengths) * DT) if run_lengths else float("nan"),
            "p90_forward_run_s": float(np.quantile(run_lengths, 0.90) * DT) if run_lengths else float("nan"),
            "n_agents": N_AGENTS,
        })

    marginal_equal = np.array_equal(np.sort(self_feedback, axis=1), np.sort(yoke_drive, axis=1))
    max_marginal_error = float(np.max(np.abs(
        np.sort(self_feedback, axis=1) - np.sort(yoke_drive, axis=1)
    )))
    check = {
        "seed_block": seed,
        "reversal_interval_s": interval,
        "donor_mapping_is_derangement": bool(np.all(donor_map != np.arange(N_AGENTS))),
        "instantaneous_population_feedback_distribution_exact": bool(marginal_equal),
        "max_sorted_feedback_value_difference": max_marginal_error,
    }
    return rows, check


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.output_dir.expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    checks: list[dict[str, object]] = []
    for index, seed in enumerate(SEEDS, start=1):
        for interval in REVERSAL_INTERVALS:
            seed_rows, check = simulate(seed, interval)
            rows.extend(seed_rows)
            checks.append(check)
        if index % 10 == 0:
            print(f"completed seed blocks {index}/{len(SEEDS)}", flush=True)

    metrics_path = out / "seed_block_metrics.csv"
    with metrics_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    check_path = out / "feedback_distribution_check.json"
    check_path.write_text(json.dumps({"checks": checks}, indent=2) + "\n")
    manifest = {
        "experiment_id": "M2_SELF_VS_YOKED_SENSORY_FEEDBACK_V1",
        "classification": "retrospective_exploratory_source_model_mechanism_probe",
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
        "n_steps": N_STEPS,
        "t_max_s": T_MAX,
        "dt_s": DT,
        "n_agents_per_seed_block": N_AGENTS,
        "seed_blocks": [SEEDS[0], SEEDS[-1]],
        "reversal_intervals_s": list(REVERSAL_INTERVALS),
        "arms": list(ARMS),
        "rows": len(rows),
        "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in (
            CONTRACT, SOURCE, AUTHOR_SOURCE, MODEL_DIR / "run_experiment.py",
            MODEL_DIR / "analyze_results.py", MODEL_DIR / "verify_results.py",
        )},
        "output_sha256": {
            metrics_path.name: sha256(metrics_path),
            check_path.name: sha256(check_path),
        },
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
