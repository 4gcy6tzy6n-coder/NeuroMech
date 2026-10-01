#!/usr/bin/env python3
"""Independent structural and arithmetic audit for the M2 compute frontier."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_BURSTY_COMPUTE_FRONTIER_V1"
OUT = ROOT / "data" / "results" / EXP
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
RUNNER = ROOT / "model" / EXP / "run_experiment.py"
PLOTTER = ROOT / "model" / EXP / "plot_frontier.py"
RESULTS_DOC = ROOT / "summery" / EXP / "RESULTS.md"
FAILURE_DOC = ROOT / "summery" / EXP / "FAILURE_LOG.md"
FEISHU_ENTRY = ROOT / "summery" / EXP / "FEISHU_ENTRY.md"
SEEDS = list(range(840500, 840532))
ARMS = ["SENSORY_SITE", "OUTPUT_SITE", "NO_FEEDBACK", "GENERIC_RNN", "GRU_8"]
CHECKPOINTS = [60, 120, 240]
Q_VALUES = [0.50, 0.25, 0.125]
NTEST = 128
NBOOT = 20_000
BOOT_SEED = 20261002


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bootstrap(values: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(values), size=(NBOOT, len(values)))
    lo, hi = np.quantile(values[idx].mean(axis=1), [0.025, 0.975])
    return float(lo), float(hi)


def cluster_summary(values: np.ndarray) -> dict:
    values = values[np.isfinite(values)]
    low, high = bootstrap(values)
    return {"mean_seed_block": float(values.mean()), "bootstrap_95ci_low": low,
            "bootstrap_95ci_high": high, "seed_blocks": int(len(values))}


def main():
    episode_path = OUT / "episode_results.csv"
    checkpoint_path = OUT / "checkpoint_results.csv"
    episodes, checkpoints = read_csv(episode_path), read_csv(checkpoint_path)
    expected_episode_rows = len(SEEDS) * len(ARMS) * len(CHECKPOINTS) * len(Q_VALUES) * NTEST
    expected_checkpoint_rows = len(SEEDS) * len(ARMS) * len(CHECKPOINTS)
    if len(episodes) != expected_episode_rows or len(checkpoints) != expected_checkpoint_rows:
        raise AssertionError(f"row counts episodes={len(episodes)} checkpoints={len(checkpoints)}")

    keys = set()
    grouped: dict[tuple[int, str, int, float], list[dict]] = {}
    for row in episodes:
        seed, arm, updates = int(row["training_seed"]), row["arm"], int(row["optimizer_updates"])
        q, episode = float(row["visibility_q"]), int(row["episode_id"])
        key = (seed, arm, updates, q, episode)
        if key in keys:
            raise AssertionError(f"duplicate episode key: {key}")
        keys.add(key)
        if seed not in SEEDS or arm not in ARMS or updates not in CHECKPOINTS or q not in Q_VALUES or not 0 <= episode < NTEST:
            raise AssertionError(f"unexpected key: {key}")
        for field in ("missing_fraction", "tracking_mse", "tracking_mae", "action_energy"):
            v = float(row[field])
            if not np.isfinite(v) or v < 0:
                raise AssertionError(f"invalid {field} for {key}: {v}")
        grouped.setdefault((seed, arm, updates, q), []).append(row)
    if len(grouped) != len(SEEDS) * len(ARMS) * len(CHECKPOINTS) * len(Q_VALUES):
        raise AssertionError("missing seed × arm × checkpoint × q cells")
    if any(len(v) != NTEST for v in grouped.values()):
        raise AssertionError("evaluation episode count mismatch")

    check_keys = set()
    parameters = {}
    for row in checkpoints:
        key = (int(row["training_seed"]), row["arm"], int(row["optimizer_updates"]))
        if key in check_keys:
            raise AssertionError(f"duplicate checkpoint: {key}")
        check_keys.add(key)
        count = int(row["parameter_count"])
        parsed = json.loads(row["parameters_json"])
        flat = [float(x) for values in parsed.values() for x in values]
        if len(flat) != count or not np.isfinite(flat).all():
            raise AssertionError(f"parameter state mismatch for {key}")
        if float(row["training_seconds_cumulative"]) <= 0:
            raise AssertionError(f"invalid training time for {key}")
        parameters.setdefault(row["arm"], set()).add(count)
    if any(len(v) != 1 for v in parameters.values()):
        raise AssertionError(f"parameter count varies by arm: {parameters}")

    def outcome(seed, arm, updates, q, column):
        vals = [float(r[column]) for r in grouped[(seed, arm, updates, q)] if r[column] != ""]
        return float(np.mean(vals)) if vals else float("nan")

    contrasts = []
    for updates in CHECKPOINTS:
        for q in Q_VALUES:
            for comparator in ("OUTPUT_SITE", "NO_FEEDBACK", "GENERIC_RNN", "GRU_8"):
                effects = np.asarray([
                    outcome(seed, comparator, updates, q, "tracking_mse")
                    - outcome(seed, "SENSORY_SITE", updates, q, "tracking_mse")
                    for seed in SEEDS
                ])
                low, high = bootstrap(effects)
                contrasts.append({
                    "checkpoint_updates": updates, "visibility_q": q,
                    "contrast": f"{comparator}_MSE_MINUS_SENSORY_SITE_MSE",
                    "mean_paired_seed_effect": float(effects.mean()),
                    "bootstrap_95ci_low": low, "bootstrap_95ci_high": high,
                    "positive_seed_blocks": int(np.sum(effects > 0)), "seed_blocks": len(SEEDS),
                })
    arm_metrics = []
    for updates in CHECKPOINTS:
        for q in Q_VALUES:
            for arm in ARMS:
                for metric in ("tracking_mse", "tracking_mae", "action_energy", "post_gap_recovery_steps"):
                    seed_values = np.asarray([
                        outcome(seed, arm, updates, q, metric) for seed in SEEDS
                    ])
                    row = {"checkpoint_updates": updates, "visibility_q": q, "arm": arm, "metric": metric}
                    row.update(cluster_summary(seed_values))
                    arm_metrics.append(row)
    primary = [x for x in contrasts if x["checkpoint_updates"] == 240 and x["visibility_q"] == 0.125
               and x["contrast"] in {"GENERIC_RNN_MSE_MINUS_SENSORY_SITE_MSE", "GRU_8_MSE_MINUS_SENSORY_SITE_MSE"}]
    summary = {
        "experiment_id": EXP,
        "status": "POST_RESULT_EXPLORATORY_ARTIFICIAL_EXPERIMENT",
        "primary_condition": {"optimizer_updates": 240, "visibility_q": 0.125},
        "primary_contrasts": primary,
        "all_tracking_mse_contrasts": contrasts,
        "arm_metric_summaries": arm_metrics,
        "resource_accounting": {arm: {"parameter_count": next(iter(parameters[arm]))} for arm in ARMS},
        "row_counts": {"episode_results": len(episodes), "checkpoint_results": len(checkpoints)},
        "independent_blocks": len(SEEDS), "episodes_per_cell": NTEST,
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    verification = {
        "experiment_id": EXP, "passed": True,
        "checks": {
            "episode_grid_complete": True, "checkpoint_grid_complete": True,
            "no_duplicate_rows": True, "metrics_finite_nonnegative": True,
            "parameter_state_counts_consistent": True, "seed_clustered_contrasts_recomputed": True,
            "primary_condition_prespecified_in_contract": (
                "Primary condition: long-gap evaluation `q=0.125` at 240 updates" in CONTRACT.read_text()
            ),
        },
        "row_counts": summary["row_counts"],
        "input_sha256": {p.name: sha(p) for p in (episode_path, checkpoint_path, CONTRACT, RUNNER)},
        "verifier_sha256": sha(Path(__file__)),
    }
    if not verification["checks"]["primary_condition_prespecified_in_contract"]:
        raise AssertionError("primary condition missing from frozen contract")
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n")
    figure_paths = [OUT / "figures" / f"{EXP}.{suffix}" for suffix in ("png", "svg", "pdf")]
    if not all(p.is_file() and p.stat().st_size > 0 for p in figure_paths):
        raise AssertionError("one or more required figure exports are missing")
    sums = [f"{sha(p)}  {p.relative_to(ROOT)}" for p in
            (CONTRACT, RESULTS_DOC, FAILURE_DOC, FEISHU_ENTRY, RUNNER, PLOTTER, Path(__file__),
             OUT / "PREFLIGHT.json", OUT / "RUN_METADATA.json", episode_path, checkpoint_path,
             summary_path, *figure_paths, OUT / "POSTRUN_VERIFICATION.json")]
    (OUT / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    print(json.dumps({"passed": True, "primary_contrasts": primary, "row_counts": summary["row_counts"]}, indent=2))


if __name__ == "__main__":
    main()
