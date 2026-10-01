#!/usr/bin/env python3
"""Compare the M2 update with an action-conditioned RKN cell in 2D pursuit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from vendor.acrkn_cell import AcRKNCell

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_ACTION_CONDITIONED_RKN_2D_PURSUIT_V1"
MODEL_DIR = ROOT / "model" / EXP
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
BASE_RUNNER = ROOT / "model" / "M2_2D_CLOSED_LOOP_PURSUIT_V1" / "run_experiment.py"
OUT_DEFAULT = ROOT / "data" / "results" / EXP / "canonical"
SEEDS = tuple(range(76100, 76124))
NTRAIN, NTEST, T = 512, 256, 32
UPDATES, BATCH, STEP, NOISE = 200, 16, 0.12, 0.25
DROP_RATE = 0.20
CONDITIONS = ("ALIGNED", "REVERSED")
LEARNED_ARMS = ("MODE_GAIN", "BILINEAR_RNN_8P", "ACRKN_L1")
ALL_ARMS = LEARNED_ARMS + ("MODE_GAIN_ACTION_YOKE", "KALMAN_ORACLE")
BOOTSTRAPS, BOOTSTRAP_SEED = 10_000, 20261031


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sensor_matrix(q: np.ndarray, condition: str) -> np.ndarray:
    aligned = condition == "ALIGNED"
    horizontal_high = (q > 0) if aligned else (q < 0)
    if np.ndim(horizontal_high):
        return np.where(np.asarray(horizontal_high)[:, None],
                        np.array([0.95, 0.10], np.float32),
                        np.array([0.10, 0.95], np.float32))
    return np.array([0.95, 0.10] if horizontal_high else [0.10, 0.95], np.float32)


def generate_training(seed: int):
    rng = np.random.default_rng(seed)
    target = rng.normal(0, 0.5, (NTRAIN, 2)).astype(np.float32)
    position = np.zeros_like(target)
    obs = np.empty((NTRAIN, T, 2), np.float32)
    qseq = np.empty((NTRAIN, T), np.float32)
    actions = np.zeros((NTRAIN, T, 3), np.float32)
    valid = rng.random((NTRAIN, T)) >= DROP_RATE
    labels = np.empty_like(obs)
    q = np.ones(NTRAIN, np.float32)
    for t in range(T):
        qseq[:, t] = q
        gain = np.where((q > 0)[:, None], [0.95, 0.10], [0.10, 0.95]).astype(np.float32)
        y = gain * (target - position) + rng.normal(0, NOISE, (NTRAIN, 2)).astype(np.float32)
        obs[:, t] = np.where(valid[:, t, None], y, 0.0)
        labels[:, t] = target - position
        axes = rng.integers(0, 2, NTRAIN)
        signs = rng.choice(np.array([-1.0, 1.0], np.float32), NTRAIN)
        move = np.zeros_like(position)
        move[np.arange(NTRAIN), axes] = STEP * signs
        actions[:, t, :2] = move
        q_next = np.where(axes == 0, 1.0, -1.0).astype(np.float32)
        actions[:, t, 2] = q_next
        position += move
        q = q_next
    incoming = np.zeros_like(actions[:, :, :2])
    incoming[:, 1:] = actions[:, :-1, :2]
    return obs, qseq, incoming, actions, valid.astype(np.float32), labels


class SmallEstimator:
    """Eight-parameter biological-shaped and bilinear state updates."""

    def __init__(self, name: str, seed: int):
        self.name = name
        torch.manual_seed(seed)
        init = ([5., 5., -0.174, -0.174, 1.56, -1.56, 0., 0.]
                if name == "MODE_GAIN" else
                [3., 3., 0.5, 0.5, 0., 0., 0., 0.])
        self.raw = nn.Parameter(torch.tensor(init, dtype=torch.float32))

    def parameters(self):
        return [self.raw]

    def step(self, h, y, q, incoming, valid):
        prior = h - incoming
        if self.name == "MODE_GAIN":
            rho = 0.999 * torch.sigmoid(self.raw[:2])
            gain = torch.sigmoid(self.raw[2:4] + self.raw[4:6] * q[:, None])
            updated = rho * prior + gain * (y - prior) + self.raw[6:8]
        else:
            rho = 0.999 * torch.sigmoid(self.raw[:2])
            updated = rho * prior + self.raw[2:4] * y + self.raw[4:6] * (y * q[:, None]) + self.raw[6:8]
        return torch.where(valid[:, None] > 0.5, updated, prior)

    def rollout(self, y, q, incoming, valid):
        h = torch.zeros((y.shape[0], 2), dtype=y.dtype)
        outputs = []
        for t in range(y.shape[1]):
            h = self.step(h, y[:, t], q[:, t], incoming[:, t], valid[:, t])
            outputs.append(h)
        return torch.stack(outputs, dim=1)


class AcRKNEstimator(nn.Module):
    """Low-dimensional AcRKN cell with posterior-state readout for control."""

    def __init__(self, seed: int):
        super().__init__()
        torch.manual_seed(seed)
        config = type("AcConfig", (), {
            "num_basis": 1,
            "bandwidth": 1,
            "trans_net_hidden_units": [],
            "control_net_hidden_units": [],
            "trans_net_hidden_activation": "Tanh",
            "control_net_hidden_activation": "ReLU",
            "learn_trans_covar": True,
            "trans_covar": 0.1,
            "learn_initial_state_covar": True,
            "initial_state_covar": 1.0,
            "learning_rate": 0.003,
            "enc_out_norm": "none",
            "clip_gradients": True,
            "never_invalid": False,
        })()
        self.cell = AcRKNCell(latent_obs_dim=1, act_dim=3, config=config)
        self.encoder_mean = nn.Linear(2, 1)
        self.encoder_var = nn.Linear(2, 1)
        self.posterior_readout = nn.Linear(2, 2)
        self.initial_upper = nn.Parameter(torch.ones(1, 1))
        self.initial_lower = nn.Parameter(torch.ones(1, 1))
        self.initial_side = nn.Parameter(torch.zeros(1, 1))

    def parameters_count(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def initial(self, batch_size: int):
        prior = torch.zeros(batch_size, 2)
        cov = [p.expand(batch_size, -1) for p in (self.initial_upper, self.initial_lower, self.initial_side)]
        return prior, cov

    def encode(self, y):
        mean = self.encoder_mean(y)
        var_raw = self.encoder_var(y)
        var = torch.exp(var_raw).where(var_raw < 0, var_raw + 1.0) + 1e-5
        return mean, var

    def update(self, prior, cov, y, valid):
        enc_mean, enc_var = self.encode(y)
        return self.cell._masked_update(prior, cov, enc_mean, enc_var, valid[:, None] > 0.5)

    def rollout(self, obs, actions, valid, labels):
        batch = obs.shape[0]
        prior, cov = self.initial(batch)
        estimates = []
        for t in range(obs.shape[1]):
            posterior, post_cov = self.update(prior, cov, obs[:, t], valid[:, t])
            estimates.append(self.posterior_readout(posterior))
            prior, cov = self.cell._predict(posterior, post_cov, actions[:, t])
        return torch.stack(estimates, dim=1)

    def online_step(self, prior, cov, obs, valid):
        posterior, post_cov = self.update(prior, cov, obs, valid)
        estimate = self.posterior_readout(posterior)
        return estimate, posterior, post_cov

    def advance(self, posterior, post_cov, action):
        return self.cell._predict(posterior, post_cov, action)


def torchify(*arrays):
    return tuple(torch.from_numpy(np.ascontiguousarray(a, dtype=np.float32)) for a in arrays)


def train_small(name, seed, obs, q, incoming, actions, valid, labels):
    model = SmallEstimator(name, seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.02)
    rng = np.random.default_rng(12000000 + seed * 31)
    ty, tq, ti, tv, tl = torchify(obs, q, incoming, valid, labels)
    losses = []
    start = time.perf_counter()
    for _ in range(UPDATES):
        idx = torch.from_numpy(rng.integers(0, NTRAIN, BATCH))
        pred = model.rollout(ty[idx], tq[idx], ti[idx], tv[idx])
        loss = ((pred - tl[idx]) ** 2).mean()
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach()))
    fit = {"training_seed": seed, "arm": name, "parameter_count": int(model.raw.numel()),
           "updates": UPDATES, "batch_size": BATCH, "sequence_tokens_per_fit": UPDATES * BATCH * T,
           "learning_rate": 0.02, "training_seconds": time.perf_counter() - start,
           "initial_loss": float(np.mean(losses[:10])), "final_loss": float(np.mean(losses[-10:])),
           "parameters_json": json.dumps(model.raw.detach().numpy().tolist())}
    return model, fit


def train_acrkn(seed, obs, q, actions, valid, labels):
    model = AcRKNEstimator(seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
    rng = np.random.default_rng(13000000 + seed * 31)
    ty, tq, ta, tv, tl = torchify(obs, q, actions, valid, labels)
    losses = []
    start = time.perf_counter()
    for _ in range(UPDATES):
        idx = torch.from_numpy(rng.integers(0, NTRAIN, BATCH))
        model.train()
        pred = model.rollout(ty[idx], ta[idx], tv[idx], tl[idx])
        loss = ((pred - tl[idx]) ** 2).mean()
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach()))
    fit = {"training_seed": seed, "arm": "ACRKN_L1", "parameter_count": model.parameters_count(),
           "updates": UPDATES, "batch_size": BATCH, "sequence_tokens_per_fit": UPDATES * BATCH * T,
           "learning_rate": 0.003, "training_seconds": time.perf_counter() - start,
           "initial_loss": float(np.mean(losses[:10])), "final_loss": float(np.mean(losses[-10:])),
           "parameters_json": json.dumps([p.detach().cpu().numpy().tolist() for p in model.parameters()])}
    return model, fit


def oracle_update(mean, var, y, pos, q, condition, valid):
    h = sensor_matrix(q, condition)
    den = h * h * var + NOISE ** 2
    k = var * h / den
    z = y + h * pos
    updated_mean = mean + k * (z - h * mean)
    updated_var = (1 - k * h) * var
    return np.where(valid[:, None], updated_mean, mean), np.where(valid[:, None], updated_var, var)


def random_derangement(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed + 1_310_000_000)
    while True:
        donor = rng.permutation(NTEST)
        if np.all(donor != np.arange(NTEST)):
            return donor


def run_policy(model, target, noise, dropout, condition, donor_moves=None, record_moves=False):
    n = len(target)
    position = np.zeros_like(target)
    q = np.ones(n, np.float32)
    incoming = np.zeros_like(position)
    active = np.ones(n, bool)
    distances = np.zeros((n, T), np.float32)
    steps = np.full(n, T, np.int16)
    moves = np.zeros((n, T, 2), np.float32)
    hstate = np.zeros_like(position)
    if isinstance(model, AcRKNEstimator):
        model.eval()
        prior, cov = model.initial(n)
    if model == "KALMAN_ORACLE":
        belief = np.zeros_like(target)
        variance = np.full_like(target, 0.25)
    for t in range(T):
        valid = ~dropout[:, t]
        gain = sensor_matrix(q, condition)
        y = gain * (target - position) + noise[:, t]
        y = np.where(valid[:, None], y, 0.0).astype(np.float32)
        if model == "KALMAN_ORACLE":
            belief, variance = oracle_update(belief, variance, y, position, q, condition, valid)
            estimate = belief - position
        elif isinstance(model, AcRKNEstimator):
            with torch.no_grad():
                estimate_t, posterior, post_cov = model.online_step(
                    prior, cov, torch.from_numpy(y), torch.from_numpy(valid.astype(np.float32)))
            estimate = estimate_t.numpy()
        else:
            with torch.no_grad():
                estimate = model.step(torch.from_numpy(hstate), torch.from_numpy(y), torch.from_numpy(q),
                                      torch.from_numpy(incoming), torch.from_numpy(valid.astype(np.float32))).numpy()
            hstate = estimate
        distance = np.linalg.norm(target - position, axis=1)
        distances[:, t] = distance
        reached = active & (distance <= 0.12)
        steps[reached] = t + 1
        active[reached] = False
        if t == T - 1:
            break
        axis = np.argmax(np.abs(estimate), axis=1)
        idx = np.where(active)[0]
        move = np.zeros_like(position)
        signs = np.sign(estimate[idx, axis[idx]])
        signs[signs == 0] = 1
        move[idx, axis[idx]] = STEP * signs
        position += move
        actual_move = move.copy()
        if donor_moves is not None and t > 0:
            incoming = donor_moves[:, t - 1]
        else:
            incoming = actual_move
        q_next = np.where(axis == 0, 1.0, -1.0).astype(np.float32)
        q[active | reached] = q_next[active | reached]
        moves[:, t] = actual_move
        if isinstance(model, AcRKNEstimator):
            action_t = np.column_stack([actual_move, q_next]).astype(np.float32)
            with torch.no_grad():
                prior, cov = model.advance(posterior, post_cov, torch.from_numpy(action_t))
    final = np.linalg.norm(target - position, axis=1)
    return {"final_distance": final, "success": (final <= 0.12).astype(np.int8),
            "mean_distance": distances.mean(axis=1), "steps_to_success": steps,
            "moves": moves if record_moves else None}


def crossed_ci(seed_episode: np.ndarray, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    boot = np.empty(BOOTSTRAPS, np.float64)
    for start in range(0, BOOTSTRAPS, 100):
        count = min(100, BOOTSTRAPS - start)
        si = rng.integers(0, seed_episode.shape[0], (count, seed_episode.shape[0]))
        ei = rng.integers(0, seed_episode.shape[1], (count, seed_episode.shape[1]))
        boot[start:start + count] = seed_episode[si[:, :, None], ei[:, None, :]].mean((1, 2))
    return [float(v) for v in np.quantile(boot, [0.025, 0.975])]


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--seeds", type=int, default=len(SEEDS), help="use fewer seeds only for a documented pilot")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output directory: {out}")
    if not 1 <= args.seeds <= len(SEEDS):
        raise ValueError("--seeds must be between 1 and the frozen seed count")
    torch.set_num_threads(1)
    out.mkdir(parents=True, exist_ok=True)
    seeds = SEEDS[:args.seeds]
    episode_rows, fit_rows, audit_rows = [], [], []
    for si, seed in enumerate(seeds, 1):
        train = generate_training(700000 + seed)
        obs, q, incoming, actions, valid, labels = train
        models = {}
        for i, arm in enumerate(("MODE_GAIN", "BILINEAR_RNN_8P")):
            model, fit = train_small(arm, seed + 1009 * (i + 1), obs, q, incoming, actions, valid, labels)
            models[arm] = model
            fit_rows.append(fit)
        acrkn, fit = train_acrkn(seed + 3011, obs, q, actions, valid, labels)
        models["ACRKN_L1"] = acrkn
        fit_rows.append(fit)
        test_rng = np.random.default_rng(900000 + seed)
        target = test_rng.normal(0, 0.5, (NTEST, 2)).astype(np.float32)
        noise = test_rng.normal(0, NOISE, (NTEST, T, 2)).astype(np.float32)
        dropout = test_rng.random((NTEST, T)) < DROP_RATE
        for condition in CONDITIONS:
            self_run = run_policy(models["MODE_GAIN"], target, noise, dropout, condition, record_moves=True)
            donor = random_derangement(seed + (0 if condition == "ALIGNED" else 90000))
            donor_moves = self_run["moves"][donor]
            audit_rows.append({"training_seed": seed, "condition": condition,
                               "donor_is_derangement": bool(np.all(donor != np.arange(NTEST))),
                               "donated_move_marginal_exact": bool(np.array_equal(
                                   np.sort(self_run["moves"], axis=0), np.sort(donor_moves, axis=0))),
                               "n_episodes": NTEST})
            results = {"MODE_GAIN": self_run,
                       "MODE_GAIN_ACTION_YOKE": run_policy(models["MODE_GAIN"], target, noise, dropout,
                                                            condition, donor_moves=donor_moves),
                       "BILINEAR_RNN_8P": run_policy(models["BILINEAR_RNN_8P"], target, noise, dropout, condition),
                       "ACRKN_L1": run_policy(acrkn, target, noise, dropout, condition),
                       "KALMAN_ORACLE": run_policy("KALMAN_ORACLE", target, noise, dropout, condition)}
            for arm, metrics in results.items():
                for episode in range(NTEST):
                    episode_rows.append({"training_seed": seed, "condition": condition,
                                         "episode_id": episode, "arm": arm,
                                         **{k: float(v[episode]) for k, v in metrics.items()
                                            if k != "moves"}})
        print(f"completed action-conditioned pursuit seed {seed} ({si}/{len(seeds)})", flush=True)
    write_csv(out / "episode_metrics.csv", episode_rows)
    write_csv(out / "training_metrics.csv", fit_rows)
    write_csv(out / "yoke_audit.csv", audit_rows)
    manifest = {
        "experiment_id": EXP,
        "classification": "post-result exploratory action-conditioned state-space comparison",
        "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
        "seed_range_used": [seeds[0], seeds[-1]], "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "pilot_or_canonical": "canonical" if len(seeds) == len(SEEDS) else "pilot",
        "n_train": NTRAIN, "n_test": NTEST, "steps": T, "drop_rate": DROP_RATE,
        "updates": UPDATES, "batch_size": BATCH, "sequence_tokens_per_fit": UPDATES * BATCH * T,
        "arms": list(ALL_ARMS), "conditions": list(CONDITIONS), "episode_rows": len(episode_rows),
        "input_sha256": {
            "contract": sha256(CONTRACT), "runner": sha256(Path(__file__)),
            "base_runner": sha256(BASE_RUNNER),
            "upstream_acrkn_cell": "2d22aaeb6299d13b4b8a65beecedee8125dfa4765136c6de5f6827ca116a2123",
            "vendored_acrkn_cell": sha256(MODEL_DIR / "vendor/acrkn_cell.py"),
        },
        "output_sha256": {name: sha256(out / name) for name in
                          ("episode_metrics.csv", "training_metrics.csv", "yoke_audit.csv")},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    # Summary retains task-native outcomes and separate contrasts for each condition.
    lookup = {(int(r["training_seed"]), r["condition"], int(r["episode_id"]), r["arm"]): r
              for r in episode_rows}
    summary = {"experiment_id": EXP, "rows": len(episode_rows), "arms": list(ALL_ARMS),
               "primary": {}, "contrasts": {}}
    for ci, condition in enumerate(CONDITIONS):
        contrast_specs = (("acrkn_minus_mode", "ACRKN_L1", "MODE_GAIN"),
                          ("bilinear_minus_mode", "BILINEAR_RNN_8P", "MODE_GAIN"),
                          ("yoke_minus_mode", "MODE_GAIN_ACTION_YOKE", "MODE_GAIN"),
                          ("oracle_minus_mode", "KALMAN_ORACLE", "MODE_GAIN"))
        summary["contrasts"][condition] = {}
        for pi, (name, left, right) in enumerate(contrast_specs):
            summary["contrasts"][condition][name] = {}
            for mi, metric in enumerate(("final_distance", "success", "mean_distance", "steps_to_success")):
                matrix = np.empty((len(seeds), NTEST), np.float64)
                for si, seed in enumerate(seeds):
                    for ep in range(NTEST):
                        matrix[si, ep] = float(lookup[(seed, condition, ep, left)][metric]) - float(
                            lookup[(seed, condition, ep, right)][metric])
                seed_boot = 20261031 + ci * 100 + pi * 10 + mi
                summary["contrasts"][condition][name][metric] = {
                    "left": left, "right": right, "mean_left_minus_right": float(matrix.mean()),
                    "crossed_95ci": crossed_ci(matrix, seed_boot),
                    "positive_seed_blocks": int(np.sum(matrix.mean(axis=1) > 0)),
                    "n_seed_blocks": len(seeds), "bootstrap_seed": seed_boot,
                }
                if condition == "ALIGNED" and name == "acrkn_minus_mode" and metric == "final_distance":
                    summary["primary"] = summary["contrasts"][condition][name][metric]
    for condition in CONDITIONS:
        summary.setdefault("arm_means", {})[condition] = {}
        for arm in ALL_ARMS:
            for metric in ("final_distance", "success", "mean_distance", "steps_to_success"):
                vals = [float(r[metric]) for r in episode_rows if r["condition"] == condition and r["arm"] == arm]
                summary["arm_means"][condition].setdefault(arm, {})[metric] = float(np.mean(vals))
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest["output_sha256"]["summary.json"] = sha256(out / "summary.json")
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": manifest, "primary": summary["primary"]}, indent=2))


if __name__ == "__main__":
    main()
