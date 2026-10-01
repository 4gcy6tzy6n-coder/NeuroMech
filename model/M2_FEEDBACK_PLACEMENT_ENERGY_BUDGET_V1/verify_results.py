#!/usr/bin/env python3
"""Verify energy-budget M2 run coverage, validation selection, metrics and hashes."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAME = "M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1"
OUT = ROOT / "data/results" / NAME / "canonical"
CONTRACT = ROOT / "summery" / NAME / "CONTRACT.md"
RUNNER = ROOT / "model" / NAME / "run_experiment.py"
BASE_RUNNER = ROOT / "model" / "M2_SENSORIMOTOR_TRANSIENT_FILTER_V1" / "run_experiment.py"
ARMS = ("SENSORY_SITE_1D", "OUTPUT_SITE_1D", "NO_FEEDBACK_1D", "GENERIC_RNN_1D", "GRU_8")
PARAMS = {"SENSORY_SITE_1D": 4, "OUTPUT_SITE_1D": 4, "NO_FEEDBACK_1D": 3, "GENERIC_RNN_1D": 6, "GRU_8": 297}
LAMBDAS = (0.0, 0.1, 0.3, 0.6)
CONDITIONS = ("TRANSIENT_PULSE", "SUSTAINED_SWITCH", "COMBINED_STRESS")
METRICS = ("movement_mse", "movement_mae", "state_accuracy", "command_energy", "pulse_window_mae", "mean_switch_latency_steps")
N_BLOCKS, N_VALIDATION, N_TEST, BUDGET = 16, 32, 64, 0.50


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
    rng = np.random.default_rng(seed)
    boot = v[rng.integers(0, len(v), size=(20_000, len(v)))].mean(axis=1)
    return {"mean": float(v.mean()), "median": float(np.median(v)),
            "ci95_low": float(np.quantile(boot, 0.025)), "ci95_high": float(np.quantile(boot, 0.975)),
            "n_seed_blocks": int(len(v))}


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0, abs_tol=1e-11)


def main() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text())
    assert manifest["experiment"] == NAME
    assert manifest["contract_sha256"] == sha256(CONTRACT)
    assert manifest["runner_sha256"] == sha256(RUNNER)
    assert manifest["base_model_runner_sha256"] == sha256(BASE_RUNNER)
    assert manifest["verifier_sha256"] == sha256(Path(__file__))
    for filename, info in manifest["outputs"].items():
        path = OUT / filename
        assert path.is_file() and path.stat().st_size == info["bytes"] and sha256(path) == info["sha256"]

    fits = read_csv(OUT / "fit_manifest.csv")
    val = read_csv(OUT / "validation_episodes.csv")
    selections = read_csv(OUT / "selection_manifest.csv")
    test = read_csv(OUT / "test_episodes.csv")
    test_seed = read_csv(OUT / "test_seed_summary.csv")
    summary = json.loads((OUT / "summary.json").read_text())
    assert len(fits) == N_BLOCKS * len(ARMS) * len(LAMBDAS)
    assert len(val) == N_BLOCKS * len(ARMS) * len(LAMBDAS) * len(CONDITIONS) * N_VALIDATION
    assert len(selections) == N_BLOCKS * len(ARMS)
    assert len(test) == N_BLOCKS * len(ARMS) * len(CONDITIONS) * N_TEST
    assert len(test_seed) == N_BLOCKS * len(ARMS) * len(CONDITIONS)

    fit_keys = set()
    for row in fits:
        key = (int(row["seed_block"]), row["arm"], float(row["energy_penalty"]))
        assert key not in fit_keys
        fit_keys.add(key)
        assert int(row["parameter_count"]) == PARAMS[row["arm"]]
        assert int(row["updates"]) == 100 and int(row["batch_size"]) == 32 and int(row["sequence_length"]) == 96

    val_groups: dict[tuple[int, str, float], list[dict[str, str]]] = defaultdict(list)
    val_keys = set()
    for row in val:
        key = (int(row["seed_block"]), row["arm"], float(row["energy_penalty"]), row["condition"], int(row["episode"]))
        assert key not in val_keys and row["arm"] in ARMS and row["condition"] in CONDITIONS
        val_keys.add(key)
        val_groups[key[:3]].append(row)
    selected_map = {}
    for row in selections:
        key = (int(row["seed_block"]), row["arm"])
        assert key not in selected_map
        selected_map[key] = row
        candidates = []
        for lam in LAMBDAS:
            cond_summary = {}
            for condition in CONDITIONS:
                rows = [r for r in val_groups[(key[0], key[1], lam)] if r["condition"] == condition]
                assert len(rows) == N_VALIDATION
                cond_summary[condition] = {
                    metric: float(np.mean([float(r[metric]) for r in rows if math.isfinite(float(r[metric]))]))
                    for metric in ("movement_mae", "command_energy")
                }
            candidates.append((lam, {m: float(np.mean([cond_summary[c][m] for c in CONDITIONS]))
                                     for m in ("movement_mae", "command_energy")}))
        eligible = [(lam, vals) for lam, vals in candidates if vals["command_energy"] <= BUDGET]
        if eligible:
            expected_lam, expected_vals = min(eligible, key=lambda x: (x[1]["movement_mae"], x[0]))
            expected_status = "VALIDATION_BUDGET_MET"
        else:
            expected_lam = min(LAMBDAS, key=lambda lam: next(v["command_energy"] for l, v in candidates if l == lam))
            expected_vals = next(v for l, v in candidates if l == expected_lam)
            expected_status = "NO_VALIDATION_POLICY_WITHIN_BUDGET"
        assert close(float(row["selected_energy_penalty"]), expected_lam)
        assert row["selection_status"] == expected_status
        assert close(float(row["validation_mean_mae_equal_condition"]), expected_vals["movement_mae"])
        assert close(float(row["validation_mean_energy_equal_condition"]), expected_vals["command_energy"])

    test_keys = set()
    test_groups: dict[tuple[int, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in test:
        key = (int(row["seed_block"]), row["arm"], row["condition"], int(row["episode"]))
        assert key not in test_keys and row["arm"] in ARMS and row["condition"] in CONDITIONS
        test_keys.add(key)
        select = selected_map[key[:2]]
        assert close(float(row["selected_energy_penalty"]), float(select["selected_energy_penalty"]))
        test_groups[key[:3]].append(row)
    seed_map = {}
    for row in test_seed:
        key = (int(row["seed_block"]), row["arm"], row["condition"])
        assert key not in seed_map
        seed_map[key] = row
        episodes = test_groups[key]
        assert len(episodes) == N_TEST and int(row["n_episodes"]) == N_TEST
        for metric in METRICS:
            vals = [float(r[metric]) for r in episodes if math.isfinite(float(r[metric]))]
            if vals:
                assert close(float(row[metric]), float(np.mean(vals)))
            else:
                assert row[metric] in ("", "nan", "None")

    primary_values = []
    for block in range(N_BLOCKS):
        ssel, osel = selected_map[(block, "SENSORY_SITE_1D")], selected_map[(block, "OUTPUT_SITE_1D")]
        if ssel["selection_status"] == osel["selection_status"] == "VALIDATION_BUDGET_MET":
            s = float(seed_map[(block, "SENSORY_SITE_1D", "TRANSIENT_PULSE")]["movement_mae"])
            o = float(seed_map[(block, "OUTPUT_SITE_1D", "TRANSIENT_PULSE")]["movement_mae"])
            primary_values.append({"seed_block": block, "sensory_minus_output_mae": s - o})
    assert len(primary_values) == summary["primary_validation_feasible_blocks"]
    if primary_values:
        expected_primary = estimate([r["sensory_minus_output_mae"] for r in primary_values], 8_123_456)
        for k, value in expected_primary.items():
            assert close(float(summary["primary_contrast_summary"][k]), float(value))
    assert all(close(float(a["sensory_minus_output_mae"]), float(b["sensory_minus_output_mae"]))
               for a, b in zip(primary_values, summary["primary_paired_seed_block_values"]))

    budget_est = {}
    for i, arm in enumerate(("SENSORY_SITE_1D", "OUTPUT_SITE_1D")):
        values = [float(r["command_energy"]) for r in test_seed
                  if r["arm"] == arm and r["condition"] == "TRANSIENT_PULSE" and
                  r["selection_status"] == "VALIDATION_BUDGET_MET"]
        budget_est[arm] = estimate(values, 9_100_000 + i) if values else None
        actual = summary["heldout_primary_energy_by_arm"][arm]
        assert (budget_est[arm] is None) == (actual is None)
        if actual is not None:
            for k, value in budget_est[arm].items():
                assert close(float(actual[k]), float(value))
    expected_budget_status = ("BOTH_TEST_MEAN_CIS_WITHIN_BUDGET" if all(budget_est[a] is not None and budget_est[a]["ci95_high"] <= BUDGET
                                                                          for a in ("SENSORY_SITE_1D", "OUTPUT_SITE_1D"))
                              else "HELDOUT_BUDGET_NOT_ESTABLISHED")
    assert summary["primary_budget_status"] == expected_budget_status

    result = {"status": "PASS", "fit_candidates": len(fits), "validation_episode_rows": len(val),
              "selected_policies": len(selections), "test_episode_rows": len(test),
              "test_seed_summary_rows": len(test_seed), "primary_blocks_recomputed": len(primary_values),
              "hashed_outputs_checked": len(manifest["outputs"]),
              "scope": "validation-selected penalty, row coverage, seed aggregation, primary bootstrap and held-out budget status"}
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
