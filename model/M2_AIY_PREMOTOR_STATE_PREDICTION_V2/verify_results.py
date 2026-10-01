#!/usr/bin/env python3
"""Independent arithmetic and score audit for the V2 source-trace analysis."""
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
LAGS = (0, 1, 2, 4, 10)
HORIZONS = (1, 4, 10)
PURGE = 40


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_source():
    p = ROOT / "model/M2_AIY_STATE_CONDITIONAL_ENCODING_V1/analyze_source_data.py"
    spec = importlib.util.spec_from_file_location("source_parser_audit", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_animals()


def independent_score(state, signal, horizon):
    n = len(state)
    origin = np.arange(max(LAGS), n - horizon)
    history = np.stack([state[origin - lag] for lag in LAGS], axis=1)
    future = np.stack([state[origin + k] for k in range(1, horizon + 1)], axis=1)
    known = np.isin(future, (-1, 1))
    keep = (state[origin] == 1) & np.isin(history, (-1, 1)).all(axis=1)
    keep &= known.any(axis=1) & np.isfinite(signal[origin])
    first = future[np.arange(len(origin)), known.argmax(axis=1)]
    origin, history, first = origin[keep], history[keep], first[keep]
    y = (first == -1).astype(int)
    x0 = history.astype(float)
    x1 = np.c_[x0, signal[origin]]
    predictions = [np.full(len(y), np.nan), np.full(len(y), np.nan)]
    edges = np.linspace(0, n, 11, dtype=int)
    for j in range(10):
        lo, hi = edges[j], edges[j + 1]
        tst = (origin >= lo) & (origin < hi)
        trn = ((origin < max(0, lo - PURGE)) | (origin >= min(n, hi + PURGE))) & ~tst
        if not tst.any() or np.unique(y[trn]).size != 2:
            continue
        for arm, x in enumerate((x0, x1)):
            standardizer = StandardScaler().fit(x[trn])
            learner = LogisticRegression(C=1.0, solver="liblinear", random_state=0)
            learner.fit(standardizer.transform(x[trn]), y[trn])
            predictions[arm][tst] = learner.predict_proba(standardizer.transform(x[tst]))[:, 1]
    valid = np.isfinite(predictions[0]) & np.isfinite(predictions[1])
    if valid.sum() < 50 or np.unique(y[valid]).size != 2:
        return None
    return {"n": int(valid.sum()), "positives": int(y[valid].sum()),
            "baseline": float(roc_auc_score(y[valid], predictions[0][valid])),
            "augmented": float(roc_auc_score(y[valid], predictions[1][valid]))}


def main():
    out = ROOT / "data/results" / EXP
    observed = pd.read_csv(out / "animal_horizon_results.csv")
    animals, source_files = load_source()
    expected = {}
    for animal in animals:
        for horizon in HORIZONS:
            for neuron in ("aiy", "ava"):
                score = independent_score(animal["state"], animal[neuron], horizon)
                expected[(animal["animal_id"], horizon, neuron.upper())] = score
    errors = []
    for rec in observed.to_dict(orient="records"):
        key = (rec["animal_id"], int(rec["horizon_samples"]), rec["neural_signal"])
        exp = expected[key]
        if exp is None:
            if pd.notna(rec["baseline_history_auc"]):
                errors.append(f"{key}: expected unscorable but row contains an AUC")
            continue
        checks = (("candidate_samples", exp["n"]), ("positive_samples", exp["positives"]),
                  ("oof_samples", exp["n"]), ("baseline_history_auc", exp["baseline"]),
                  ("history_plus_neural_auc", exp["augmented"]),
                  ("incremental_auc", exp["augmented"] - exp["baseline"]))
        for field, value in checks:
            if not np.isclose(float(rec[field]), float(value), rtol=0, atol=1e-10):
                errors.append(f"{key}/{field}: observed={rec[field]} expected={value}")
    if len(observed) != len(expected):
        errors.append(f"row count {len(observed)} != expected {len(expected)}")
    summary = json.loads((out / "summary.json").read_text())
    for p in source_files:
        entry = next(x for x in summary["source_files"] if x["filename"] == p.name)
        if entry["bytes"] != p.stat().st_size or entry["sha256"] != digest(p):
            errors.append(f"source hash mismatch: {p.name}")
    primary = observed[(observed.horizon_samples == 4) & (observed.neural_signal == "AIY")]
    for group, frame in primary.groupby("group"):
        vals = frame.incremental_auc.dropna().to_numpy(float)
        saved = summary["group_summaries"][group]["primary_incremental_auc"]
        if len(vals) != saved["n_animals"] or (len(vals) and not np.isclose(vals.mean(), saved["mean"], atol=1e-12)):
            errors.append(f"group summary mismatch: {group}")
    for neuron in ("AIY", "AVA"):
        frame = observed[(observed.horizon_samples == 4) & (observed.neural_signal == neuron)]
        wt = frame.loc[frame.group == "WT", "incremental_auc"].dropna().to_numpy(float)
        rim = frame.loc[frame.group == "RIM_ABLATED", "incremental_auc"].dropna().to_numpy(float)
        saved = summary["primary_group_contrasts_descriptive_only"][neuron]
        if len(wt) and len(rim):
            contrast = float(wt.mean() - rim.mean())
            if not np.isclose(contrast, saved["WT_minus_RIM_ABLATED"], atol=1e-12):
                errors.append(f"group contrast mismatch: {neuron}")
            pool = np.r_[wt, rim]
            import itertools
            diffs = []
            for subset in itertools.combinations(range(len(pool)), len(wt)):
                mask = np.zeros(len(pool), dtype=bool)
                mask[list(subset)] = True
                diffs.append(pool[mask].mean() - pool[~mask].mean())
            p = float(np.mean(np.abs(diffs) >= abs(contrast) - 1e-15))
            if len(diffs) != saved["permutations"] or not np.isclose(p, saved["exact_label_permutation_p_descriptive_only"], atol=1e-15):
                errors.append(f"permutation summary mismatch: {neuron}")
    if errors:
        raise SystemExit("FAIL\n" + "\n".join(errors[:30]))
    print(json.dumps({"status": "PASS", "independently_recomputed_rows": len(expected),
                      "source_files_verified": len(source_files),
                      "v2_half_second_horizon_unscorable_rim_animals": int(observed[(observed.horizon_samples == 1) & (observed.neural_signal == "AIY")].query("group == 'RIM_ABLATED'").baseline_history_auc.isna().sum())}, indent=2))


if __name__ == "__main__":
    main()
