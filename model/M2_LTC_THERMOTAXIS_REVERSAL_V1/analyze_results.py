#!/usr/bin/env python3
"""Seed-block paired analysis for M2_LTC_THERMOTAXIS_REVERSAL_V1."""
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
NTEST, NBOOT, BOOT_SEED = 128, 20_000, 20261003

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def read_csv(p):
    with p.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))

def boot(v):
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(v), size=(NBOOT, len(v)))
    return [float(x) for x in np.quantile(v[idx].mean(1), [0.025, 0.975])]

def main():
    episodes = read_csv(OUT / "episode_results.csv")
    training = read_csv(OUT / "training_results.csv")
    exp_n = len(SEEDS) * len(ARMS) * len(HAZARDS) * NTEST
    if len(episodes) != exp_n or len(training) != len(SEEDS) * 7:
        raise AssertionError(f"unexpected rows: episodes={len(episodes)}, training={len(training)}")
    grid, seen = {}, set()
    metrics = ["position_mse", "position_mae", "temperature_error_mse", "action_energy",
               "preferred_band_occupancy", "post_reversal_band_recovery_steps"]
    for r in episodes:
        seed, arm, hazard, ep = int(r["training_seed"]), r["arm"], float(r["reversal_hazard"]), int(r["episode_id"])
        key = (seed, arm, hazard, ep)
        if key in seen: raise AssertionError(f"duplicate episode row: {key}")
        seen.add(key)
        if seed not in SEEDS or arm not in ARMS or hazard not in HAZARDS or not 0 <= ep < NTEST:
            raise AssertionError(f"unexpected episode key: {key}")
        for m in metrics:
            if r[m] != "" and (not np.isfinite(float(r[m])) or float(r[m]) < 0):
                raise AssertionError(f"invalid {m}: {key}")
        grid.setdefault((seed, arm, hazard), []).append(r)
    if len(grid) != len(SEEDS)*len(ARMS)*len(HAZARDS) or any(len(v) != NTEST for v in grid.values()):
        raise AssertionError("incomplete seed × arm × reversal-hazard × episode grid")
    def avg(seed, arm, hazard, metric):
        v = [float(r[metric]) for r in grid[(seed, arm, hazard)] if r[metric] != ""]
        return float(np.mean(v)) if v else float("nan")
    contrasts, arms_summary = [], []
    comparators = [a for a in ARMS if a != "LTC_SENSORY_SITE"]
    for hazard in HAZARDS:
        for comp in comparators:
            effects = np.array([avg(s, comp, hazard, "position_mse") -
                                avg(s, "LTC_SENSORY_SITE", hazard, "position_mse") for s in SEEDS])
            ci = boot(effects)
            contrasts.append({"reversal_hazard": hazard,
                "contrast": f"{comp}_POSITION_MSE_MINUS_LTC_SENSORY_SITE_POSITION_MSE",
                "mean_paired_seed_effect": float(effects.mean()), "bootstrap_95ci": ci,
                "positive_seed_blocks": int((effects > 0).sum()), "seed_blocks": len(SEEDS)})
        for arm in ARMS:
            for metric in metrics:
                values = np.array([avg(s, arm, hazard, metric) for s in SEEDS])
                ci = boot(values)
                arms_summary.append({"reversal_hazard": hazard, "arm": arm, "metric": metric,
                    "mean_seed_block": float(values.mean()), "bootstrap_95ci": ci,
                    "seed_blocks": len(SEEDS)})
    primary = [r for r in contrasts if r["reversal_hazard"] == 1/20]
    train_summary = {}
    for arm in ARMS[:-1]:
        rows = [r for r in training if r["arm"] == arm]
        params = sorted(set(int(r["parameter_count"]) for r in rows))
        train_summary[arm] = {"parameter_counts": params,
            "mean_training_seconds": float(np.mean([float(r["training_seconds"]) for r in rows])),
            "mean_final_10_update_loss": float(np.mean([float(r["final_10_update_loss"]) for r in rows]))}
    summary = {"experiment_id": EXP, "status": "POST_RESULT_EXPLORATORY_ARTIFICIAL_EXPERIMENT",
        "primary_condition": {"evaluation_reversal_hazard": 1/20}, "primary_contrasts": primary,
        "all_position_mse_contrasts": contrasts, "arm_metric_summaries": arms_summary,
        "resource_accounting": train_summary,
        "row_counts": {"episode_results": len(episodes), "training_results": len(training)},
        "independent_seed_blocks": len(SEEDS), "episodes_per_seed_arm_condition": NTEST,
        "analysis": {"bootstrap_resamples": NBOOT, "seed": BOOT_SEED,
                     "resampling_unit": "paired training-seed block"}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"row_counts": summary["row_counts"], "primary_contrasts": primary,
        "resource_accounting": train_summary}, indent=2))

if __name__ == "__main__": main()
