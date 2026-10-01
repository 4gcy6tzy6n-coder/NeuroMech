#!/usr/bin/env python3
"""Summarize the frozen M2 bursty-observation experiment."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

ARMS = ("SENSORY_SITE", "OUTPUT_SITE", "NO_FEEDBACK", "GENERIC_RNN", "GRU_8")
QS = (0.50, 0.25, 0.125)
NBOOT, BOOT_SEED = 10_000, 20261001


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def crossed_bootstrap(diff, rng, nboot=NBOOT):
    nseed, nepisode = diff.shape
    values = np.empty(nboot, dtype=float)
    for b in range(nboot):
        seeds = rng.integers(0, nseed, size=nseed)
        ep = rng.integers(0, nepisode, size=(nseed, nepisode))
        values[b] = np.mean(diff[seeds[:, None], ep])
    return [float(np.quantile(values, .025)), float(np.quantile(values, .975))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_dir", type=Path)
    args = ap.parse_args()
    rows = read_csv(args.result_dir / "episode_results.csv")
    seeds = sorted({int(r["training_seed"]) for r in rows})
    missing_by_episode = {(int(r["training_seed"]), float(r["visibility_q"]), int(r["episode_id"])):
                          float(r["missing_fraction"]) for r in rows if r["arm"] == "SENSORY_SITE"}
    summary = {"experiment_id": "M2_BURSTY_OBSERVATION_FEEDBACK_V1", "episode_rows": len(rows),
               "training_seed_count": len(seeds), "conditions": {}, "primary": {}}
    lookup = {(int(r["training_seed"]), float(r["visibility_q"]), int(r["episode_id"]), r["arm"]): r for r in rows}
    for q in QS:
        condition = {}
        for arm in ARMS:
            vals = np.array([float(r["tracking_mse"]) for r in rows if float(r["visibility_q"]) == q and r["arm"] == arm])
            ens = np.array([float(r["action_energy"]) for r in rows if float(r["visibility_q"]) == q and r["arm"] == arm])
            recs = [float(r["post_gap_recovery_steps"]) for r in rows if float(r["visibility_q"]) == q and r["arm"] == arm and r["post_gap_recovery_steps"] != ""]
            condition[arm] = {"mean_tracking_mse": float(vals.mean()), "sd_episode_tracking_mse": float(vals.std(ddof=1)),
                              "mean_action_energy": float(ens.mean()), "mean_post_gap_recovery_steps": float(np.mean(recs)),
                              "post_gap_episode_rows": len(recs)}
        summary["conditions"][str(q)] = condition
        condition["realized_mean_missing_fraction"] = float(np.mean([v for (s, qq, e), v in missing_by_episode.items() if qq == q]))
    q = .125
    rng = np.random.default_rng(BOOT_SEED)
    primary_diffs = {}
    for comparator in ("OUTPUT_SITE", "GENERIC_RNN", "GRU_8", "NO_FEEDBACK"):
        d = np.array([[float(lookup[(s, q, e, comparator)]["tracking_mse"]) -
                       float(lookup[(s, q, e, "SENSORY_SITE")]["tracking_mse"])
                       for e in range(128)] for s in seeds])
        primary_diffs[comparator] = d
        summary["primary"][f"{comparator}_minus_SENSORY_SITE"] = {
            "mean_difference": float(d.mean()), "ci95_crossed_seed_episode": crossed_bootstrap(d, rng),
            "positive_seed_means": int(np.sum(d.mean(axis=1) > 0)), "seed_count": len(seeds)}
    fits = read_csv(args.result_dir / "training_results.csv")
    summary["fit_counts"] = {arm: sum(r["arm"] == arm for r in fits) for arm in ARMS}
    summary["parameter_counts"] = {arm: sorted({int(r["parameter_count"]) for r in fits if r["arm"] == arm})[0] for arm in ARMS}
    summary["training_seconds_by_arm_mean"] = {arm: float(np.mean([float(r["training_seconds"]) for r in fits if r["arm"] == arm])) for arm in ARMS}
    summary["classification"] = "post-result exploratory artificial mechanism-transfer study"
    (args.result_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
