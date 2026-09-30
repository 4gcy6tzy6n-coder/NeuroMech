#!/usr/bin/env python3
"""Compare corrected sensory feedback with scalar and marginal-duration controls."""
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
SOURCE_MODEL = ROOT / "model/M2_PERSISTENCE_YOKED_DIRECTION_V1/source_model.py"
AUTHOR_SOURCE = ROOT / "data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m"
CONTRACT = ROOT / "summery/M2_PERSISTENCE_YOKED_DIRECTION_V1/CONTRACT.md"
V5_SUMMARY = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V5/summary.json"
OUT_DEFAULT = ROOT / "data/results/M2_PERSISTENCE_YOKED_DIRECTION_V1"
NOISE_SCALES = (0.75, 1.00, 1.25)
DEV_SEEDS = range(350000, 350040)
TEST_SEEDS = range(360000, 360200)
MOTOR_COEFFICIENTS = {0.75: 0.760, 1.00: 0.665, 1.25: 0.610}
N_BOOT = 20_000
BOOT_SEED = 20261006
YOKE_SEED_OFFSET = 800_000_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as f:
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def contiguous_lengths(mask: np.ndarray) -> list[int]:
    change = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    starts = np.flatnonzero(change == 1)
    ends = np.flatnonzero(change == -1)
    return (ends - starts).tolist()


def summarize_yoke(seed: int, scale: float, forward_library: list[int], reverse_library: list[int], model) -> dict[str, object]:
    n_steps, n_agents, dt = model.N_STEPS, model.N_AGENTS, model.DT

    # Match the source-model heading random stream: noise array first, then resets, then initial headings.
    heading_rng = np.random.default_rng(seed)
    heading_rng.standard_normal((n_steps, n_agents))
    heading_reset = heading_rng.random((n_steps, n_agents)) * (2.0 * math.pi)
    heading0 = heading_rng.random(n_agents) * (2.0 * math.pi)
    bout_rng = np.random.default_rng(seed + YOKE_SEED_OFFSET + int(scale * 1000))

    forward = np.zeros((n_steps, n_agents), dtype=bool)
    for agent in range(n_agents):
        cursor = 0
        is_forward = True
        while cursor < n_steps:
            library = forward_library if is_forward else reverse_library
            bout_steps = max(1, int(library[bout_rng.integers(0, len(library))]))
            stop = min(n_steps, cursor + bout_steps)
            forward[cursor:stop, agent] = is_forward
            cursor = stop
            is_forward = not is_forward

    theta = np.empty((n_steps, n_agents), dtype=float)
    theta[0] = heading0
    for t in range(1, n_steps):
        f_to_r = forward[t - 1] & ~forward[t]
        r_to_f = ~forward[t - 1] & forward[t]
        theta[t] = theta[t - 1]
        theta[t, f_to_r] = np.mod(theta[t, f_to_r] + math.pi, 2.0 * math.pi)
        theta[t, r_to_f] = heading_reset[t, r_to_f]

    lengths = [n for agent in range(n_agents) for n in contiguous_lengths(forward[:, agent])]
    reverse_lengths = [n for agent in range(n_agents) for n in contiguous_lengths(~forward[:, agent])]
    forward_samples = int(forward.sum())
    direction = float((-np.cos(theta) * forward).sum() / forward_samples) if forward_samples else math.nan
    displacement = float(np.cos(theta).sum(axis=0).mean() * dt)
    return {
        "seed_block": seed,
        "arm": "MARGINAL_PERSISTENCE_YOKE",
        "noise_scale": scale,
        "sensory_site_feedback": 0.0,
        "motor_only_feedback": 0.0,
        "warm_direction_index": direction,
        "mean_forward_run_s": float(np.mean(lengths) * dt),
        "median_forward_run_s": float(np.median(lengths) * dt),
        "p90_forward_run_s": float(np.quantile(lengths, 0.90) * dt),
        "fraction_forward_runs_ge_30s": float(np.mean(np.asarray(lengths) * dt >= 30.0)),
        "forward_occupancy": float(forward_samples / (n_steps * n_agents)),
        "mean_final_warm_displacement": -displacement,
        "n_agents": n_agents,
        "n_forward_runs": len(lengths),
        "mean_reverse_run_s": float(np.mean(reverse_lengths) * dt),
        "median_reverse_run_s": float(np.median(reverse_lengths) * dt),
        "p90_reverse_run_s": float(np.quantile(reverse_lengths, 0.90) * dt),
        "n_reverse_runs": len(reverse_lengths),
    }


