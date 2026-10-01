#!/usr/bin/env python3
"""Independently verify M2 transient-filter episode coverage and summaries."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_SENSORIMOTOR_TRANSIENT_FILTER_V1"
OUT = ROOT / "data/results" / NAME / "canonical"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
RUNNER = ROOT / "model" / NAME / "run_experiment.py"
LEARNED_ARMS = ("SENSORY_SITE_1D", "OUTPUT_SITE_1D", "NO_FEEDBACK_1D", "GENERIC_RNN_1D", "GRU_8")
ARMS = LEARNED_ARMS + ("DIRECT_SENSOR", "TARGET_ORACLE")
CONDITIONS = ("CLEAN_STABLE", "TRANSIENT_PULSE", "LONG_PULSE", "SUSTAINED_SWITCH", "COMBINED_STRESS")
METRICS = ("movement_mse", "movement_mae", "state_accuracy", "command_energy", "pulse_window_mae", "mean_switch_latency_steps")
N_BLOCKS, N_EPISODES = 20, 64
PARAMS = {"SENSORY_SITE_1D": 4, "OUTPUT_SITE_1D": 4, "NO_FEEDBACK_1D": 3, "GENERIC_RNN_1D": 6, "GRU_8": 297}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def estimate(values: list[float], seed: int) -> dict[str, float | int]:
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    boot = np.mean(v[rng.integers(0, len(v), size=(20_000, len(v)))], axis=1)
    return {"mean": float(v.mean()), "median": float(np.median(v)),
            "ci95_low": float(np.quantile(boot, 0.025)), "ci95_high": float(np.quantile(boot, 0.975)),
            "n_seed_blocks": int(len(v))}


def same(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0, abs_tol=1e-11)


def main() -> None:
    out = json.loads((OUT / "manifest.json").read_text())
    assert out["experiment"] == NAME
    assert out["contract_sha256"] == sha256(CONTRACT)
    assert out["runner_sha256"] == sha256(RUNNER)
    for filename, meta in out["outputs"].items():
        p = OUT / filename
        assert p.is_file() and p.stat().st_size == meta["bytes"]
        assert sha256(p) == meta["sha256"]
    episodes = read_csv(OUT / "episode_metrics.csv")
    fits = read_csv(OUT / "fit_manifest.csv")
    seeds = read_csv(OUT / "seed_summary.csv")
    summary = json.loads((OUT / "summary.json").read_text())
    assert len(episodes) == N_BLOCKS * len(ARMS) * len(CONDITIONS) * N_EPISODES
    assert len(fits) == N_BLOCKS * len(LEARNED_ARMS)
    assert len(seeds) == N_BLOCKS * len(ARMS) * len(CONDITIONS)
    assert summary["total_episode_arm_rows"] == len(episodes)
    assert summary["fit_records"] == len(fits)
    keys = set()
    episode_groups = defaultdict(list)
    for row in episodes:
        assert row["arm"] in ARMS and row["condition"] in CONDITIONS
        key = (int(row["seed_block"]), row["arm"], row["condition"], int(row["episode"]))
        assert key not in keys
        keys.add(key)
        episode_groups[key[:3]].append(row)
        for m in METRICS:
            v = float(row[m])
            if math.isfinite(v):
                assert math.isfinite(v)
        assert int(row["n_eligible_pulses"]) >= 0 and int(row["n_target_switches"]) >= 0
    fit_keys = set()
    for row in fits:
        key = (int(row["seed_block"]), row["arm"])
        assert key not in fit_keys
        fit_keys.add(key)
        assert int(row["parameter_count"]) == PARAMS[row["arm"]]
        assert int(row["updates"]) == 100 and int(row["batch_size"]) == 32 and int(row["sequence_length"]) == 96
    seed_map = {}
    for row in seeds:
        key = (int(row["seed_block"]), row["arm"], row["condition"])
        assert key not in seed_map
        seed_map[key] = row
        source_rows = episode_groups[key]
        assert len(source_rows) == N_EPISODES
        assert int(row["n_episodes"]) == N_EPISODES
        for metric in METRICS:
            vals = [float(r[metric]) for r in source_rows if math.isfinite(float(r[metric]))]
            if vals:
                assert row[metric] not in ("", "nan", "None") and same(float(row[metric]), float(np.mean(vals)))
            else:
                assert row[metric] in ("", "nan", "None")
    recomputed = {}
    for ci, condition in enumerate(CONDITIONS):
        recomputed[condition] = {}
        for ai, arm in enumerate(ARMS):
            recomputed[condition][arm] = {}
            for mi, metric in enumerate(METRICS):
                vals = [float(seed_map[(block, arm, condition)][metric]) for block in range(N_BLOCKS)
                        if seed_map[(block, arm, condition)][metric] not in ("", "nan", "None")]
                recomputed[condition][arm][metric] = estimate(vals, 909090 + ci * 100 + ai * 10 + mi) if vals else None
    for condition in CONDITIONS:
        for arm in ARMS:
            for metric in METRICS:
                expected = recomputed[condition][arm][metric]
                actual = summary["metric_summary"][condition][arm][metric]
                assert (expected is None) == (actual is None)
                if expected:
                    for k, v in expected.items():
                        assert same(float(actual[k]), float(v))
    contrasts = []
    for block in range(N_BLOCKS):
        s = float(seed_map[(block, "SENSORY_SITE_1D", "TRANSIENT_PULSE")]["pulse_window_mae"])
        o = float(seed_map[(block, "OUTPUT_SITE_1D", "TRANSIENT_PULSE")]["pulse_window_mae"])
        contrasts.append(o - s)
    assert len(contrasts) == N_BLOCKS and all(math.isfinite(x) for x in contrasts)
    primary = estimate(contrasts, 8_888_888)
    for k, v in primary.items():
        assert same(float(summary["primary_seed_block_contrast"][k]), float(v))
    stored = {int(k): float(v) for k, v in summary["primary_seed_block_values"].items()}
    assert len(stored) == N_BLOCKS
    assert all(same(stored[i], contrasts[i]) for i in range(N_BLOCKS))
    result = {"status": "PASS", "episode_rows": len(episodes), "fit_records": len(fits),
              "seed_summary_rows": len(seeds), "primary_seed_block_contrasts_recomputed": len(contrasts),
              "hashed_outputs_checked": len(out["outputs"]),
              "scope": "coverage, fit metadata, output hashes, aggregation and primary bootstrap; not an independent model-training implementation"}
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
