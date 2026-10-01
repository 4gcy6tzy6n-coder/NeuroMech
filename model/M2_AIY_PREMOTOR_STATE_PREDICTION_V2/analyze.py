#!/usr/bin/env python3
"""Blocked animal-level prediction of impending reversals from Ji et al. traces."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_AIY_PREMOTOR_STATE_PREDICTION_V2"
FOLDS = 10
PURGE_SAMPLES = 40  # 20 s at the source's 2 Hz sampling rate
HORIZONS = {1: "0.5s_secondary", 4: "2s_primary", 10: "5s_secondary"}
STATE_LAGS = (0, 1, 2, 4, 10)  # 0, 0.5, 1, 2, 5 s before forecast origin


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def source_animals():
    source_path = ROOT / "model/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/analyze_source_data.py"
    spec = importlib.util.spec_from_file_location("m2_source_parser", source_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.load_animals()


def assemble(state: np.ndarray, signal: np.ndarray, horizon: int):
    n = len(state)
    rows = np.arange(max(STATE_LAGS), n - horizon)
    xstate = np.column_stack([state[rows - lag] for lag in STATE_LAGS])
    future = np.column_stack([state[rows + step] for step in range(1, horizon + 1)])
    # Source label 0 marks a transition/unknown sample. Treat it as interval-censored:
    # target the first known motor state within the forecast window, skipping zeros.
    known = np.isin(future, (-1, 1))
    has_known = known.any(axis=1)
    first_known = future[np.arange(len(rows)), known.argmax(axis=1)]
    valid = (state[rows] == 1) & np.isin(xstate, (-1, 1)).all(axis=1)
    valid &= has_known & np.isfinite(signal[rows])
    rows = rows[valid]
    base = xstate[valid].astype(float)
    y = (first_known[valid] == -1).astype(int)
    augmented = np.column_stack([base, signal[rows]])
    return rows, base, augmented, y


def blocked_oof_auc(rows, x, y, n_raw):
    pred = np.full(len(rows), np.nan)
    bounds = np.linspace(0, n_raw, FOLDS + 1, dtype=int)
    for fold in range(FOLDS):
        lo, hi = bounds[fold], bounds[fold + 1]
        test = (rows >= lo) & (rows < hi)
        train = ((rows < max(0, lo - PURGE_SAMPLES)) |
                 (rows >= min(n_raw, hi + PURGE_SAMPLES)))
        train &= ~test
        if test.sum() == 0 or np.unique(y[train]).size < 2:
            continue
        scaler = StandardScaler().fit(x[train])
        clf = LogisticRegression(C=1.0, solver="liblinear", random_state=0)
        clf.fit(scaler.transform(x[train]), y[train])
        pred[test] = clf.predict_proba(scaler.transform(x[test]))[:, 1]
    ok = np.isfinite(pred)
    if ok.sum() < 50 or np.unique(y[ok]).size != 2:
        return None, int(ok.sum())
    return float(roc_auc_score(y[ok], pred[ok])), int(ok.sum())


def summarize(vals, seed, draws=50000):
    vals = np.asarray(vals, dtype=float)
    if len(vals) == 0:
        return {"n_animals": 0, "mean": None, "median": None, "animal_values": [],
                "animal_bootstrap_95pct_interval": None, "status": "NOT_ESTIMABLE_NO_SCORED_ANIMALS"}
    rng = np.random.default_rng(seed)
    boot = rng.choice(vals, size=(draws, len(vals)), replace=True).mean(axis=1)
    return {"n_animals": int(len(vals)), "mean": float(vals.mean()),
            "median": float(np.median(vals)), "animal_values": vals.tolist(),
            "animal_bootstrap_95pct_interval": [float(x) for x in np.quantile(boot, [0.025, 0.975])]}


def group_contrast(frame, metric, seed, draws=50000):
    wt = frame.loc[frame.group == "WT", metric].dropna().to_numpy(float)
    rim = frame.loc[frame.group == "RIM_ABLATED", metric].dropna().to_numpy(float)
    if len(wt) == 0 or len(rim) == 0:
        return {"status": "NOT_ESTIMABLE", "n_WT": int(len(wt)), "n_RIM_ABLATED": int(len(rim))}
    rng = np.random.default_rng(seed)
    boot = (rng.choice(wt, (draws, len(wt)), replace=True).mean(axis=1) -
            rng.choice(rim, (draws, len(rim)), replace=True).mean(axis=1))
    pooled = np.r_[wt, rim]
    diffs = []
    import itertools
    for chosen in itertools.combinations(range(len(pooled)), len(wt)):
        mask = np.zeros(len(pooled), dtype=bool)
        mask[list(chosen)] = True
        diffs.append(pooled[mask].mean() - pooled[~mask].mean())
    observed = float(wt.mean() - rim.mean())
    p = float(np.mean(np.abs(diffs) >= abs(observed) - 1e-15))
    return {"status": "DESCRIPTIVE_SMALL_COHORT", "n_WT": int(len(wt)), "n_RIM_ABLATED": int(len(rim)),
            "WT_minus_RIM_ABLATED": observed,
            "independent_animal_bootstrap_95pct_interval": [float(x) for x in np.quantile(boot, [0.025, 0.975])],
            "exact_label_permutation_p_descriptive_only": p, "permutations": len(diffs)}


def main():
    out = ROOT / "data/results" / EXP
    out.mkdir(parents=True, exist_ok=True)
    animals, source_files = source_animals()
    rows_out = []
    for animal in animals:
        if not np.all(np.diff(animal["time"]) > 0) or not 0.45 <= np.median(np.diff(animal["time"])) <= 0.55:
            raise ValueError(f"Unexpected time axis: {animal['animal_id']}")
        for horizon, horizon_name in HORIZONS.items():
            for neuron in ("aiy", "ava"):
                rows, xbase, xaug, y = assemble(animal["state"], animal[neuron], horizon)
                base_auc, n_base = blocked_oof_auc(rows, xbase, y, len(animal["state"]))
                aug_auc, n_aug = blocked_oof_auc(rows, xaug, y, len(animal["state"]))
                rows_out.append({"group": animal["group"], "animal_id": animal["animal_id"],
                                 "horizon_samples": horizon, "horizon": horizon_name,
                                 "neural_signal": neuron.upper(), "candidate_samples": len(y),
                                 "positive_samples": int(y.sum()), "negative_samples": int(len(y) - y.sum()),
                                 "event_prevalence": float(y.mean()) if len(y) else None,
                                 "baseline_history_auc": base_auc, "history_plus_neural_auc": aug_auc,
                                 "incremental_auc": (aug_auc - base_auc) if base_auc is not None and aug_auc is not None else None,
                                 "oof_samples": min(n_base, n_aug)})

    result = pd.DataFrame(rows_out)
    result.to_csv(out / "animal_horizon_results.csv", index=False, float_format="%.10g")
    summary = {"experiment_id": EXP, "classification": "retrospective_outcome_informed_exploratory_reanalysis",
               "primary_horizon": "2s", "primary_endpoint": "animal-level OOF AUC(history + AIY) - AUC(history)",
               "unit": "animal", "folds": FOLDS, "purge_samples": PURGE_SAMPLES,
               "state_lags_samples": list(STATE_LAGS), "group_summaries": {}, "source_files": []}
    for p in source_files:
        summary["source_files"].append({"filename": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)})
    primary = result[(result.horizon_samples == 4) & (result.neural_signal == "AIY")]
    for group, frame in primary.groupby("group"):
        valid = frame.dropna(subset=["incremental_auc"])
        summary["group_summaries"][group] = {
            "n_total_animals": int(len(frame)), "n_scored_animals": int(len(valid)),
            "primary_incremental_auc": summarize(valid.incremental_auc.to_numpy(), 20261012),
            "animal_rows": frame.to_dict(orient="records")}
    summary["primary_group_contrasts_descriptive_only"] = {
        neuron: group_contrast(result[(result.horizon_samples == 4) & (result.neural_signal == neuron)],
                               "incremental_auc", 20261013)
        for neuron in ("AIY", "AVA")}
    summary["all_animal_rows"] = rows_out
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    contract = ROOT / "summery" / EXP / "CONTRACT.md"
    manifest = {"experiment_id": EXP, "runner_sha256": sha256(Path(__file__)),
                "contract_sha256": sha256(contract),
                "outputs": {p.name: sha256(p) for p in (out / "animal_horizon_results.csv", out / "summary.json")}}
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({g: s["primary_incremental_auc"] for g, s in summary["group_summaries"].items()}, indent=2))


if __name__ == "__main__":
    main()
