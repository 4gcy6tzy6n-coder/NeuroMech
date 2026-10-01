#!/usr/bin/env python3
"""Map delayed-credit accuracy against a bounded active feature-state budget."""
from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = "M5_ELIGIBILITY_MEMORY_FRONTIER_V1"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
OUT = ROOT / "data" / "results" / EXP / "canonical"
MASTER = 20261002
N_INPUT, N_FEATURES, N_CLASSES = 32, 64, 4
N_TRAIN, N_TEST = 3000, 1000
SEEDS, DELAYS, GAMMA, LR = tuple(range(100, 130)), (1, 4, 16, 64), 0.98, 0.01
GENERATORS = ("IID_GAUSSIAN", "AR1_GAUSSIAN", "SPARSE_SIGN")
ARMS = ("ELIGIBILITY_TRACE_64", "EXACT_FIFO_64", "EXACT_FIFO_256", "EXACT_FIFO_1024",
        "EXACT_FIFO_4096", "CURRENT_FEATURE_64", "EXACT_REPLAY_UNBOUNDED")
CAPACITY = {"EXACT_FIFO_64": 1, "EXACT_FIFO_256": 4, "EXACT_FIFO_1024": 16,
            "EXACT_FIFO_4096": 64}
BOOTSTRAPS = 20_000


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_stream(rng: np.random.Generator, family: str, n: int) -> np.ndarray:
    if family == "IID_GAUSSIAN":
        return rng.normal(size=(n, N_INPUT))
    if family == "AR1_GAUSSIAN":
        x = np.empty((n, N_INPUT), dtype=np.float64)
        x[0] = rng.normal(size=N_INPUT)
        scale = np.sqrt(1 - 0.8**2)
        for t in range(1, n):
            x[t] = 0.8 * x[t - 1] + scale * rng.normal(size=N_INPUT)
        return x
    if family == "SPARSE_SIGN":
        keep = rng.random((n, N_INPUT)) < 0.2
        sign = rng.choice(np.asarray([-1.0, 1.0]), size=(n, N_INPUT))
        return keep * sign / np.sqrt(0.2)
    raise ValueError(family)


def make_task(family: str, seed: int):
    family_idx = GENERATORS.index(family)
    rng = np.random.default_rng(np.random.SeedSequence([MASTER, family_idx, seed, 610]))
    projection = rng.normal(size=(N_INPUT, N_FEATURES)) / np.sqrt(N_INPUT)
    teacher = rng.normal(size=(N_FEATURES, N_CLASSES)) / np.sqrt(N_FEATURES)
    raw_train = make_stream(rng, family, N_TRAIN)
    raw_test = make_stream(rng, family, N_TEST)
    # BLAS may report harmless intermediate underflow on some builds; reject
    # non-finite projections explicitly after suppressing those intermediates.
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        phi_train = np.tanh(raw_train @ projection)
        phi_test = np.tanh(raw_test @ projection)
    phi_train /= np.maximum(np.linalg.norm(phi_train, axis=1, keepdims=True), 1e-12)
    phi_test /= np.maximum(np.linalg.norm(phi_test, axis=1, keepdims=True), 1e-12)
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        train_logits = phi_train @ teacher
        test_logits = phi_test @ teacher
    if not (np.isfinite(phi_train).all() and np.isfinite(phi_test).all()
            and np.isfinite(train_logits).all() and np.isfinite(test_logits).all()):
        raise FloatingPointError("non-finite task feature or teacher projection")
    labels_train = np.argmax(train_logits, axis=1)
    labels_test = np.argmax(test_logits, axis=1)
    return phi_train, labels_train, phi_test, labels_test


def softmax(vec: np.ndarray) -> np.ndarray:
    z = vec - np.max(vec)
    ex = np.exp(z)
    return ex / ex.sum()


