#!/usr/bin/env python3
"""Test source-derived cerebellar temporal profiles on an independent interval task."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import h5py
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
EXP = "M5_CEREBELLAR_INTERVAL_TIMING_TRANSFER_V1"
RAW = ROOT / "data/raw/cerebellar_interval_timing_dryad_v4/learning_1s_to_2s_GrC_CF.mat"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
OUT = ROOT / "data/results" / EXP
GRID = np.linspace(0.0, 2.4, 81)
DT = float(GRID[1] - GRID[0])
N_CELL_PER_GROUP = 32
SEEDS = tuple(range(6100, 6112))
NTRAIN, NTEST, NEPOCH = 1800, 500, 8
TRACE_DECAY, LR, L2 = 0.90, 0.20, 1e-4
BOOTSTRAPS, BOOT_SEED = 20000, 20261014
torch.set_num_threads(1)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ref_object(h5: h5py.File, ref: h5py.Reference):
    if not ref:
        raise ValueError("unexpected null MATLAB object reference")
    return h5[ref]


def session_refs(h5: h5py.File, group_index: int):
    cell = ref_object(h5, h5["groups"][0, group_index])
    return [cell[0, j] for j in range(cell.shape[1])]


def read_vector(session: h5py.Group, name: str) -> np.ndarray:
    return np.asarray(session[name][()]).reshape(-1)


def extract_cell_profiles() -> tuple[np.ndarray, list[dict[str, object]]]:
    """Recompute per-cell, source-filtered temporal profiles from the pinned MAT."""
    profiles: list[np.ndarray] = []
    meta: list[dict[str, object]] = []
    with h5py.File(RAW, "r") as h5:
        for group_index, group_label, threshold in (
            (0, "1-s expert", 0.75),
            (2, "2-s expert", 1.75),
        ):
            for session_index, ref in enumerate(session_refs(h5, group_index), start=1):
                s = ref_object(h5, ref)
                t = read_vector(s, "tmpxCb")
                dtb = float(np.asarray(s["dtb"][()]).reshape(-1)[0])
                delay = (read_vector(s, "rewtimes") - read_vector(s, "midpt")) * dtb
                keep = read_vector(s, "rewarded").astype(bool) & read_vector(s, "goodmvdir").astype(bool) & (delay > threshold)
                trials = np.flatnonzero(keep)
                if not len(trials):
                    raise ValueError(f"no eligible trials: {group_label} session {session_index}")
                # The HDF5 view is time × cells × trials (MATLAB stores trials × cells × time).
                activity = np.asarray(s["midAlgn/sigFilt_GrC"][:, :, trials], dtype=np.float32)
                mean_activity = activity.mean(axis=2, dtype=np.float64).T
                baseline = (t >= -1.0) & (t <= 0.0)
                window = (t >= 0.0) & (t <= 2.0)
                rel = mean_activity[:, window] - mean_activity[:, baseline].mean(axis=1, keepdims=True)
                positive = np.maximum(rel, 0.0)
                peaks = positive.max(axis=1, keepdims=True)
                valid = peaks[:, 0] > 1e-12
                normalized = positive[valid] / peaks[valid]
                times = t[window]
                for cell_index, row in enumerate(normalized, start=1):
                    profiles.append(np.interp(GRID[GRID <= 2.0], times, row, left=0.0, right=0.0))
                    meta.append({
                        "source_group": group_index + 1,
                        "source_group_label": group_label,
                        "within_group_session_index": session_index,
                        "cell_index_within_session": cell_index,
                        "eligible_reward_trials": len(trials),
                    })
    return np.asarray(profiles, dtype=np.float32), meta


def selected_biological_basis() -> tuple[np.ndarray, list[dict[str, object]], np.ndarray]:
    all_profiles, meta = extract_cell_profiles()
    chosen: list[int] = []
    for group in (1, 3):
        ix = np.flatnonzero([int(m["source_group"]) == group for m in meta])
        chosen.extend(ix[np.linspace(0, len(ix) - 1, N_CELL_PER_GROUP).round().astype(int)].tolist())
    chosen_array = np.asarray(chosen, dtype=int)
    # Hold features at zero after the measured 0–2 s interval.
    basis = np.zeros((len(GRID), len(chosen)), dtype=np.float32)
    basis[GRID <= 2.0] = all_profiles[chosen_array].T
    chosen_meta = [meta[int(i)] for i in chosen_array]
    return basis, chosen_meta, all_profiles


def make_generic_basis() -> np.ndarray:
    centers = np.linspace(0.0, 2.0, 64)
    width = 0.11
    return np.exp(-0.5 * ((GRID[:, None] - centers[None, :]) / width) ** 2).astype(np.float32)


def episode(rng: np.random.Generator, cue: int, base_interval: float, basis: np.ndarray):
    target = float(base_interval + rng.uniform(-0.15, 0.15))
    target = float(np.clip(target, 0.3, 2.25))
    y = np.zeros(len(GRID), dtype=np.float32)
    y[int(np.argmin(np.abs(GRID - target)))] = 1.0
    # Small independent observation noise makes the task less like template lookup.
    x = np.concatenate([basis, np.full((len(GRID), 1), 1.0 if cue == 0 else -1.0, dtype=np.float32)], axis=1)
    x[:, :-1] += rng.normal(0.0, 0.025, x[:, :-1].shape).astype(np.float32)
    return x, y, target


def sigmoid(x):
    x = np.clip(x, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-x))


def local_fit(train, dim: int, trace: bool) -> np.ndarray:
    """Cue-conditioned minibatch reward-error learning with/without eligibility."""
    w = np.zeros((2, dim + 1), dtype=np.float64)
    prepared = {}
    for cue in (0, 1):
        chosen = [r for r in train if r[0] == cue]
        x = np.stack([np.concatenate([r[1][:, :dim], np.ones((len(GRID), 1), dtype=np.float32)], axis=1) for r in chosen]).astype(np.float64)
        y = np.stack([r[2] for r in chosen]).astype(np.float64)
        if trace:
            e = np.empty_like(x)
            state = np.zeros((len(chosen), dim + 1), dtype=np.float64)
            for t in range(len(GRID)):
                state = TRACE_DECAY * state + (1.0 - TRACE_DECAY) * x[:, t, :]
                e[:, t, :] = state
        else:
            e = x
        prepared[cue] = (x, y, e)
    weights = np.where(prepared[0][1] > 0.5, 24.0, 1.0)
    normalizer = float(weights.sum(axis=1).mean())
    for epoch in range(NEPOCH):
        rate = LR / math.sqrt(1.0 + epoch * 0.15)
        for cue in (0, 1):
            x, y, e = prepared[cue]
            p = sigmoid(np.einsum("ntd,d->nt", x, w[cue]))
            err = (y - p) * np.where(y > 0.5, 24.0, 1.0)
            grad = np.einsum("nt,ntd->d", err, e) / (len(y) * normalizer) - L2 * w[cue]
            norm = float(np.linalg.norm(grad))
            if norm > 1.0: grad /= norm
            w[cue] += rate * grad
            if not np.isfinite(w[cue]).all(): raise FloatingPointError("nonfinite local-readout weights")
    return w


class HazardGRU(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.gru = nn.GRU(input_dim, 16, batch_first=True)
        self.head = nn.Linear(16, 1)

    def forward(self, x):
        h, _ = self.gru(x)
        return self.head(h).squeeze(-1)


def fit_gru(train, seed: int, input_dim: int):
    torch.manual_seed(seed)
    model = HazardGRU(input_dim)
    opt = torch.optim.Adam(model.parameters(), lr=0.004)
    xs = torch.tensor(np.stack([a[1] for a in train]), dtype=torch.float32)
    ys = torch.tensor(np.stack([a[2] for a in train]), dtype=torch.float32)
    # Positive-event weighting balances the one positive bin in each episode.
    weights = torch.ones_like(ys)
    weights[ys > 0.5] = 24.0
    ds = torch.utils.data.TensorDataset(xs, ys, weights)
    loader = torch.utils.data.DataLoader(ds, batch_size=128, shuffle=True, generator=torch.Generator().manual_seed(seed))
    for _ in range(18):
        model.train()
        for bx, by, bw in loader:
            opt.zero_grad(set_to_none=True)
            logits = model(bx)
            loss = (nn.functional.binary_cross_entropy_with_logits(logits, by, reduction="none") * bw).mean()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
    return model


def predict_local(w: np.ndarray, cue: int, x: np.ndarray, dim: int) -> np.ndarray:
    z = np.concatenate([x[:, :dim], np.ones((len(GRID), 1))], axis=1)
    if not np.isfinite(z).all() or not np.isfinite(w[cue]).all():
        raise FloatingPointError("nonfinite local model input or weights")
    logits = np.einsum("td,d->t", z, w[cue], optimize=False)
    if not np.isfinite(logits).all(): raise FloatingPointError("nonfinite local model logits")
    return sigmoid(logits)


def predict_gru(model, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(model(torch.tensor(x[None], dtype=torch.float32))[0]).cpu().numpy()


def write_csv(path: Path, rows: list[dict[str, object]]):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def bootstrap_ci(values: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOT_SEED)
    samples = rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))
    return [float(v) for v in np.quantile(values[samples].mean(axis=1), [0.025, 0.975])]


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    runner_hash_at_start = sha(Path(__file__))
    contract_hash_at_start = sha(CONTRACT)
    input_hash_at_start = sha(RAW)
    biological, chosen_meta, all_profiles = selected_biological_basis()
    rbf = make_generic_basis()
    # A marginal-preserving temporal-order destruction control.
    shuffle_rng = np.random.default_rng(909)
    shuffled = biological.copy()
    for j in range(shuffled.shape[1]):
        shuffled[:, j] = shuffled[shuffle_rng.permutation(len(GRID)), j]

    basis_rows = []
    for t, time_s in enumerate(GRID):
        row = {"time_seconds": float(time_s)}
        for j in range(biological.shape[1]): row[f"bio_{j:02d}"] = float(biological[t, j])
        for j in range(rbf.shape[1]): row[f"rbf_{j:02d}"] = float(rbf[t, j])
        basis_rows.append(row)
    write_csv(OUT / "temporal_basis.csv", basis_rows)
    write_csv(OUT / "selected_cell_provenance.csv", chosen_meta)

    conditions = {
        "ALIGNED": (0.9, 1.8),
        "REVERSED": (1.8, 0.9),
    }
    rows: list[dict[str, object]] = []
    start = time.perf_counter()
    for seed in SEEDS:
        for condition, cue_intervals in conditions.items():
            rng = np.random.default_rng(seed * 1009 + (0 if condition == "ALIGNED" else 1))
            tr = []
            for _ in range(NTRAIN):
                cue = int(rng.integers(0, 2))
                x, y, target = episode(rng, cue, cue_intervals[cue], biological)
                tr.append((cue, x, y, target))
            te_rng = np.random.default_rng(seed * 1009 + 555)
            te = []
            for _ in range(NTEST):
                cue = int(te_rng.integers(0, 2))
                x, y, target = episode(te_rng, cue, cue_intervals[cue], biological)
                te.append((cue, x, y, target))

            # Evaluate the exact same episodes with alternative fixed bases.
            for basis_name, basis, arm_name, has_trace in (
                ("BIO_PROFILE", biological, "ELIGIBILITY", True),
                ("BIO_PROFILE", biological, "NO_TRACE", False),
                ("GENERIC_RBF", rbf, "ELIGIBILITY", True),
                ("SHUFFLED_PROFILE", shuffled, "ELIGIBILITY", True),
            ):
                dim = basis.shape[1]
                train_variant = []
                for cue, source_x, y, target in tr:
                    # Reuse the episode's identical observation-noise realization across bases.
                    noise = source_x[:, :-1] - biological
                    x = np.concatenate([basis + noise, np.full((len(GRID), 1), 1.0 if cue == 0 else -1.0, dtype=np.float32)], axis=1)
                    train_variant.append((cue, x, y, target))
                w = local_fit(train_variant, dim, has_trace)
                for cue, source_x, y, target in te:
                    noise = source_x[:, :-1] - biological
                    x = np.concatenate([basis + noise, np.full((len(GRID), 1), 1.0 if cue == 0 else -1.0, dtype=np.float32)], axis=1)
                    pred = predict_local(w, cue, x, dim)
                    estimate = float(GRID[int(np.argmax(pred))])
                    rows.append({"task_seed": seed, "mapping": condition, "arm": f"{basis_name}_{arm_name}",
                                 "cue": cue, "true_time_seconds": target, "estimated_time_seconds": estimate,
                                 "absolute_error_seconds": abs(estimate - target), "peak_score": float(pred.max()),
                                 "parameters": int(2 * (dim + 1))})

            profile_train = [(cue, np.column_stack([x[:, :-1], np.full(len(GRID), cue, dtype=np.float32)]), y, target)
                             for cue, x, y, target in tr]
            profile_test = [(cue, np.column_stack([x[:, :-1], np.full(len(GRID), cue, dtype=np.float32)]), target)
                            for cue, x, _, target in te]
            clock_train = [(cue, np.column_stack([np.ones(len(GRID), dtype=np.float32), np.full(len(GRID), cue, dtype=np.float32)]), y, target)
                           for cue, _, y, target in tr]
            clock_test = [(cue, np.column_stack([np.ones(len(GRID), dtype=np.float32), np.full(len(GRID), cue, dtype=np.float32)]), target)
                          for cue, _, _, target in te]
            for arm, gru_train, gru_test, input_dim, model_seed in (
                ("GRU_PROFILE_BPTT", profile_train, profile_test, biological.shape[1] + 1, 0),
                ("GRU_CLOCK_BPTT", clock_train, clock_test, 2, 60000),
            ):
                model = fit_gru(gru_train, seed + (0 if condition == "ALIGNED" else 30000) + model_seed, input_dim)
                for cue, x, target in gru_test:
                    pred = predict_gru(model, x)
                    estimate = float(GRID[int(np.argmax(pred))])
                    rows.append({"task_seed": seed, "mapping": condition, "arm": arm, "cue": cue,
                                 "true_time_seconds": target, "estimated_time_seconds": estimate,
                                 "absolute_error_seconds": abs(estimate - target), "peak_score": float(pred.max()),
                                 "parameters": int(sum(p.numel() for p in model.parameters()))})

            # Strong explicit timer estimated from training labels only.
            for cue in (0, 1):
                mean_time = float(np.mean([z[3] for z in tr if z[0] == cue]))
                for cue_test, _, _, target in te:
                    if cue_test == cue:
                        rows.append({"task_seed": seed, "mapping": condition, "arm": "EMPIRICAL_TIMER", "cue": cue,
                                     "true_time_seconds": target, "estimated_time_seconds": mean_time,
                                     "absolute_error_seconds": abs(mean_time - target), "peak_score": float("nan"),
                                     "parameters": 2})
        print(f"finished seed {seed} ({seed - SEEDS[0] + 1}/{len(SEEDS)})", flush=True)

    write_csv(OUT / "episode_results.csv", rows)
    summaries = []
    # First reduce episodes to task-seed means; seeds are the paired units.
    keys = sorted({(r["mapping"], r["arm"]) for r in rows})
    seed_means: dict[tuple[str, str, int], float] = {}
    for mapping, arm in keys:
        for seed in SEEDS:
            vals = [float(r["absolute_error_seconds"]) for r in rows
                    if r["mapping"] == mapping and r["arm"] == arm and int(r["task_seed"]) == seed]
            seed_means[(mapping, arm, seed)] = float(np.mean(vals))
        v = np.array([seed_means[(mapping, arm, s)] for s in SEEDS])
        summaries.append({"mapping": mapping, "arm": arm, "mean_absolute_error_seconds": float(v.mean()),
                          "seed_bootstrap_95ci": bootstrap_ci(v), "seeds": len(v),
                          "episode_count_per_seed": NTEST})
    paired_contrasts = []
    for mapping in ("ALIGNED", "REVERSED"):
        ref = "BIO_PROFILE_ELIGIBILITY"
        for comparator in ("BIO_PROFILE_NO_TRACE", "GENERIC_RBF_ELIGIBILITY", "SHUFFLED_PROFILE_ELIGIBILITY",
                           "GRU_PROFILE_BPTT", "GRU_CLOCK_BPTT", "EMPIRICAL_TIMER"):
            diffs = np.array([seed_means[(mapping, ref, s)] - seed_means[(mapping, comparator, s)] for s in SEEDS])
            paired_contrasts.append({"mapping": mapping, "contrast": f"{ref}_MINUS_{comparator}",
                                     "mean_error_difference_seconds": float(diffs.mean()),
                                     "seed_bootstrap_95ci": bootstrap_ci(diffs),
                                     "positive_seeds": int((diffs > 0).sum()), "seeds": len(SEEDS)})
    summary = {"experiment_id": EXP, "classification": "POST_RESULT_EXPLORATORY_ARTIFICIAL_EXPERIMENT",
               "primary_outcome": "per-episode absolute reward-time error, summarized by task seed",
               "summaries": summaries, "paired_contrasts": paired_contrasts, "seed_range": [SEEDS[0], SEEDS[-1]],
               "train_episodes_per_seed_mapping": NTRAIN, "test_episodes_per_seed_mapping": NTEST,
               "selected_biological_cells": len(chosen_meta), "extracted_source_cells": int(len(all_profiles)),
               "elapsed_seconds": time.perf_counter() - start,
               "bootstrap": {"resamples": BOOTSTRAPS, "seed": BOOT_SEED, "unit": "task seed"},
               "interpretation": "Synthetic transfer only; source-derived traces are condition-averaged signals, not synaptic weights or independent animal replicates."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    output_files = ["temporal_basis.csv", "selected_cell_provenance.csv", "episode_results.csv", "summary.json"]
    manifest = {"experiment_id": EXP, "contract_sha256": contract_hash_at_start, "runner_sha256": runner_hash_at_start,
                "input_mat_sha256": input_hash_at_start, "python": platform.python_version(), "numpy": np.__version__,
                "h5py": h5py.__version__, "torch": torch.__version__, "seeds": list(SEEDS),
                "grid_seconds": GRID.tolist(), "mapping_intervals_seconds": conditions, "selected_cell_count": len(chosen_meta),
                "output_sha256": {name: sha(OUT / name) for name in output_files}}
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"summaries": summaries, "elapsed_seconds": summary["elapsed_seconds"]}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        OUT.mkdir(parents=True, exist_ok=True)
        profiles, meta, _ = selected_biological_basis()
        if profiles.shape != (len(GRID), 64) or len(meta) != 64: raise AssertionError("unexpected biological basis shape")
        if not np.isfinite(profiles).all() or profiles.min() < 0 or profiles.max() > 1.001: raise AssertionError("invalid normalized profile")
        # Synthetic target generation must be independent of biological inputs.
        x, y, target = episode(np.random.default_rng(7), 0, 0.9, profiles)
        if x.shape != (len(GRID), 65) or y.sum() != 1 or abs(GRID[np.argmax(y)] - target) > DT: raise AssertionError("synthetic task preflight failed")
        pre = {"experiment_id": EXP, "classification": "POST_RESULT_EXPLORATORY", "outcomes_computed": False,
               "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
               "input_mat_sha256": sha(RAW), "profile_shape": list(profiles.shape), "selected_cells": len(meta),
               "finite_profiles": True, "independent_synthetic_label_check": "PASS", "arms": ["BIO_PROFILE_ELIGIBILITY", "BIO_PROFILE_NO_TRACE", "GENERIC_RBF_ELIGIBILITY", "SHUFFLED_PROFILE_ELIGIBILITY", "GRU_PROFILE_BPTT", "GRU_CLOCK_BPTT", "EMPIRICAL_TIMER"]}
        (OUT / "PREFLIGHT.json").write_text(json.dumps(pre, indent=2) + "\n")
        print(json.dumps(pre, indent=2)); return
    prefile = OUT / "PREFLIGHT.json"
    if not prefile.exists(): raise FileNotFoundError("run --preflight before experiment")
    pre = json.loads(prefile.read_text())
    if pre["contract_sha256"] != sha(CONTRACT) or pre["runner_sha256"] != sha(Path(__file__)): raise RuntimeError("contract or runner changed since preflight")
    if (OUT / "episode_results.csv").exists(): raise FileExistsError("refusing to overwrite existing results")
    run()


if __name__ == "__main__": main()
