#!/usr/bin/env python3
"""Paired-seed follow-up contrasts for the interval-timing transfer run."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = "M5_CEREBELLAR_INTERVAL_TIMING_TRANSFER_V1"
RESULTS = ROOT / "data/results" / EXP
SOURCE = RESULTS / "episode_results.csv"
NBOOT = 20000
BOOT_SEED = 20261015


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ci(v):
    rng = np.random.default_rng(BOOT_SEED)
    ix = rng.integers(0, len(v), size=(NBOOT, len(v)))
    return [float(x) for x in np.quantile(v[ix].mean(axis=1), [0.025, 0.975])]


def main():
    grouped = defaultdict(list)
    with SOURCE.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            grouped[(row["mapping"], row["arm"], int(row["task_seed"]))].append(float(row["absolute_error_seconds"]))
    means = {k: float(np.mean(v)) for k, v in grouped.items()}
    seeds = sorted({k[2] for k in means})
    contrasts = []
    for mapping in ("ALIGNED", "REVERSED"):
        for left, right in (("GRU_PROFILE_BPTT", "GRU_CLOCK_BPTT"),
                            ("BIO_PROFILE_ELIGIBILITY", "BIO_PROFILE_NO_TRACE"),
                            ("BIO_PROFILE_ELIGIBILITY", "GENERIC_RBF_ELIGIBILITY"),
                            ("BIO_PROFILE_ELIGIBILITY", "GRU_PROFILE_BPTT"),
                            ("BIO_PROFILE_ELIGIBILITY", "EMPIRICAL_TIMER")):
            d = np.array([means[(mapping, left, s)] - means[(mapping, right, s)] for s in seeds])
            contrasts.append({"mapping": mapping, "contrast": f"{left}_MINUS_{right}",
                              "mean_error_difference_seconds": float(d.mean()),
                              "seed_bootstrap_95ci": ci(d), "positive_seeds": int(np.sum(d > 0)),
                              "seeds": len(seeds), "resampling_unit": "task seed"})
    out = RESULTS / "supplementary_paired_contrasts.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(contrasts[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(contrasts)
    meta = {"experiment_id": EXP, "source_results_sha256": sha(SOURCE),
            "analysis_script_sha256": sha(Path(__file__)), "bootstrap_resamples": NBOOT,
            "bootstrap_seed": BOOT_SEED, "unit": "paired task seed",
            "output_sha256": sha(out), "contrasts": contrasts,
            "status": "exploratory supplementary analysis; no new task data or model fit"}
    (RESULTS / "SUPPLEMENTARY_ANALYSIS.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(contrasts, indent=2))


if __name__ == "__main__": main()
