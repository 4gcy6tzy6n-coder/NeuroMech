#!/usr/bin/env python3
"""Run the frozen exploratory CA3-inspired partial-cue benchmark."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_v2_unclamped_method_correction"
N = 120
LOADS = (0.05, 0.10, 0.15, 0.20)
VISIBLE_FRACTIONS = (0.2, 0.4, 0.6, 0.8, 1.0)
FLIP_RATES = (0.0, 0.1, 0.2)
N_SEEDS = 25
N_QUERIES = 10
MAX_SWEEPS = 100
BOOTSTRAPS = 5000


def hopfield_recall(patterns: np.ndarray, weights: np.ndarray, cue: np.ndarray, observed: np.ndarray,
                    rng: np.random.Generator) -> tuple[np.ndarray, bool, int]:
    n = patterns.shape[1]
    state = np.zeros(n, dtype=np.int8)
    state[observed] = cue[observed]
    for sweep in range(1, MAX_SWEEPS + 1):
        changed = False
        for idx in rng.permutation(n):
            field = float(weights[idx] @ state)
            new_value = 1 if field > 0 else -1 if field < 0 else (int(state[idx]) or 1)
            if new_value != state[idx]:
                state[idx] = new_value
                changed = True
        if not changed:
            return state, True, sweep
    return state, False, MAX_SWEEPS


def map_exemplar(patterns: np.ndarray, cue: np.ndarray,
                 observed: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, int]:
    distances = np.count_nonzero(patterns[:, observed] != cue[observed], axis=1)
    winners = np.flatnonzero(distances == distances.min())
    return patterns[int(rng.choice(winners))].copy(), int(winners.size)


def bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    draws = rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))
    means = values[draws].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    per_seed: dict[tuple[float, float, float], dict[int, dict[str, list[float]]]] = {}

    for load in LOADS:
        p_count = max(1, int(round(N * load)))
        for seed in range(N_SEEDS):
            rng = np.random.default_rng(2026093000 + seed + int(load * 10000))
            patterns = rng.choice(np.array([-1, 1], dtype=np.int8), size=(p_count, N))
            weights = patterns.T @ patterns / N
            np.fill_diagonal(weights, 0.0)
            for query in range(N_QUERIES):
                target_idx = int(rng.integers(p_count))
                target = patterns[target_idx]
                for visible_fraction in VISIBLE_FRACTIONS:
                    observed = rng.random(N) < visible_fraction
                    if not observed.any():
                        observed[int(rng.integers(N))] = True
                    for flip_rate in FLIP_RATES:
                        cue = target.copy()
                        flips = observed & (rng.random(N) < flip_rate)
                        cue[flips] *= -1
                        recurrent_rng = np.random.default_rng(rng.integers(0, 2**63 - 1))
                        map_rng = np.random.default_rng(rng.integers(0, 2**63 - 1))

                        rec, converged, sweeps = hopfield_recall(patterns, weights, cue, observed, recurrent_rng)
                        exemplar, n_tied = map_exemplar(patterns, cue, observed, map_rng)
                        visible_patterns = patterns[:, observed]
                        distances = np.count_nonzero(visible_patterns != cue[observed], axis=1)
                        cue_ambiguous = int(np.count_nonzero(distances == distances.min()) > 1)
                        key = (load, visible_fraction, flip_rate)
                        per_seed.setdefault(key, {}).setdefault(seed, {"recurrent": [], "map": []})
                        per_seed[key][seed]["recurrent"].append(float(np.array_equal(rec, target)))
                        per_seed[key][seed]["map"].append(float(np.array_equal(exemplar, target)))

                        for method, output, extra in (
                            ("hebbian_recurrent", rec, {"converged": int(converged), "sweeps": sweeps, "tie_count": ""}),
                            ("exact_exemplar_map", exemplar, {"converged": "", "sweeps": "", "tie_count": n_tied}),
                        ):
                            records.append({
                                "load_fraction": load,
                                "memory_count": p_count,
                                "seed": seed,
                                "query": query,
                                "visible_fraction": visible_fraction,
                                "flip_rate": flip_rate,
                                "cue_ambiguous": cue_ambiguous,
                                "method": method,
                                "exact_recall": int(np.array_equal(output, target)),
                                "bit_accuracy": float(np.mean(output == target)),
                                "output_not_in_memory": int(method == "hebbian_recurrent" and not np.any(np.all(patterns == output, axis=1))),
                                **extra,
                            })

    with (OUT / "trial_results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    bootstrap_rng = np.random.default_rng(941703)
    summaries = []
    for (load, visible_fraction, flip_rate), seed_rows in sorted(per_seed.items()):
        rec_seed = np.array([np.mean(seed_rows[s]["recurrent"]) for s in sorted(seed_rows)])
        map_seed = np.array([np.mean(seed_rows[s]["map"]) for s in sorted(seed_rows)])
        delta = rec_seed - map_seed
        lo, hi = bootstrap_mean_ci(delta, bootstrap_rng)
        summaries.append({
            "load_fraction": load,
            "memory_count": max(1, int(round(N * load))),
            "exemplar_storage_bits_ignoring_metadata": max(1, int(round(N * load))) * N,
            "dense_float32_weight_storage_bits": N * N * 32,
            "dense_weights_to_exemplar_storage_ratio": (N * N * 32) / (max(1, int(round(N * load))) * N),
            "visible_fraction": visible_fraction,
            "flip_rate": flip_rate,
            "recurrent_exact_recall": float(rec_seed.mean()),
            "map_exact_recall": float(map_seed.mean()),
            "paired_delta_recurrent_minus_map": float(delta.mean()),
            "seed_cluster_bootstrap_95ci_low": lo,
            "seed_cluster_bootstrap_95ci_high": hi,
            "seeds": N_SEEDS,
            "queries_per_seed": N_QUERIES,
        })
    seed_deltas: dict[int, list[float]] = {seed: [] for seed in range(N_SEEDS)}
    for seed_rows in per_seed.values():
        for seed, method_rows in seed_rows.items():
            seed_deltas[seed].extend(np.asarray(method_rows["recurrent"]) - np.asarray(method_rows["map"]))
    overall_seed_delta = np.array([np.mean(seed_deltas[seed]) for seed in sorted(seed_deltas)])
    overall_ci = bootstrap_mean_ci(overall_seed_delta, bootstrap_rng)
    with (OUT / "summary.json").open("w") as f:
        json.dump({"contract": str((ROOT / "EXPLORATORY_BENCHMARK_CONTRACT.md").relative_to(ROOT.parent.parent)),
                   "n": N, "loads": LOADS, "visible_fractions": VISIBLE_FRACTIONS,
                   "flip_rates": FLIP_RATES, "seeds": N_SEEDS, "queries_per_seed": N_QUERIES,
                   "overall_seed_cluster_delta_recurrent_minus_map": float(overall_seed_delta.mean()),
                   "overall_seed_cluster_bootstrap_95ci": list(overall_ci),
                   "rows": summaries}, f, indent=2)

    print(f"wrote {len(records)} trial rows and {len(summaries)} condition summaries to {OUT}")


if __name__ == "__main__":
    main()
