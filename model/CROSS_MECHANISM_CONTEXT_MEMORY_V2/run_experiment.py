#!/usr/bin/env python3
"""Post-result exploratory benchmark: M2 recurrent baseline and M5 overlapping credit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from scipy.optimize import least_squares
from torch import nn

SEEDS = 32
BOOT = 10_000
BOOT_SEED = 20261002
M5_DIM = 16
M5_UPDATES = 3_000
M5_TEST = 1_024
DELAYS = (1, 4, 16, 64)
KAPPAS = (1.0, 0.0, -1.0)
LAMBDA = 0.95
ETA = 0.003


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def simulate_m2(rng: np.random.Generator, n_ep: int, length: int, kappa: float):
    n = n_ep * length
    state = np.empty(n, dtype=np.float32)
    obs = np.empty(n, dtype=np.float32)
    ctx = rng.choice((-1.0, 1.0), size=n)
    same = rng.random(n) < ((1.0 + kappa) / 2.0)
    low_noise_ctx = np.where(same, ctx, -ctx)
    s = float(rng.choice((-1.0, 1.0)))
    for i in range(n):
        if rng.random() < 0.04:
            s = -s
        state[i] = s
        obs[i] = s + rng.normal(0.0, 0.35 if low_noise_ctx[i] > 0 else 1.1)
    shape = (n_ep, length)
    return state.reshape(shape), obs.reshape(shape), ctx.astype(np.float32).reshape(shape)


def filt_gain(obs, ctx, p):
    g0, g1, bias = p
    out = np.zeros_like(obs, dtype=np.float64)
    for t in range(obs.shape[1]):
        prev = out[:, t - 1] if t else 0.0
        g = np.clip(g0 + g1 * ctx[:, t], 0.001, 0.999)
        out[:, t] = (1.0 - g) * prev + g * obs[:, t] + bias
    return out


def fit_gain(state, obs, ctx):
    target = state.ravel()
    fit = least_squares(lambda p: filt_gain(obs, ctx, p).ravel() - target,
                        np.array([0.4, 0.0, 0.0]),
                        bounds=([0.001, -0.49, -0.2], [0.999, 0.49, 0.2]), max_nfev=120)
    return fit.x


class TinyGRU(nn.Module):
    def __init__(self, inputs: int, hidden: int = 8):
        super().__init__()
        self.gru = nn.GRU(inputs, hidden, batch_first=True)
        self.readout = nn.Linear(hidden, 1)

    def forward(self, x):
        h, _ = self.gru(x)
        return self.readout(h).squeeze(-1)


def train_gru(obs, ctx, state, include_context: bool, seed: int):
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    inputs = np.stack((obs, ctx), axis=-1) if include_context else obs[..., None]
    x = torch.tensor(inputs, dtype=torch.float32)
    y = torch.tensor(state, dtype=torch.float32)
    model = TinyGRU(inputs.shape[-1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()
    for _ in range(50):
        optimizer.zero_grad(set_to_none=True)
        loss = loss_fn(model(x), y)
        loss.backward()
        optimizer.step()
    return model, int(sum(p.numel() for p in model.parameters())), float(loss.detach())


def run_m2(seed: int):
    rng = np.random.default_rng(1_810_000 + seed)
    train_s, train_y, train_c = simulate_m2(rng, 24, 300, 1.0)
    gain_p = fit_gain(train_s, train_y, train_c)
    gru_ctx, n_ctx, loss_ctx = train_gru(train_y, train_c, train_s, True, 31_000 + seed)
    gru_noctx, n_noctx, loss_noctx = train_gru(train_y, train_c, train_s, False, 41_000 + seed)
    rows = []
    for kappa in KAPPAS:
        state, obs, ctx = simulate_m2(rng, 64, 300, kappa)
        gain_mse = float(np.mean((filt_gain(obs, ctx, gain_p) - state) ** 2))
        with torch.no_grad():
            x_ctx = torch.tensor(np.stack((obs, ctx), axis=-1), dtype=torch.float32)
            x_noctx = torch.tensor(obs[..., None], dtype=torch.float32)
            pred_ctx = gru_ctx(x_ctx).cpu().numpy()
            pred_noctx = gru_noctx(x_noctx).cpu().numpy()
        ctx_mse = float(np.mean((pred_ctx - state) ** 2))
        noctx_mse = float(np.mean((pred_noctx - state) ** 2))
        rows.append({"seed": seed, "kappa": kappa, "context_gain_mse": gain_mse,
                     "gru_context_mse": ctx_mse, "gru_no_context_mse": noctx_mse,
                     "gru_context_minus_gain": ctx_mse - gain_mse,
                     "gru_no_context_minus_gain": noctx_mse - gain_mse,
                     "context_gain_parameters": 3, "gru_context_parameters": n_ctx,
                     "gru_no_context_parameters": n_noctx,
                     "gru_context_train_loss": loss_ctx, "gru_no_context_train_loss": loss_noctx,
                     "gain_parameters_json": json.dumps(gain_p.tolist())})
    return rows


def sign(x):
    return np.where(x >= 0.0, 1.0, -1.0)


def unit_rows(x):
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def run_m5(seed: int):
    rng = np.random.default_rng(2_920_000 + seed)
    teacher = rng.normal(size=M5_DIM)
    teacher /= np.linalg.norm(teacher)
    rows = []
    for delay in DELAYS:
        stream = unit_rows(rng.normal(size=(M5_UPDATES + delay, M5_DIM)))
        scores = np.sum(stream * teacher[None, :], axis=1)
        labels = sign(scores + rng.normal(0.0, 0.05, size=len(scores)))
        weights = {"eligibility": np.zeros(M5_DIM), "latest_input": np.zeros(M5_DIM), "exact_fifo": np.zeros(M5_DIM)}
        trace = np.zeros(M5_DIM)
        latest_state = np.zeros(M5_DIM)
        for t, x_t in enumerate(stream):
            trace = LAMBDA * trace + x_t
            latest_state[:] = x_t
            if t < delay:
                continue
            update_idx = t - delay
            y_delayed = labels[update_idx]
            updates = {"eligibility": trace, "latest_input": latest_state, "exact_fifo": stream[update_idx]}
            for name, w in weights.items():
                w += ETA * y_delayed * updates[name]
                norm = np.linalg.norm(w)
                if norm > 2.0:
                    w *= 2.0 / norm
        test = unit_rows(rng.normal(size=(M5_TEST, M5_DIM)))
        y_test = sign(np.sum(test * teacher[None, :], axis=1))
        accuracy = {name: float(np.mean(sign(np.sum(test * w[None, :], axis=1)) == y_test))
                    for name, w in weights.items()}
        rows.append({"seed": seed, "delay": delay,
                     "eligibility_accuracy": accuracy["eligibility"],
                     "latest_input_accuracy": accuracy["latest_input"],
                     "exact_fifo_accuracy": accuracy["exact_fifo"],
                     "eligibility_minus_latest_input": accuracy["eligibility"] - accuracy["latest_input"],
                     "eligibility_minus_exact_fifo": accuracy["eligibility"] - accuracy["exact_fifo"],
                     "learned_parameters_each_arm": M5_DIM,
                     "eligibility_state_dimensions": M5_DIM,
                     "latest_input_state_dimensions": M5_DIM,
                     "fifo_state_dimensions": delay * M5_DIM})
    return rows


def write_csv(path: Path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def bootstrap(values, rng):
    draws = np.mean(values[rng.integers(0, len(values), (BOOT, len(values)))], axis=1)
    return {"mean": float(np.mean(values)),
            "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
            "positive_seed_blocks": int(np.sum(values > 0)), "n_seed_blocks": int(len(values))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="data/results/CROSS_MECHANISM_CONTEXT_MEMORY_V2/canonical_corrected")
    args = ap.parse_args()
    out = Path(args.output_dir)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    m2 = [r for seed in range(SEEDS) for r in run_m2(seed)]
    m5 = [r for seed in range(SEEDS) for r in run_m5(seed)]
    write_csv(out / "m2_seed_results.csv", m2)
    write_csv(out / "m5_seed_results.csv", m5)
    rng = np.random.default_rng(BOOT_SEED)
    m2_summary = {}
    for k in KAPPAS:
        rows = [r for r in m2 if r["kappa"] == k]
        m2_summary[str(k)] = {
            "gru_context_minus_gain": bootstrap(np.array([r["gru_context_minus_gain"] for r in rows]), rng),
            "gru_no_context_minus_gain": bootstrap(np.array([r["gru_no_context_minus_gain"] for r in rows]), rng)}
    m5_summary = {}
    for delay in DELAYS:
        rows = [r for r in m5 if r["delay"] == delay]
        m5_summary[str(delay)] = {
            "eligibility_minus_latest_input": bootstrap(np.array([r["eligibility_minus_latest_input"] for r in rows]), rng),
            "eligibility_minus_exact_fifo": bootstrap(np.array([r["eligibility_minus_exact_fifo"] for r in rows]), rng)}
    summary = {"experiment_id": "CROSS_MECHANISM_CONTEXT_MEMORY_V2", "classification": "POST_RESULT_EXPLORATORY",
               "seed_blocks": SEEDS, "bootstrap_resamples": BOOT, "bootstrap_seed": BOOT_SEED,
               "m2_primary": "context-aware GRU MSE minus context-gain MSE; positive means context-gain wins",
               "m2_by_mapping": m2_summary, "m5_primary": "eligibility accuracy minus latest-input accuracy",
               "m5_by_delay": m5_summary,
               "resource_accounting": {"m2_parameters": {"context_gain": 3, "gru_context": 297, "gru_no_context": 273},
                                       "m5_learned_weights_per_arm": M5_DIM,
                                       "m5_trace_state": M5_DIM, "m5_latest_input_state": M5_DIM,
                                       "m5_fifo_state_by_delay": {str(d): d * M5_DIM for d in DELAYS}},
               "claim_boundary": "Task-specific artificial results only; no biological validation and no pooled cross-mechanism effect."}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {"python": __import__("sys").version, "numpy": np.__version__, "scipy": __import__("scipy").__version__,
                "torch": torch.__version__, "seeds": SEEDS,
                "runner_sha256": sha256(Path(__file__).resolve()),
                "contract_sha256": sha256(Path("summery/CROSS_MECHANISM_CONTEXT_MEMORY_V2/CONTRACT.md")),
                "files": {p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file()}}
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