def ci95(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOT_SEED)
    indices = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    means = values[indices].mean(axis=1)
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    out = parser.parse_args().output_dir.expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    spec = importlib.util.spec_from_file_location("m2_persistence_yoke_source", SOURCE_MODEL)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import corrected source model")
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)

    # Build the yoke library from forward/reverse durations only. Do not use direction outcomes.
    dev_records: list[dict[str, object]] = []
    bout_library: dict[str, dict[str, list[int]]] = {
        str(scale): {"forward": [], "reverse": []} for scale in NOISE_SCALES
    }
    for i, seed in enumerate(DEV_SEEDS, 1):
        for scale in NOISE_SCALES:
            rows = model.run(seed, [("SENSORY_SITE_FB", 1.0, 0.0, scale)], capture_bouts=True)
            row = rows[0]
            dev_records.append({
                key: row[key] for key in (
                    "seed_block", "arm", "noise_scale", "mean_forward_run_s",
                    "median_forward_run_s", "p90_forward_run_s",
                    "fraction_forward_runs_ge_30s", "n_forward_runs",
                )
            })
            lib = bout_library[str(scale)]
            lib["forward"].extend(n for agent in row["forward_bouts_steps"] for n in agent)
            lib["reverse"].extend(n for agent in row["reverse_bouts_steps"] for n in agent)
        if i % 10 == 0:
            print(f"development seed blocks {i}/{len(DEV_SEEDS)}", flush=True)
    if any(not value[k] for value in bout_library.values() for k in ("forward", "reverse")):
        raise RuntimeError("development bout library is empty")

    dev_path = out / "development_summary.csv"
    write_csv(dev_path, dev_records)
    bouts_path = out / "development_bout_library.json"
    bouts_path.write_text(json.dumps(bout_library, separators=(",", ":")) + "\n")

    test_rows: list[dict[str, object]] = []
    conditions = []
    for scale in NOISE_SCALES:
        conditions.extend([
            ("SENSORY_SITE_FB", 1.0, 0.0, scale),
            ("MOTOR_MULTI_STAT_MATCHED", 0.0, MOTOR_COEFFICIENTS[scale], scale),
            ("NO_FEEDBACK", 0.0, 0.0, scale),
        ])
    for i, seed in enumerate(TEST_SEEDS, 1):
        source_rows = model.run(seed, conditions)
        test_rows.extend(source_rows)
        for scale in NOISE_SCALES:
            lib = bout_library[str(scale)]
            test_rows.append(summarize_yoke(seed, scale, lib["forward"], lib["reverse"], model))
        if i % 25 == 0:
            print(f"held-out seed blocks {i}/{len(TEST_SEEDS)}", flush=True)
    metrics_path = out / "heldout_metrics.csv"
    write_csv(metrics_path, test_rows)

    lookup = {(int(r["seed_block"]), float(r["noise_scale"]), str(r["arm"])): r for r in test_rows}
    by_scale: dict[str, object] = {}
    sensory_yoke_diffs = []
    sensory_scalar_diffs = []
    for scale in NOISE_SCALES:
        d_yoke = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "MARGINAL_PERSISTENCE_YOKE")]["warm_direction_index"])
            for seed in TEST_SEEDS
        ])
        d_scalar = np.asarray([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "MOTOR_MULTI_STAT_MATCHED")]["warm_direction_index"])
            for seed in TEST_SEEDS
        ])
        sensory_yoke_diffs.append(d_yoke)
        sensory_scalar_diffs.append(d_scalar)
        arms = {}
        for arm in ("SENSORY_SITE_FB", "MOTOR_MULTI_STAT_MATCHED", "MARGINAL_PERSISTENCE_YOKE", "NO_FEEDBACK"):
            cell = [r for r in test_rows if r["arm"] == arm and float(r["noise_scale"]) == scale]
            metrics = ("warm_direction_index", "mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s",
                       "fraction_forward_runs_ge_30s", "forward_occupancy", "mean_final_warm_displacement", "n_forward_runs")
            if arm == "MARGINAL_PERSISTENCE_YOKE":
                metrics += ("mean_reverse_run_s", "median_reverse_run_s", "p90_reverse_run_s", "n_reverse_runs")
            arms[arm] = {metric: float(np.mean([float(r[metric]) for r in cell])) for metric in metrics}
        persistence_diffs = {
            metric: float(np.mean([
                float(lookup[(seed, scale, "SENSORY_SITE_FB")][metric])
                - float(lookup[(seed, scale, "MARGINAL_PERSISTENCE_YOKE")][metric])
                for seed in TEST_SEEDS
            ]))
            for metric in ("mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s", "fraction_forward_runs_ge_30s", "forward_occupancy")
        }
        by_scale[str(scale)] = {
            "arms": arms,
            "sensory_minus_yoke_direction": {"mean": float(d_yoke.mean()), "ci95": ci95(d_yoke), "positive_blocks": int((d_yoke > 0).sum())},
            "sensory_minus_scalar_direction": {"mean": float(d_scalar.mean()), "ci95": ci95(d_scalar), "positive_blocks": int((d_scalar > 0).sum())},
            "sensory_minus_yoke_persistence_summary_means": persistence_diffs,
        }

    pooled_yoke = np.stack(sensory_yoke_diffs, axis=1).mean(axis=1)
    pooled_scalar = np.stack(sensory_scalar_diffs, axis=1).mean(axis=1)
    summary = {
        "experiment": "M2_PERSISTENCE_YOKED_DIRECTION_V1",
        "classification": "RETROSPECTIVE_EXPLORATORY_SOURCE_MODEL_ANALYSIS",
        "primary": {"estimand": "equal-weighted within-seed SENSORY_SITE_FB minus MARGINAL_PERSISTENCE_YOKE warm-direction index across noise scales",
                    "mean": float(pooled_yoke.mean()), "ci95_seed_block_bootstrap": ci95(pooled_yoke),
                    "positive_seed_blocks": int((pooled_yoke > 0).sum()), "n_seed_blocks": len(TEST_SEEDS)},
        "secondary_scalar_control": {"mean": float(pooled_scalar.mean()), "ci95_seed_block_bootstrap": ci95(pooled_scalar),
                                      "positive_seed_blocks": int((pooled_scalar > 0).sum())},
        "heldout_by_noise_scale": by_scale,
        "analysis_unit": "simulation seed block; agents and timesteps are clustered",
        "yoke_definition": "marginal empirical forward/reverse duration resampling from development sensory-site simulations, independent of position and heading",
        "limitations": [
            "prior M2/V3/V4/V5 outcomes were known; exploratory and retrospective",
            "the yoke matches marginal bout-duration distributions by construction but not state-, heading-, temperature-, or position-conditional bout statistics",
            "a positive sensory-minus-yoke difference would show marginal persistence alone is insufficient, not identify a unique feedback site or synapse",
            "source-model uncertainty is over simulation seed blocks and imposed noise scales, not animals",
            "no new biological validation or AI-transfer evidence is produced",
            "source index is corrected in code, but end-to-end MATLAB/Octave numerical parity remains unverified",
        ],
    }
    summary_path = out / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {
        "experiment": "M2_PERSISTENCE_YOKED_DIRECTION_V1",
        "development_seed_range": [min(DEV_SEEDS), max(DEV_SEEDS)],
        "heldout_seed_range": [min(TEST_SEEDS), max(TEST_SEEDS)],
        "noise_scales": list(NOISE_SCALES), "agents_per_block": model.N_AGENTS, "steps_per_trajectory": model.N_STEPS,
        "bootstrap_resamples": N_BOOT, "bootstrap_seed": BOOT_SEED, "yoke_seed_offset": YOKE_SEED_OFFSET,
        "motor_only_coefficients_from_v5": {str(k): v for k, v in MOTOR_COEFFICIENTS.items()},
        "inputs": {"contract_sha256": sha256(CONTRACT), "source_model_sha256": sha256(SOURCE_MODEL),
                   "runner_sha256": sha256(Path(__file__).resolve()),
                   "author_matlab_sha256": sha256(AUTHOR_SOURCE), "v5_summary_sha256": sha256(V5_SUMMARY)},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "heldout_rows": len(test_rows),
        "output_sha256": {p.name: sha256(p) for p in (dev_path, bouts_path, metrics_path, summary_path)},
    }
    manifest_path = out / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
