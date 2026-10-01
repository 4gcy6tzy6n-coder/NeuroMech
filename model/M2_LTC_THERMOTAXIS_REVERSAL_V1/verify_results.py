#!/usr/bin/env python3
"""Independent structural and summary arithmetic audit."""
import csv, hashlib, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_LTC_THERMOTAXIS_REVERSAL_V1"
OUT = ROOT / "data/results" / EXP
SEEDS = list(range(920000, 920032))
ARMS = ["LTC_SENSORY_SITE", "LTC_OUTPUT_SITE", "LTC_NO_FEEDBACK", "LTC_DENSE_FEEDBACK",
        "LTC_SENSORY_YOKED", "GRU_4", "GRU_8", "GRADIENT_SIGN_ORACLE"]
HAZARDS = [1/80, 1/40, 1/20]
NTEST = 128

def read(p):
    with p.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ep, fits = read(OUT/"episode_results.csv"), read(OUT/"training_results.csv")
    summary = json.loads((OUT/"summary.json").read_text())
    preflight = json.loads((OUT/"PREFLIGHT.json").read_text())
    metadata = json.loads((OUT/"RUN_METADATA.json").read_text())
    runner = ROOT/"model"/EXP/"run_experiment.py"
    contract = ROOT/"summery"/EXP/"CONTRACT.md"
    assert preflight["contract_sha256"] == metadata["contract_sha256"] == sha(contract)
    assert preflight["runner_sha256"] == metadata["runner_sha256"] == sha(runner)
    assert preflight["outcomes_computed"] is False
    expected = len(SEEDS)*len(ARMS)*len(HAZARDS)*NTEST
    assert len(ep) == expected == 98304
    assert len(fits) == len(SEEDS)*7 == 224
    keys, cells = set(), {}
    for r in ep:
        k = (int(r["training_seed"]), r["arm"], float(r["reversal_hazard"]), int(r["episode_id"]))
        assert k not in keys, f"duplicate row: {k}"
        keys.add(k)
        assert k[0] in SEEDS and k[1] in ARMS and k[2] in HAZARDS and 0 <= k[3] < NTEST
        for m in ("position_mse", "position_mae", "temperature_error_mse", "action_energy", "preferred_band_occupancy"):
            x = float(r[m]); assert np.isfinite(x) and x >= 0, (k, m, x)
        cells.setdefault(k[:3], 0); cells[k[:3]] += 1
    assert len(cells) == len(SEEDS)*len(ARMS)*len(HAZARDS)
    assert set(cells.values()) == {NTEST}
    pcounts = {}
    for r in fits:
        state = json.loads(r["parameters_json"])
        # sensory_mask is a registered non-trainable buffer in saved LTC state.
        n = sum(len(v) for name, v in state.items() if name != "sensory_mask")
        assert n == int(r["parameter_count"])
        assert np.isfinite([float(x) for v in state.values() for x in v]).all()
        pcounts.setdefault(r["arm"], set()).add(n)
    assert pcounts == {"LTC_SENSORY_SITE": {114}, "LTC_OUTPUT_SITE": {114}, "LTC_NO_FEEDBACK": {114},
        "LTC_DENSE_FEEDBACK": {114}, "LTC_SENSORY_YOKED": {114}, "GRU_4": {113}, "GRU_8": {321}}
    primary = [r for r in summary["all_position_mse_contrasts"] if r["reversal_hazard"] == 1/20]
    assert primary == summary["primary_contrasts"]
    # Independently recompute primary point estimates from raw rows.
    keyed = {}
    for r in ep:
        k = (int(r["training_seed"]), r["arm"], float(r["reversal_hazard"]))
        keyed.setdefault(k, []).append(float(r["position_mse"]))
    for result in primary:
        comp = result["contrast"].split("_POSITION_MSE_MINUS_")[0]
        diffs = [np.mean(keyed[(s, comp, 1/20)]) - np.mean(keyed[(s, "LTC_SENSORY_SITE", 1/20)]) for s in SEEDS]
        assert abs(float(np.mean(diffs))-result["mean_paired_seed_effect"]) < 1e-10
    figures = [OUT/"figures"/f"{EXP}.{x}" for x in ("png", "svg", "pdf")]
    assert all(p.is_file() and p.stat().st_size > 0 for p in figures)
    report = {"experiment_id": EXP, "passed": True,
        "checks": {"episode_grid_complete": True, "fits_complete": True,
            "no_duplicate_episode_rows": True, "outcomes_finite_and_nonnegative": True,
            "saved_parameter_states_match_counts": True, "primary_point_estimates_recomputed": True,
            "figure_exports_present": True},
        "row_counts": {"episode_results": len(ep), "training_results": len(fits)},
        "sha256": {p.name: sha(p) for p in [OUT/"episode_results.csv", OUT/"training_results.csv", OUT/"summary.json"]}}
    (OUT/"POSTRUN_VERIFICATION.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__": main()
