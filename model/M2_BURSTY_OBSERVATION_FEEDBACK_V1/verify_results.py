#!/usr/bin/env python3
"""Independent structural and primary-estimand verification."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ARMS = ("SENSORY_SITE", "OUTPUT_SITE", "NO_FEEDBACK", "GENERIC_RNN", "GRU_8")
SEEDS = tuple(range(830100, 830124))
QS = (0.50, 0.25, 0.125)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def bootstrap(diff, rng, nboot=10_000):
    ns, ne = diff.shape
    out = np.empty(nboot)
    for i in range(nboot):
        si = rng.integers(0, ns, size=ns)
        ei = rng.integers(0, ne, size=(ns, ne))
        out[i] = diff[si[:, None], ei].mean()
    return [float(np.quantile(out, .025)), float(np.quantile(out, .975))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_dir", type=Path)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--runner", type=Path, required=True)
    args = ap.parse_args()
    out = args.result_dir
    ep = rows(out / "episode_results.csv")
    fit = rows(out / "training_results.csv")
    meta = json.loads((out / "RUN_METADATA.json").read_text())
    pre = json.loads((out / "PREFLIGHT.json").read_text())
    expected = len(SEEDS) * len(QS) * 128 * len(ARMS)
    keys = [(int(r["training_seed"]), float(r["visibility_q"]), int(r["episode_id"]), r["arm"]) for r in ep]
    assert len(ep) == expected, (len(ep), expected)
    assert len(set(keys)) == expected, "duplicate episode key"
    assert set(int(r["training_seed"]) for r in ep) == set(SEEDS)
    assert set(float(r["visibility_q"]) for r in ep) == set(QS)
    assert set(r["arm"] for r in ep) == set(ARMS)
    assert all(0 <= float(r["tracking_mse"]) < 4 for r in ep)
    assert all(0 <= float(r["action_energy"]) <= 1 for r in ep)
    visibility = {}
    for r in ep:
        k = (int(r["training_seed"]), float(r["visibility_q"]), int(r["episode_id"]))
        frac = float(r["missing_fraction"])
        assert 0 <= frac <= 1
        if k in visibility:
            assert visibility[k] == frac, "paired policies did not receive identical visibility streams"
        visibility[k] = frac
    for q in QS:
        realized = np.mean([v for (s, qq, e), v in visibility.items() if qq == q])
        assert abs(realized - .5) < .01, (q, realized)
    assert len(fit) == len(SEEDS) * len(ARMS)
    params = {a: {int(r["parameter_count"]) for r in fit if r["arm"] == a} for a in ARMS}
    assert all(len(params[a]) == 1 for a in ARMS)
    assert all(next(iter(params[a])) == 4 for a in ARMS if a != "GRU_8"), params
    assert next(iter(params["GRU_8"])) == 321, params
    assert all(int(r["updates"]) == 60 and int(r["sequence_steps_per_fit"]) == 60 * 16 * 160 for r in fit)
    assert meta["contract_sha256"] == sha(args.contract)
    assert meta["runner_sha256"] == sha(args.runner)
    assert pre["contract_sha256"] == sha(args.contract) and pre["runner_sha256"] == sha(args.runner)
    lookup = {(int(r["training_seed"]), float(r["visibility_q"]), int(r["episode_id"]), r["arm"]): r for r in ep}
    seed_ids = sorted(SEEDS)
    rng = np.random.default_rng(20261001)
    contrasts = {}
    q = .125
    for arm in ("OUTPUT_SITE", "GENERIC_RNN", "GRU_8", "NO_FEEDBACK"):
        d = np.array([[float(lookup[(s, q, e, arm)]["tracking_mse"]) -
                       float(lookup[(s, q, e, "SENSORY_SITE")]["tracking_mse"])
                       for e in range(128)] for s in seed_ids])
        contrasts[arm] = {"mean": float(d.mean()), "ci95": bootstrap(d, rng),
                          "positive_seed_means": int((d.mean(axis=1) > 0).sum())}
    summary = json.loads((out / "summary.json").read_text())
    for q in QS:
        realized = np.mean([v for (s, qq, e), v in visibility.items() if qq == q])
        assert abs(summary["conditions"][str(q)]["realized_mean_missing_fraction"] - realized) < 1e-12
    for arm, calc in contrasts.items():
        recorded = summary["primary"][f"{arm}_minus_SENSORY_SITE"]
        assert abs(recorded["mean_difference"] - calc["mean"]) < 1e-12
        assert np.allclose(recorded["ci95_crossed_seed_episode"], calc["ci95"], atol=1e-12, rtol=0)
        assert recorded["positive_seed_means"] == calc["positive_seed_means"]
    report = {"status": "PASS", "scope": "schema, complete grid, parameter/update accounting, source pinning, primary estimate and bootstrap independently recomputed",
              "episode_rows": len(ep), "fit_rows": len(fit), "parameter_counts": {k: next(iter(v)) for k, v in params.items()},
              "primary_recomputed": contrasts,
              "sha256": {p.name: sha(p) for p in (out / "episode_results.csv", out / "training_results.csv", out / "summary.json")}}
    (out / "POSTRUN_VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
