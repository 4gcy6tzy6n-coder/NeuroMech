#!/usr/bin/env python3
"""Compare corrected M2 feedback with full motor-state trajectory replay."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import platform
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE_MODEL = ROOT / "model/M2_STATE_TRAJECTORY_REPLAY_V1/source_model.py"
AUTHOR_SOURCE = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m"
CONTRACT = ROOT / "summery/M2_STATE_TRAJECTORY_REPLAY_V1/CONTRACT.md"
V5_SUMMARY = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5/summary.json"
OUT_DEFAULT = ROOT / "data/results/M2_STATE_TRAJECTORY_REPLAY_V1"
NOISE_SCALES = (0.75, 1.00, 1.25)
DEV_SEEDS = range(370000, 370040)
TEST_SEEDS = range(380000, 380200)
MOTOR_COEFFICIENTS = {0.75: 0.760, 1.00: 0.665, 1.25: 0.610}
N_BOOT = 20_000
BOOT_SEED = 20261007
REPLAY_SEED_OFFSET = 900_000_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def lengths(mask: np.ndarray) -> list[int]:
    change = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    starts, ends = np.flatnonzero(change == 1), np.flatnonzero(change == -1)
    return (ends - starts).tolist()


def replay(seed: int, scale: float, packed_library: list[list[int]], model) -> dict[str, object]:
    n_steps, n_agents, dt = model.N_STEPS, model.N_AGENTS, model.DT
    # Preserve the source model's per-seed initial and reset headings.
    heading_rng = np.random.default_rng(seed)
    heading_rng.standard_normal((n_steps, n_agents))
    heading_reset = heading_rng.random((n_steps, n_agents)) * (2.0 * math.pi)
    heading0 = heading_rng.random(n_agents) * (2.0 * math.pi)

    replay_rng = np.random.default_rng(seed + REPLAY_SEED_OFFSET + int(scale * 1000))
    picks = replay_rng.integers(0, len(packed_library), size=n_agents)
    forward = np.empty((n_steps, n_agents), dtype=bool)
    for agent, pick in enumerate(picks):
        packed = np.asarray(packed_library[int(pick)], dtype=np.uint8)
        forward[:, agent] = np.unpackbits(packed, count=n_steps, bitorder="little").astype(bool)

    theta = np.empty((n_steps, n_agents), dtype=float)
    theta[0] = heading0
    for t in range(1, n_steps):
        f_to_r = forward[t - 1] & ~forward[t]
        r_to_f = ~forward[t - 1] & forward[t]
        theta[t] = theta[t - 1]
        theta[t, f_to_r] = np.mod(theta[t, f_to_r] + math.pi, 2.0 * math.pi)
        theta[t, r_to_f] = heading_reset[t, r_to_f]

    forward_lengths = [n for agent in range(n_agents) for n in lengths(forward[:, agent])]
    reverse_lengths = [n for agent in range(n_agents) for n in lengths(~forward[:, agent])]
    active = int(forward.sum())
    direction = float((-np.cos(theta) * forward).sum() / active) if active else math.nan
    return {
        "seed_block": seed, "arm": "FULL_TRAJECTORY_REPLAY", "noise_scale": scale,
        "sensory_site_feedback": 0.0, "motor_only_feedback": 0.0,
        "warm_direction_index": direction,
        "mean_forward_run_s": float(np.mean(forward_lengths) * dt),
        "median_forward_run_s": float(np.median(forward_lengths) * dt),
        "p90_forward_run_s": float(np.quantile(forward_lengths, .90) * dt),
        "fraction_forward_runs_ge_30s": float(np.mean(np.asarray(forward_lengths) * dt >= 30.0)),
        "forward_occupancy": float(active / (n_steps * n_agents)),
        "mean_final_warm_displacement": -float(np.cos(theta).sum(axis=0).mean() * dt),
        "n_agents": n_agents, "n_forward_runs": len(forward_lengths),
        "mean_reverse_run_s": float(np.mean(reverse_lengths) * dt),
        "median_reverse_run_s": float(np.median(reverse_lengths) * dt),
        "p90_reverse_run_s": float(np.quantile(reverse_lengths, .90) * dt),
        "n_reverse_runs": len(reverse_lengths),
    }


def bootstrap_ci(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    means = values[idx].mean(axis=1)
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    out = parser.parse_args().output_dir.expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    spec = importlib.util.spec_from_file_location("m2_full_trajectory_source", SOURCE_MODEL)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import corrected source model")
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)

    mode_library = {str(scale): [] for scale in NOISE_SCALES}
    development: list[dict[str, object]] = []
    for i, seed in enumerate(DEV_SEEDS, 1):
        for scale in NOISE_SCALES:
            row = model.run(seed, [("SENSORY_SITE_FB", 1.0, 0.0, scale)], capture_modes=True)[0]
            mode_library[str(scale)].extend(row["forward_mode_packed_by_agent"])
            development.append({k: row[k] for k in (
                "seed_block", "arm", "noise_scale", "forward_occupancy", "n_forward_runs", "n_reverse_runs"
            )})
        if i % 10 == 0:
            print(f"development seed blocks {i}/{len(DEV_SEEDS)}", flush=True)
    dev_path = out / "development_modes_summary.csv"
    write_csv(dev_path, development)
    library_path = out / "development_mode_trace_library.json"
    library_path.write_text(json.dumps(mode_library, separators=(",", ":")) + "\n")

    conditions = []
    for scale in NOISE_SCALES:
        conditions.extend([
            ("SENSORY_SITE_FB", 1.0, 0.0, scale),
            ("MOTOR_MULTI_STAT_MATCHED", 0.0, MOTOR_COEFFICIENTS[scale], scale),
            ("NO_FEEDBACK", 0.0, 0.0, scale),
        ])
    heldout: list[dict[str, object]] = []
    for i, seed in enumerate(TEST_SEEDS, 1):
        heldout.extend(model.run(seed, conditions))
        for scale in NOISE_SCALES:
            heldout.append(replay(seed, scale, mode_library[str(scale)], model))
        if i % 25 == 0:
            print(f"held-out seed blocks {i}/{len(TEST_SEEDS)}", flush=True)
    metrics_path = out / "heldout_metrics.csv"
    write_csv(metrics_path, heldout)

    lookup = {(int(r["seed_block"]), float(r["noise_scale"]), str(r["arm"])): r for r in heldout}
    by_scale: dict[str, object] = {}
    replay_diffs, scalar_diffs = [], []
    for scale in NOISE_SCALES:
        d_replay = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "FULL_TRAJECTORY_REPLAY")]["warm_direction_index"])
            for seed in TEST_SEEDS
        ])
        d_scalar = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "MOTOR_MULTI_STAT_MATCHED")]["warm_direction_index"])
            for seed in TEST_SEEDS
        ])
        replay_diffs.append(d_replay)
        scalar_diffs.append(d_scalar)
        arms = {}
        for arm in ("SENSORY_SITE_FB", "MOTOR_MULTI_STAT_MATCHED", "FULL_TRAJECTORY_REPLAY", "NO_FEEDBACK"):
            cell = [r for r in heldout if r["arm"] == arm and float(r["noise_scale"]) == scale]
            metrics = ("warm_direction_index", "mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s",
                       "fraction_forward_runs_ge_30s", "forward_occupancy", "mean_final_warm_displacement", "n_forward_runs",
                       "mean_reverse_run_s", "median_reverse_run_s", "p90_reverse_run_s", "n_reverse_runs")
            arms[arm] = {m: float(np.mean([float(r[m]) for r in cell])) for m in metrics if m in cell[0]}
        persistence = {}
        for metric in ("mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s", "fraction_forward_runs_ge_30s",
                       "forward_occupancy", "mean_reverse_run_s", "median_reverse_run_s", "p90_reverse_run_s"):
            persistence[metric] = float(np.mean([
                float(lookup[(seed, scale, "SENSORY_SITE_FB")][metric])
                - float(lookup[(seed, scale, "FULL_TRAJECTORY_REPLAY")][metric])
                for seed in TEST_SEEDS
            ]))
        by_scale[str(scale)] = {
            "arms": arms,
            "sensory_minus_replay_direction": {"mean": float(d_replay.mean()), "ci95": bootstrap_ci(d_replay), "positive_blocks": int((d_replay > 0).sum())},
            "sensory_minus_scalar_direction": {"mean": float(d_scalar.mean()), "ci95": bootstrap_ci(d_scalar), "positive_blocks": int((d_scalar > 0).sum())},
            "sensory_minus_replay_persistence_summary_means": persistence,
        }

    pooled_replay = np.stack(replay_diffs, axis=1).mean(axis=1)
    pooled_scalar = np.stack(scalar_diffs, axis=1).mean(axis=1)
    summary = {
        "experiment": "M2_STATE_TRAJECTORY_REPLAY_V1",
        "classification": "RETROSPECTIVE_EXPLORATORY_SOURCE_MODEL_ANALYSIS",
        "primary": {"estimand": "equal-weighted within-seed sensory-site minus full-trajectory-replay warm-direction index over noise scales",
                    "mean": float(pooled_replay.mean()), "ci95_seed_block_bootstrap": bootstrap_ci(pooled_replay),
                    "positive_seed_blocks": int((pooled_replay > 0).sum()), "n_seed_blocks": len(TEST_SEEDS)},
        "secondary_scalar_control": {"mean": float(pooled_scalar.mean()), "ci95_seed_block_bootstrap": bootstrap_ci(pooled_scalar),
                                      "positive_seed_blocks": int((pooled_scalar > 0).sum())},
        "heldout_by_noise_scale": by_scale,
        "analysis_unit": "simulation seed block; agents and timesteps are clustered",
        "replay_definition": "complete development sensory-site binary motor-state sequences sampled independently of held-out position and heading",
        "limitations": [
            "previous M2/V3/V4/V5 and V1 yoke results were known; retrospective and exploratory",
            "development replay controls marginal sequence distribution but not held-out position-, heading-, or temperature-conditional motor-state timing",
            "no equivalence bounds were frozen; held-out persistence summaries are descriptive and adequacy is not a pass/fail claim",
            "source-model uncertainty is not animal-level evidence; no biological validation or AI transfer",
            "corrected delay index is source-code audited, but MATLAB/Octave execution parity remains unverified",
        ],
    }
    summary_path = out / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {
        "experiment": "M2_STATE_TRAJECTORY_REPLAY_V1",
        "development_seed_range": [min(DEV_SEEDS), max(DEV_SEEDS)], "heldout_seed_range": [min(TEST_SEEDS), max(TEST_SEEDS)],
        "noise_scales": list(NOISE_SCALES), "agents_per_block": model.N_AGENTS, "steps_per_trajectory": model.N_STEPS,
        "bootstrap_resamples": N_BOOT, "bootstrap_seed": BOOT_SEED, "replay_seed_offset": REPLAY_SEED_OFFSET,
        "motor_coefficients_from_v5": {str(k): v for k,v in MOTOR_COEFFICIENTS.items()},
        "inputs": {"contract_sha256": sha256(CONTRACT), "source_model_sha256": sha256(SOURCE_MODEL),
                   "runner_sha256": sha256(Path(__file__).resolve()), "author_matlab_sha256": sha256(AUTHOR_SOURCE),
                   "v5_summary_sha256": sha256(V5_SUMMARY)},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__}, "heldout_rows": len(heldout),
        "output_sha256": {p.name: sha256(p) for p in (dev_path, library_path, metrics_path, summary_path)},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
