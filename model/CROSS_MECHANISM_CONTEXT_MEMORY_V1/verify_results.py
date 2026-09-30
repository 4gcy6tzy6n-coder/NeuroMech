#!/usr/bin/env python3
"""Independent structural and arithmetic verification for CROSS_MECHANISM_CONTEXT_MEMORY_V1."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V1/canonical"
BOOT = 10_000
BOOT_SEED = 20261001


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str):
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def close(a, b):
    return bool(np.isclose(float(a), float(b), atol=1e-12, rtol=0))


def bootstrap(values: np.ndarray, rng: np.random.Generator):
    draws = np.mean(values[rng.integers(0, len(values), (BOOT, len(values)))], axis=1)
    return {"mean": float(np.mean(values)),
            "ci95": [float(np.quantile(draws, .025)), float(np.quantile(draws, .975))],
            "positive_seed_blocks": int(np.sum(values > 0)), "n_seed_blocks": int(len(values))}


def main():
    m2, m5 = load("m2_seed_results.csv"), load("m5_seed_results.csv")
    summary = json.loads((OUT / "summary.json").read_text())
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    assert len(m2) == 96 and len(m5) == 128
    assert {int(r["seed"]) for r in m2} == set(range(32))
    assert {int(r["seed"]) for r in m5} == set(range(32))
    assert {float(r["kappa"]) for r in m2} == {-1.0, 0.0, 1.0}
    assert {int(r["delay"]) for r in m5} == {1, 4, 16, 64}
    for r in m2:
        assert close(r["control_minus_gain"], float(r["additive_control_mse"]) - float(r["context_gain_mse"]))
    for r in m5:
        assert close(r["eligibility_minus_misassignment"], float(r["eligibility_accuracy"]) - float(r["misassignment_accuracy"]))
        assert close(r["eligibility_minus_replay"], float(r["eligibility_accuracy"]) - float(r["replay_accuracy"]))
        assert close(r["eligibility_accuracy"], r["replay_accuracy"])
        assert int(r["learned_parameters"]) == 16
        assert int(r["eligibility_state_dimensions"]) == int(r["replay_state_dimensions"]) == 16
    rng = np.random.default_rng(BOOT_SEED)
    for k in (1.0, 0.0, -1.0):
        vals = np.array([float(r["control_minus_gain"]) for r in m2 if float(r["kappa"]) == k])
        got, expected = summary["m2_by_context_mapping"][str(k)], bootstrap(vals, rng)
        assert close(got["mean"], expected["mean"]) and np.allclose(got["ci95"], expected["ci95"], atol=1e-12, rtol=0)
    for d in (1, 4, 16, 64):
        vals = np.array([float(r["eligibility_minus_misassignment"]) for r in m5 if int(r["delay"]) == d])
        got, expected = summary["m5_by_delay"][str(d)], bootstrap(vals, rng)
        assert close(got["mean"], expected["mean"]) and np.allclose(got["ci95"], expected["ci95"], atol=1e-12, rtol=0)
        replay_vals = np.array([float(r["eligibility_minus_replay"]) for r in m5 if int(r["delay"]) == d])
        replay_got, replay_expected = summary["m5_eligibility_minus_capacity_matched_persistent_cue_by_delay"][str(d)], bootstrap(replay_vals, rng)
        assert close(replay_got["mean"], replay_expected["mean"]) and np.allclose(replay_got["ci95"], replay_expected["ci95"], atol=1e-12, rtol=0)
    assert manifest["runner_sha256"] == digest(ROOT / "model/CROSS_MECHANISM_CONTEXT_MEMORY_V1/run_experiment.py")
    assert manifest["contract_sha256"] == digest(ROOT / "summery/CROSS_MECHANISM_CONTEXT_MEMORY_V1/CONTRACT.md")
    for name, expected in manifest["files"].items():
        assert digest(OUT / name) == expected
    print("PASS: 96 M2 rows, 128 M5 rows, seed-block contrasts, bootstrap summaries, matched M5 trace/replay state, and artifact hashes verified.")


if __name__ == "__main__":
    main()
