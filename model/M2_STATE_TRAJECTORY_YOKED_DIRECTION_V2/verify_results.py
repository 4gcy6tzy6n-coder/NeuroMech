#!/usr/bin/env python3
"""Independently audit M2 V2 row completeness, sequence coverage, and estimates."""
import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/M2_STATE_TRAJECTORY_YOKED_DIRECTION_V2/final"
SCALES = (0.75, 1.0, 1.25)
SEEDS = range(380000, 380200)
N_BOOT = 20_000
BOOT_SEED = 20261007


def bootstrap(values):
    rng = np.random.default_rng(BOOT_SEED)
    ix = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    boot = values[ix].mean(axis=1)
    return [float(np.quantile(boot, .025)), float(np.quantile(boot, .975))]


def independent_yoke_direction(seed, scale, donor):
    steps, agents = 1500, 50
    movement = np.zeros((steps, agents), dtype=bool)
    latent = np.zeros((steps, agents), dtype=bool)
    chooser = np.random.default_rng(seed + 900_000_000 + int(scale * 1000))
    for agent in range(agents):
        item = donor[int(chooser.integers(0, len(donor)))]
        for key, target in (("movement", movement), ("latent_mode", latent)):
            pos = 0
            for state, length in item[key]:
                target[pos:pos + length, agent] = bool(state)
                pos += length
            assert pos == steps
    rng = np.random.default_rng(seed)
    rng.standard_normal((steps, agents))
    reset = rng.random((steps, agents)) * (2 * math.pi)
    theta = np.empty((steps, agents))
    theta[0] = rng.random(agents) * (2 * math.pi)
    for t in range(1, steps):
        old, previous = latent[max(0, t - 2)], latent[t - 1]
        to_reverse, to_forward = old & ~previous, ~old & previous
        theta[t] = theta[t - 1]
        theta[t, to_reverse] = np.mod(theta[t, to_reverse] + math.pi, 2 * math.pi)
        theta[t, to_forward] = reset[t, to_forward]
    return float((-np.cos(theta) * movement).sum() / movement.sum())


def main():
    with (OUT / "heldout_metrics.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2400, len(rows)
    lookup = {}
    for row in rows:
        key = (int(row["seed_block"]), float(row["noise_scale"]), row["arm"])
        assert key not in lookup, key
        lookup[key] = row
    expected_arms = {"SENSORY_SITE_FB", "MOTOR_MULTI_STAT_MATCHED", "NO_FEEDBACK", "FULL_TRAJECTORY_YOKE"}
    assert len(lookup) == 2400
    assert all({arm for arm in expected_arms} <= {a for (s, n, a) in lookup if s == seed and n == scale}
               for seed in SEEDS for scale in SCALES)
    assert all(math.isfinite(float(row["warm_direction_index"])) for row in rows)

    library = json.loads((OUT / "development_trajectory_library.json").read_text())
    sequence_count = {}
    for scale in SCALES:
        donors = library[str(scale)]
        sequence_count[str(scale)] = len(donors)
        assert len(donors) == 1500
        for item in donors:
            for key in ("movement", "latent_mode"):
                assert sum(length for _, length in item[key]) == 1500
                assert all(state in (0, 1) and length > 0 for state, length in item[key])

    differences = np.asarray([
        np.mean([
            float(lookup[(seed, scale, "SENSORY_SITE_FB")]["warm_direction_index"])
            - float(lookup[(seed, scale, "FULL_TRAJECTORY_YOKE")]["warm_direction_index"])
            for scale in SCALES
        ]) for seed in SEEDS
    ])
    summary = json.loads((OUT / "summary.json").read_text())
    primary = summary["primary"]
    assert abs(float(differences.mean()) - primary["mean"]) < 1e-12
    assert bootstrap(differences) == primary["ci95_seed_block_bootstrap"]
    assert int((differences > 0).sum()) == primary["positive_seed_blocks"] == 200

    replay_check = independent_yoke_direction(380000, 0.75, library["0.75"])
    saved_check = float(lookup[(380000, 0.75, "FULL_TRAJECTORY_YOKE")]["warm_direction_index"])
    assert abs(replay_check - saved_check) < 1e-12
    receipt = {
        "status": "PASS",
        "heldout_rows": len(rows),
        "unique_seed_scale_arm_keys": len(lookup),
        "development_donors_per_scale": sequence_count,
        "all_replayed_sequences_1500_steps": True,
        "primary_mean": float(differences.mean()),
        "primary_bootstrap_95ci": bootstrap(differences),
        "positive_seed_blocks": int((differences > 0).sum()),
        "independent_yoke_replay_check": {"seed": 380000, "noise_scale": 0.75,
                                          "absolute_difference": abs(replay_check - saved_check)},
    }
    (OUT / "POSTRUN_VERIFICATION.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
