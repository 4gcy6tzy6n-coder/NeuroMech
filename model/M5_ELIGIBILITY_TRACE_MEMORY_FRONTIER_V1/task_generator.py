#!/usr/bin/env python3
"""M8-family synthetic AR(1) random-feature classification task generator."""
import numpy as np

MASTER_SEED = 20260930
N_INPUT, N_FEATURES, N_OUTPUT = 32, 64, 4
N_TRAIN, N_TEST = 3000, 1000


def stream(rng, rho, n):
    x = np.empty((n, N_INPUT), dtype=np.float64)
    x[0] = rng.normal(size=N_INPUT)
    scale = np.sqrt(1.0 - rho * rho)
    for t in range(1, n):
        x[t] = rho * x[t - 1] + scale * rng.normal(size=N_INPUT)
    return x


def make_task(rho, seed):
    base = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, seed, 101]))
    projection = base.normal(size=(N_INPUT, N_FEATURES)) / np.sqrt(N_INPUT)
    teacher = base.normal(size=(N_FEATURES, N_OUTPUT)) / np.sqrt(N_FEATURES)
    rng = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, int(rho * 10), seed, 707]))
    x_train = stream(rng, rho, N_TRAIN)
    x_test = stream(rng, rho, N_TEST)
    phi_train = np.tanh(x_train @ projection)
    phi_test = np.tanh(x_test @ projection)
    phi_train /= np.maximum(np.linalg.norm(phi_train, axis=1, keepdims=True), 1e-12)
    phi_test /= np.maximum(np.linalg.norm(phi_test, axis=1, keepdims=True), 1e-12)
    if not all(np.isfinite(array).all() for array in (phi_train, phi_test)):
        raise FloatingPointError("task generator produced non-finite features")
    return (
        phi_train,
        np.argmax(phi_train @ teacher, axis=1),
        phi_test,
        np.argmax(phi_test @ teacher, axis=1),
    )