def evaluate(w: np.ndarray, x: np.ndarray, y: np.ndarray):
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        logits = x @ w
    if not np.isfinite(logits).all():
        raise FloatingPointError("non-finite evaluation logits")
    logits -= logits.max(axis=1, keepdims=True)
    ex = np.exp(logits)
    p = ex / ex.sum(axis=1, keepdims=True)
    return float(np.mean(np.argmax(p, axis=1) == y)), float(-np.mean(np.log(np.maximum(p[np.arange(len(y)), y], 1e-12))))


def train_task(phi, labels, test_x, test_y, delay: int):
    weights = {arm: np.zeros((N_FEATURES, N_CLASSES), dtype=np.float64) for arm in ARMS}
    probs_pending: dict[str, dict[int, np.ndarray]] = {arm: {} for arm in ARMS}
    feature_pending: dict[str, dict[int, np.ndarray]] = {arm: {} for arm in CAPACITY}
    trace = np.zeros(N_FEATURES, dtype=np.float64)
    fifo_order = {arm: [] for arm in CAPACITY}
    fifo_updates = {arm: 0 for arm in CAPACITY}
    step_updates = {arm: 0 for arm in ARMS if arm != "CURRENT_FEATURE_64"}
    feature_memory_peak = {arm: 0 for arm in ARMS}
    start = time.perf_counter()

    def store_current(index: int, value: np.ndarray):
        for fifo_arm in CAPACITY:
            q = feature_pending[fifo_arm]
            q[index] = value
            fifo_order[fifo_arm].append(index)
            while len(fifo_order[fifo_arm]) > CAPACITY[fifo_arm]:
                old = fifo_order[fifo_arm].pop(0)
                q.pop(old, None)
            feature_memory_peak[fifo_arm] = max(feature_memory_peak[fifo_arm], len(q) * N_FEATURES)

    for t in range(N_TRAIN + delay):
        has_input = t < N_TRAIN
        feature = phi[t] if has_input else np.zeros(N_FEATURES, dtype=np.float64)
        trace = GAMMA * trace + feature
        if has_input:
            for arm in ARMS:
                p = softmax(feature @ weights[arm])
                probs_pending[arm][t] = p
            feature_memory_peak["ELIGIBILITY_TRACE_64"] = N_FEATURES
            feature_memory_peak["CURRENT_FEATURE_64"] = N_FEATURES if has_input else 0

        target = t - delay
        if not (0 <= target < N_TRAIN):
            if has_input:
                store_current(t, feature)
            continue
        one_hot = np.zeros(N_CLASSES, dtype=np.float64)
        one_hot[int(labels[target])] = 1.0
        for arm in ARMS:
            error = one_hot - probs_pending[arm].pop(target)
            if arm == "ELIGIBILITY_TRACE_64":
                update_feature = trace / max(float(np.linalg.norm(trace)), 1e-12)
            elif arm == "CURRENT_FEATURE_64":
                update_feature = feature
            elif arm in CAPACITY:
                update_feature = feature_pending[arm].pop(target, None)
                if update_feature is None:
                    continue
                fifo_updates[arm] += 1
                if target in fifo_order[arm]:
                    fifo_order[arm].remove(target)
            else:
                update_feature = phi[target]
            weights[arm] += LR * np.outer(update_feature, error)
            if arm in step_updates:
                step_updates[arm] += 1

        # Process a delayed label before storing the current cue so a D-vector
        # FIFO can retain the cue at age D.
        if has_input:
            store_current(t, feature)

    rows, audit = [], []
    for arm in ARMS:
        accuracy, loss = evaluate(weights[arm], test_x, test_y)
        rows.append({"arm": arm, "delay": delay, "test_accuracy": accuracy,
                     "test_cross_entropy": loss, "n_train": N_TRAIN, "n_test": N_TEST,
                     "active_feature_state_values": 64 if arm in {"ELIGIBILITY_TRACE_64", "CURRENT_FEATURE_64"}
                     else (min(CAPACITY[arm], delay) * 64 if arm in CAPACITY
                           else delay * 64 if arm == "EXACT_REPLAY_UNBOUNDED" else 0)})
        if arm in CAPACITY:
            audit.append({"arm": arm, "delay": delay, "capacity_vectors": CAPACITY[arm],
                          "label_updates_applied": fifo_updates[arm],
                          "label_updates_possible": N_TRAIN,
                          "update_coverage": fifo_updates[arm] / N_TRAIN,
                          "peak_active_feature_values": feature_memory_peak[arm]})
        elif arm == "EXACT_REPLAY_UNBOUNDED":
            audit.append({"arm": arm, "delay": delay, "capacity_vectors": delay,
                          "label_updates_applied": step_updates[arm], "label_updates_possible": N_TRAIN,
                          "update_coverage": step_updates[arm] / N_TRAIN,
                          "peak_active_feature_values": delay * N_FEATURES})
        else:
            audit.append({"arm": arm, "delay": delay, "capacity_vectors": 1,
                          "label_updates_applied": N_TRAIN, "label_updates_possible": N_TRAIN,
                          "update_coverage": 1.0, "peak_active_feature_values": N_FEATURES})
    return rows, audit, time.perf_counter() - start


