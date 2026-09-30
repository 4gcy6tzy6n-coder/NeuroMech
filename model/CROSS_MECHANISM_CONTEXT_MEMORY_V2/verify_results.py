#!/usr/bin/env python3
"""Independent structural/arithmetic verification for CROSS_MECHANISM_CONTEXT_MEMORY_V2."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/canonical_corrected"
BOOT = 10_000
BOOT_SEED = 20261002


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name):
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def boot(values, rng):
    draws = values[rng.integers(0, len(values), (BOOT, len(values)))].mean(axis=1)
    return {"mean": float(values.mean()), "ci95": [float(np.quantile(draws, .025)), float(np.quantile(draws, .975))],
            "positive_seed_blocks": int(np.sum(values > 0)), "n_seed_blocks": int(len(values))}


def match(got, expected):
    assert np.isclose(got["mean"], expected["mean"], atol=1e-12, rtol=0)
    assert np.allclose(got["ci95"], expected["ci95"], atol=1e-12, rtol=0)
    assert got["positive_seed_blocks"] == expected["positive_seed_blocks"]


def main():
    m2, m5 = rows("m2_seed_results.csv"), rows("m5_seed_results.csv")
    summary = json.loads((OUT / "summary.json").read_text())
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    assert len(m2) == 96 and len(m5) == 128
    assert {int(r["seed"]) for r in m2} == set(range(32))
    assert {int(r["seed"]) for r in m5} == set(range(32))
    assert {float(r["kappa"]) for r in m2} == {-1.0, 0.0, 1.0}
    assert {int(r["delay"]) for r in m5} == {1, 4, 16, 64}
    for r in m2:
        assert np.isclose(float(r["gru_context_minus_gain"]), float(r["gru_context_mse"]) - float(r["context_gain_mse"]), atol=1e-12, rtol=0)
        assert np.isclose(float(r["gru_no_context_minus_gain"]), float(r["gru_no_context_mse"]) - float(r["context_gain_mse"]), atol=1e-12, rtol=0)
        assert int(r["context_gain_parameters"]) == 3 and int(r["gru_context_parameters"]) == 297 and int(r["gru_no_context_parameters"]) == 273
    for r in m5:
        assert int(r["learned_parameters_each_arm"]) == 16
        assert int(r["eligibility_state_dimensions"]) == int(r["latest_input_state_dimensions"]) == 16
        assert int(r["fifo_state_dimensions"]) == int(r["delay"]) * 16
        assert np.isclose(float(r["eligibility_minus_latest_input"]), float(r["eligibility_accuracy"]) - float(r["latest_input_accuracy"]), atol=1e-12, rtol=0)
        assert np.isclose(float(r["eligibility_minus_exact_fifo"]), float(r["eligibility_accuracy"]) - float(r["exact_fifo_accuracy"]), atol=1e-12, rtol=0)
    rng = np.random.default_rng(BOOT_SEED)
    for k in (1.0, 0.0, -1.0):
        group = [r for r in m2 if float(r["kappa"]) == k]
        got = summary["m2_by_mapping"][str(k)]
        match(got["gru_context_minus_gain"], boot(np.array([float(r["gru_context_minus_gain"]) for r in group]), rng))
        match(got["gru_no_context_minus_gain"], boot(np.array([float(r["gru_no_context_minus_gain"]) for r in group]), rng))
    for d in (1, 4, 16, 64):
        group = [r for r in m5 if int(r["delay"]) == d]
        got = summary["m5_by_delay"][str(d)]
        match(got["eligibility_minus_latest_input"], boot(np.array([float(r["eligibility_minus_latest_input"]) for r in group]), rng))
        match(got["eligibility_minus_exact_fifo"], boot(np.array([float(r["eligibility_minus_exact_fifo"]) for r in group]), rng))
    assert manifest["runner_sha256"] == digest(ROOT / "model/CROSS_MECHANISM_CONTEXT_MEMORY_V2/run_experiment.py")
    assert manifest["contract_sha256"] == digest(ROOT / "summery/CROSS_MECHANISM_CONTEXT_MEMORY_V2/CONTRACT.md")
    for name, expected in manifest["files"].items():
        assert digest(OUT / name) == expected
    print("PASS: 96 M2 and 128 M5 rows; paired contrasts, parameter/state accounting, seed-block bootstrap summaries, and artifact hashes verified.")


if __name__ == "__main__":
    main()
