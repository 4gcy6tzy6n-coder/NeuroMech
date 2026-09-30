#!/usr/bin/env python3
"""Outcome-informed V4 M2 source-model stress test with multi-statistic calibration."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
V3_RUNNER = ROOT / "model/M2_FEEDBACK_SITE_SPECIFICITY_V3/run_experiment.py"
V3_DEV = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3/development_calibration.csv"
V3_MANIFEST = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V3/run_manifest.json"
CONTRACT = ROOT / "summery/M2_FEEDBACK_SITE_SPECIFICITY_V4/CONTRACT.md"
OUT_DEFAULT = ROOT / "data/results/M2_FEEDBACK_SITE_SPECIFICITY_V4"
NOISE_SCALES = (0.75, 1.00, 1.25)
TEST_SEEDS = tuple(range(320000, 320200))
MATCH_METRICS = ("mean_forward_run_s", "median_forward_run_s", "p90_forward_run_s", "fraction_forward_runs_ge_30s")
N_BOOT = 20_000
BOOT_SEED = 20261004


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def calibrate(rows: list[dict[str, str]]) -> tuple[dict[float, float], dict[str, object]]:
    selected: dict[float, float] = {}
    details: dict[str, object] = {}
    for scale in NOISE_SCALES:
        cell = [r for r in rows if float(r["noise_scale"]) == scale]
        target_rows = [r for r in cell if r["arm"] == "SENSORY_SITE_FB"]
        target = {m: float(np.mean([float(r[m]) for r in target_rows])) for m in MATCH_METRICS}
        candidates = sorted({float(r["motor_only_feedback"]) for r in cell if r["arm"].startswith("MOTOR_ONLY_")})
        summaries = {
            c: {m: float(np.mean([float(r[m]) for r in cell if r["arm"] == f"MOTOR_ONLY_{c:.3f}"])) for m in MATCH_METRICS}
            for c in candidates
        }
        scales = {m: float(np.std([summaries[c][m] for c in candidates], ddof=0)) for m in MATCH_METRICS}
        scores = {
            c: sum(((summaries[c][m] - target[m]) / scales[m]) ** 2 if scales[m] > 0 else 0.0 for m in MATCH_METRICS)
            for c in candidates
        }
        choice = min(candidates, key=lambda c: (scores[c], c))
        selected[scale] = choice
        details[str(scale)] = {
            "target_development_means": target,
            "selected_motor_feedback": choice,
            "selected_development_means": summaries[choice],
            "standardization_sd_across_motor_grid": scales,
            "selected_standardized_squared_error": scores[choice],
            "grid": candidates,
        }
    return selected, details


def bootstrap_ci(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOT_SEED)
    ix = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    means = values[ix].mean(axis=1)
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    out = args.output_dir.expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    v3_manifest = json.loads(V3_MANIFEST.read_text())
    dev_rows = read_csv(V3_DEV)
    selected, calibration = calibrate(dev_rows)
    spec = importlib.util.spec_from_file_location("m2_v3_runner", V3_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the archived V3 source-model runner")
    v3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v3)

    conditions = []
    for scale in NOISE_SCALES:
        conditions.extend([
            ("SENSORY_SITE_FB", 1.0, 0.0, scale),
            ("MOTOR_MULTI_STAT_MATCHED", 0.0, selected[scale], scale),
            ("NO_FEEDBACK", 0.0, 0.0, scale),
        ])
    heldout: list[dict[str, object]] = []
    for i, seed in enumerate(TEST_SEEDS, 1):
        heldout.extend(v3.run(seed, conditions))
        if i % 25 == 0:
            print(f"held-out seed blocks {i}/{len(TEST_SEEDS)}", flush=True)

    metrics_path = out / "heldout_simulation_metrics.csv"
    with metrics_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(heldout[0]))
        writer.writeheader(); writer.writerows(heldout)

    lookup = {(int(r["seed_block"]), float(r["noise_scale"]), str(r["arm"])): r for r in heldout}
    scale_diffs: list[np.ndarray] = []
    by_scale: dict[str, object] = {}
    for scale in NOISE_SCALES:
        pairs = [(lookup[(seed, scale, "SENSORY_SITE_FB")], lookup[(seed, scale, "MOTOR_MULTI_STAT_MATCHED")]) for seed in TEST_SEEDS]
        d = np.array([float(a["warm_direction_index"]) - float(b["warm_direction_index"]) for a, b in pairs])
        scale_diffs.append(d)
        summary_diffs = {
            metric: float(np.mean([float(a[metric]) - float(b[metric]) for a, b in pairs]))
            for metric in MATCH_METRICS
        }
        arm_means = {
            arm: {metric: float(np.mean([float(r[metric]) for r in heldout if r["arm"] == arm and float(r["noise_scale"]) == scale]))
                  for metric in ("warm_direction_index", *MATCH_METRICS, "forward_occupancy", "n_forward_runs", "mean_final_warm_displacement")}
            for arm in ("SENSORY_SITE_FB", "MOTOR_MULTI_STAT_MATCHED", "NO_FEEDBACK")
        }
        by_scale[str(scale)] = {
            "selected_motor_feedback": selected[scale],
            "arms": arm_means,
            "sensory_minus_motor_warm_direction": {"mean": float(d.mean()), "ci95_seed_block_bootstrap": bootstrap_ci(d), "positive_blocks": int((d > 0).sum())},
            "sensory_minus_motor_persistence_summary_means": summary_diffs,
        }
    pooled = np.stack(scale_diffs, axis=1).mean(axis=1)
    summary = {
        "experiment": "M2_FEEDBACK_SITE_SPECIFICITY_V4",
        "classification": "RETROSPECTIVE_OUTCOME_INFORMED_SOURCE_MODEL_STRESS_TEST",
        "question": "Does the V3 sensory-site warm-direction advantage persist after development-only motor calibration to four forward-run persistence summaries?",
        "primary": {"estimand": "equal-weighted within-seed sensory-site minus motor-only warm-direction index across three noise scales",
                    "mean": float(pooled.mean()), "ci95_seed_block_bootstrap": bootstrap_ci(pooled),
                    "positive_seed_blocks": int((pooled > 0).sum()), "n_seed_blocks": len(TEST_SEEDS)},
        "calibration": calibration,
        "heldout_by_noise_scale": by_scale,
        "analysis_unit": "simulation seed block; 50 agents are clustered within block",
        "limitations": [
            "all prior M2 and V3 outcomes were known before this follow-up; exploratory and retrospective",
            "calibration matches four run-duration summaries, not the full distribution, occupancy, switching latency, or internal state",
            "Python source-model implementation parity with the author's MATLAB/Octave implementation remains unverified",
            "imposed noise scales are simulation conditions, not measured biological boundary conditions",
            "this source-model result is not new biological evidence or AI transfer",
        ],
    }
    summary_path = out / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {
        "experiment": "M2_FEEDBACK_SITE_SPECIFICITY_V4",
        "development_seed_range": [310000, 310039], "heldout_test_seed_range": [TEST_SEEDS[0], TEST_SEEDS[-1]],
        "noise_scales": list(NOISE_SCALES), "agents_per_block": v3.N_AGENTS, "steps_per_trajectory": v3.N_STEPS,
        "bootstrap_resamples": N_BOOT, "bootstrap_seed": BOOT_SEED,
        "inputs": {"contract_sha256": sha256(CONTRACT), "v3_runner_sha256": sha256(V3_RUNNER),
                   "v3_development_csv_sha256": sha256(V3_DEV), "v3_run_manifest_sha256": sha256(V3_MANIFEST),
                   "source_archive_sha256": v3_manifest["source_archive_sha256"]},
        "selected_motor_feedback": {str(k): v for k, v in selected.items()},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "rows": len(heldout), "output_sha256": {p.name: sha256(p) for p in (metrics_path, summary_path)},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