def crossed_bootstrap(values: np.ndarray, seed: int = MASTER + 400):
    # values: fixed generator × task seed, already averaged over paired delays.
    rng = np.random.default_rng(seed)
    out = np.empty(BOOTSTRAPS, dtype=np.float64)
    for start in range(0, BOOTSTRAPS, 200):
        count = min(200, BOOTSTRAPS - start)
        sample = np.empty((count, values.shape[0]), dtype=np.float64)
        for gi in range(values.shape[0]):
            idx = rng.integers(0, values.shape[1], size=(count, values.shape[1]))
            sample[:, gi] = values[gi, idx].mean(axis=1)
        out[start:start + count] = sample.mean(axis=1)
    return [float(x) for x in np.quantile(out, [0.025, 0.975])]


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    metric_rows, coverage_rows, runtime_rows = [], [], []
    for family in GENERATORS:
        for seed in SEEDS:
            phi, labels, test_x, test_y = make_task(family, seed)
            for delay in DELAYS:
                rows, audits, seconds = train_task(phi, labels, test_x, test_y, delay)
                for row in rows:
                    row.update(generator=family, seed=seed)
                    metric_rows.append(row)
                for audit in audits:
                    audit.update(generator=family, seed=seed)
                    coverage_rows.append(audit)
                runtime_rows.append({"generator": family, "seed": seed, "delay": delay, "training_seconds": seconds})
        print(f"completed memory-frontier generator {family}", flush=True)

    write_csv(OUT / "task_metrics.csv", metric_rows)
    write_csv(OUT / "update_coverage.csv", coverage_rows)
    write_csv(OUT / "runtime_metrics.csv", runtime_rows)
    indexed = {(r["generator"], int(r["seed"]), int(r["delay"]), r["arm"]): r for r in metric_rows}
    # The primary contrast is trace minus an exact FIFO with the same 64-value active feature budget.
    effects = np.empty((len(GENERATORS), len(SEEDS)), dtype=np.float64)
    per_cell = []
    for gi, family in enumerate(GENERATORS):
        for si, seed in enumerate(SEEDS):
            ds = []
            for delay in DELAYS:
                trace = float(indexed[(family, seed, delay, "ELIGIBILITY_TRACE_64")]["test_accuracy"])
                fifo = float(indexed[(family, seed, delay, "EXACT_FIFO_64")]["test_accuracy"])
                ds.append(trace - fifo)
                per_cell.append({"generator": family, "seed": seed, "delay": delay,
                                 "trace_minus_fifo64": trace - fifo})
            effects[gi, si] = np.mean(ds)
    primary = float(effects.mean())
    ci = crossed_bootstrap(effects)

    frontier = []
    paired_rows = []
    for family in GENERATORS:
        for delay in DELAYS:
            for arm in ARMS:
                vals = [float(indexed[(family, seed, delay, arm)]["test_accuracy"]) for seed in SEEDS]
                covs = [float(r["update_coverage"]) for r in coverage_rows
                        if r["generator"] == family and int(r["seed"]) in SEEDS and int(r["delay"]) == delay and r["arm"] == arm]
                frontier.append({"generator": family, "delay": delay, "arm": arm,
                                 "active_feature_state_values": indexed[(family, SEEDS[0], delay, arm)]["active_feature_state_values"],
                                 "mean_test_accuracy": float(np.mean(vals)),
                                 "mean_update_coverage": float(np.mean(covs)) if covs else 1.0,
                                 "task_seeds": len(vals)})
                if arm != "ELIGIBILITY_TRACE_64":
                    diffs = np.asarray([
                        float(indexed[(family, seed, delay, "ELIGIBILITY_TRACE_64")]["test_accuracy"]) -
                        float(indexed[(family, seed, delay, arm)]["test_accuracy"])
                        for seed in SEEDS
                    ])
                    rng = np.random.default_rng(MASTER + 5000 + GENERATORS.index(family) * 100 + delay * 10 + ARMS.index(arm))
                    boot = rng.choice(diffs, size=(BOOTSTRAPS, len(SEEDS)), replace=True).mean(axis=1)
                    lo, hi = np.quantile(boot, [0.025, 0.975])
                    paired_rows.append({"generator": family, "delay": delay, "contrast": "ELIGIBILITY_TRACE_64_MINUS_REFERENCE",
                                        "reference_arm": arm, "mean_paired_difference": float(diffs.mean()),
                                        "task_seed_bootstrap_95ci_low": float(lo), "task_seed_bootstrap_95ci_high": float(hi),
                                        "positive_seed_count": int(np.sum(diffs > 0)), "n_task_seeds": len(SEEDS)})

    summary = {
        "experiment_id": EXP, "classification": "post-result exploratory bounded-memory comparison",
        "primary_estimand": "equal-generator mean of task-seed four-delay mean accuracy difference: eligibility trace (64 feature values) minus exact FIFO replay (64 feature values)",
        "primary_mean_difference": primary, "primary_hierarchical_seed_bootstrap_95ci": ci,
        "positive_generator_seed_blocks": int(np.sum(effects > 0)), "generator_seed_blocks": int(effects.size),
        "generator_means": {family: float(effects[i].mean()) for i, family in enumerate(GENERATORS)},
        "per_generator_delay_means": [
            {"generator": g, "delay": d,
             "trace_minus_fifo64": float(np.mean([float(indexed[(g, s, d, "ELIGIBILITY_TRACE_64")]["test_accuracy"]) -
                                                 float(indexed[(g, s, d, "EXACT_FIFO_64")]["test_accuracy"])
                                                 for s in SEEDS]))}
            for g in GENERATORS for d in DELAYS],
        "frontier": frontier,
        "scope": "conditional on three fixed input generators and this synthetic classification task; no biological validation or arbitrary-task generalization",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_csv(OUT / "per_seed_primary_contrasts.csv", per_cell)
    write_csv(OUT / "paired_contrasts.csv", paired_rows)
    manifest = {
        "experiment_id": EXP, "master_seed": MASTER,
        "generators": list(GENERATORS), "task_seeds": [SEEDS[0], SEEDS[-1]], "n_task_seeds_per_generator": len(SEEDS),
        "delays": list(DELAYS), "arms": list(ARMS), "active_state_unit": "one stored 64-value feature vector",
        "readout_parameters_per_arm": N_FEATURES * N_CLASSES,
        "training_parameters": {"learning_rate": LR, "eligibility_decay": GAMMA, "n_train": N_TRAIN, "n_test": N_TEST},
        "row_counts": {"task_metrics": len(metric_rows), "coverage": len(coverage_rows), "runtime": len(runtime_rows)},
        "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
        "outputs_sha256": {p.name: digest(p) for p in OUT.iterdir() if p.is_file()},
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"primary_mean_difference": primary, "ci95": ci, "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
