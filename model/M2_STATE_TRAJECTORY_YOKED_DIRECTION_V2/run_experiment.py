#!/usr/bin/env python3
"""Replay intact development motor-state sequences independently of test context."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import source_model as model

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "summery/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/CONTRACT.md"
AUTHOR_SOURCE = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m"
V5_SUMMARY = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5/summary.json"
OUT = ROOT / "data/results/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/final"
SCALES = (0.75, 1.00, 1.25)
DEV_SEEDS = range(370000, 370030)
TEST_SEEDS = range(380000, 380200)
MOTOR_COEFFICIENTS = {0.75: 0.760, 1.00: 0.665, 1.25: 0.610}
N_BOOT = 20_000
BOOT_SEED = 20261007
YOKE_OFFSET = 900_000_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def bouts(mask: np.ndarray) -> list[int]:
    changes = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return (ends - starts).tolist()


def trajectory_yoke(seed: int, scale: float, library: list[dict[str, list[list[int]]]]) -> dict[str, object]:
    steps, agents, dt = model.N_STEPS, model.N_AGENTS, model.DT
    donor_rng = np.random.default_rng(seed + YOKE_OFFSET + int(scale * 1000))
    schedule = np.zeros((steps, agents), dtype=bool)
    latent_mode = np.zeros((steps, agents), dtype=bool)
    for agent in range(agents):
        donor = library[int(donor_rng.integers(0, len(library)))]
        for key, target in (("movement", schedule), ("latent_mode", latent_mode)):
            sequence = donor[key]
            if sum(length for _, length in sequence) != steps:
                raise ValueError(f"development {key} sequence has an invalid length")
            cursor = 0
            for state, length in sequence:
                target[cursor:cursor + length, agent] = bool(state)
                cursor += length

    # Match the source model's random stream consumption for heading resets and starts.
    heading_rng = np.random.default_rng(seed)
    heading_rng.standard_normal((steps, agents))
    reset = heading_rng.random((steps, agents)) * (2.0 * math.pi)
    theta0 = heading_rng.random(agents) * (2.0 * math.pi)
    theta = np.empty((steps, agents), dtype=float)
    theta[0] = theta0
    for t in range(1, steps):
        old_forward = latent_mode[max(0, t - 2)]
        previous_forward = latent_mode[t - 1]
        f_to_r = old_forward & ~previous_forward
        r_to_f = ~old_forward & previous_forward
        theta[t] = theta[t - 1]
        theta[t, f_to_r] = np.mod(theta[t, f_to_r] + math.pi, 2.0 * math.pi)
        theta[t, r_to_f] = reset[t, r_to_f]

    forward_lengths = [length for agent in range(agents) for length in bouts(schedule[:, agent])]
    reverse_lengths = [length for agent in range(agents) for length in bouts(~schedule[:, agent])]
    n_forward = int(schedule.sum())
    direction = float((-np.cos(theta) * schedule).sum() / n_forward) if n_forward else math.nan
    return {
        "seed_block": seed, "arm": "FULL_TRAJECTORY_YOKE", "noise_scale": scale,
        "sensory_site_feedback": 0.0, "motor_only_feedback": 0.0,
        "warm_direction_index": direction,
        "mean_forward_run_s": float(np.mean(forward_lengths) * dt),
        "median_forward_run_s": float(np.median(forward_lengths) * dt),
        "p90_forward_run_s": float(np.quantile(forward_lengths, 0.90) * dt),
        "fraction_forward_runs_ge_30s": float(np.mean(np.asarray(forward_lengths) * dt >= 30.0)),
        "forward_occupancy": float(n_forward / (steps * agents)),
        "mean_final_warm_displacement": float(-np.cos(theta).sum(axis=0).mean() * dt),
        "n_agents": agents, "n_forward_runs": len(forward_lengths),
        "mean_reverse_run_s": float(np.mean(reverse_lengths) * dt),
        "median_reverse_run_s": float(np.median(reverse_lengths) * dt),
        "p90_reverse_run_s": float(np.quantile(reverse_lengths, 0.90) * dt),
        "n_reverse_runs": len(reverse_lengths),
    }


def bootstrap_ci(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    means = values[idx].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    library_by_scale: dict[str, list[dict[str, list[list[int]]]]] = {str(s): [] for s in SCALES}
    development = []
    for seed in DEV_SEEDS:
        for scale in SCALES:
            row = model.run(seed, [("SENSORY_SITE_FB", 1.0, 0.0, scale)], capture_sequences=True)[0]
            trajectories = row["ordered_motor_sequences"]
            library = library_by_scale[str(scale)]
            latent_sequences = row["ordered_latent_mode_sequences"]
            library.extend([
                {"movement": movement, "latent_mode": latent}
                for movement, latent in zip(trajectories, latent_sequences)
            ])
            development.append({
                "seed_block": seed, "noise_scale": scale, "n_donor_trajectories": len(trajectories),
                "mean_bouts_per_trajectory": float(np.mean([len(x) for x in trajectories])),
                "mean_forward_occupancy": float(np.mean([sum(length for state, length in x if state) / model.N_STEPS for x in trajectories])),
            })
    if any(not library for library in library_by_scale.values()):
        raise RuntimeError("development trajectory library is empty")
    write_csv(OUT / "development_summary.csv", development)
    (OUT / "development_trajectory_library.json").write_text(json.dumps(library_by_scale, separators=(",", ":")) + "\n")

    conditions = []
    for scale in SCALES:
        conditions.extend([
            ("SENSORY_SITE_FB", 1.0, 0.0, scale),
            ("MOTOR_MULTI_STAT_MATCHED", 0.0, MOTOR_COEFFICIENTS[scale], scale),
            ("NO_FEEDBACK", 0.0, 0.0, scale),
        ])
    rows = []
    for i, seed in enumerate(TEST_SEEDS, 1):
        rows.extend(model.run(seed, conditions))
        for scale in SCALES:
            rows.append(trajectory_yoke(seed, scale, library_by_scale[str(scale)]))
        if i % 25 == 0:
            print(f"held-out seed blocks {i}/{len(TEST_SEEDS)}", flush=True)
    write_csv(OUT / "heldout_metrics.csv", rows)
    lookup = {(int(r["seed_block"]), float(r["noise_scale"]), str(r["arm"])): r for r in rows}
    per_scale = {}
    seed_differences = []
    for scale in SCALES:
        differences = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "FULL_TRAJECTORY_YOKE")]["warm_direction_index"])
            for seed in TEST_SEEDS
        ])
        seed_differences.append(differences)
        metrics = ("mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s",
                   "fraction_forward_runs_ge_30s", "forward_occupancy", "n_forward_runs")
        persistence = {
            metric: float(np.mean([
                float(lookup[(seed, scale, "SENSORY_SITE_FB")][metric])
                - float(lookup[(seed, scale, "FULL_TRAJECTORY_YOKE")][metric])
                for seed in TEST_SEEDS
            ])) for metric in metrics
        }
        per_scale[str(scale)] = {
            "sensory_minus_trajectory_yoke_direction": {
                "mean": float(differences.mean()), "ci95_seed_block_bootstrap": bootstrap_ci(differences),
                "positive_blocks": int((differences > 0).sum()), "n_seed_blocks": len(TEST_SEEDS),
            },
            "sensory_minus_yoke_persistence_summary_means": persistence,
        }
    pooled = np.stack(seed_differences, axis=1).mean(axis=1)
    summary = {
        "experiment": "M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2",
        "classification": "RETROSPECTIVE_EXPLORATORY_SOURCE_MODEL_ANALYSIS",
        "primary": {
            "estimand": "equal-weighted within-seed SENSORY_SITE_FB minus FULL_TRAJECTORY_YOKE warm-direction index across noise scales",
            "mean": float(pooled.mean()), "ci95_seed_block_bootstrap": bootstrap_ci(pooled),
            "positive_seed_blocks": int((pooled > 0).sum()), "n_seed_blocks": len(TEST_SEEDS),
        },
        "by_noise_scale": per_scale,
        "analysis_unit": "simulation seed block; 50 agents and 1500 timesteps are clustered",
        "yoke": "each held-out agent replays one complete ordered forward/reverse motor-state sequence from an independent development sensory-site trajectory; donor choice is independent of test position, heading, and direction outcome",
        "limitations": [
            "prior M2 source-model outcomes were known; this is retrospective and not confirmatory",
            "sequence replay preserves each donor trajectory's ordered bout pattern, not all conditional motor statistics across test environments",
            "reported persistence summaries are descriptive and no equivalence margin was frozen",
            "a sensory-minus-yoke contrast would show that replayed motor state alone is insufficient in this source model, not identify a unique synapse or biological mechanism",
            "simulation seed blocks are not animals; no new biological validation or AI-transfer evidence is produced",
            "the source-model translation has not been validated by end-to-end MATLAB/Octave numerical parity",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {
        "experiment": summary["experiment"], "classification": summary["classification"],
        "development_seeds": [min(DEV_SEEDS), max(DEV_SEEDS)],
        "heldout_seeds": [min(TEST_SEEDS), max(TEST_SEEDS)], "noise_scales": list(SCALES),
        "n_donor_trajectories_per_scale": len(library_by_scale[str(SCALES[0])]),
        "n_bootstrap_draws": N_BOOT, "bootstrap_seed": BOOT_SEED, "yoke_seed_offset": YOKE_OFFSET,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "inputs_sha256": {"contract": sha256(CONTRACT), "source_model": sha256(Path(model.__file__)),
                          "runner": sha256(Path(__file__).resolve()),
                          "author_source": sha256(AUTHOR_SOURCE), "v5_summary": sha256(V5_SUMMARY)},
        "outputs_sha256": {p.name: sha256(p) for p in OUT.iterdir() if p.is_file() and p.name != "run_manifest.json"},
        "heldout_rows": len(rows),
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary["primary"], indent=2))


if __name__ == "__main__":
    main()
