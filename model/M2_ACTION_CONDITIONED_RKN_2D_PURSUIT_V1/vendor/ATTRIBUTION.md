# Action-Conditional Recurrent Kalman Network cell attribution

`acrkn_cell.py` is adapted from the official implementation at [ALRhub/action-conditional-rkn](https://github.com/ALRhub/action-conditional-rkn), commit `7a8ae18c17ff3f324f58a6d2ef8ee93265a6fa07`, for Shaj et al., “Action-Conditional Recurrent Kalman Networks For Forward and Inverse Dynamics Learning,” CoRL 2020 / PMLR 155 (2021), <https://proceedings.mlr.press/v155/shaj21a.html>.

The upstream MIT license is included as `LICENSE-MIT.txt`. Local compatibility changes: the unused `tsensor` import is removed because the only uses in the source file are commented out, and a minimal `ConfigDict` fallback is provided when the optional upstream `util` package is absent. The Kalman update, action-conditioned prediction, covariance propagation, and control network are retained. The experiment-specific encoder, posterior readout, config, and loop are implemented in the sibling runner; this wrapper is therefore an adapted AcRKN cell baseline, not a byte-for-byte reproduction of the complete CoRL model.

Upstream source SHA-256 before the compatibility edit: `2d22aaeb6299d13b4b8a65beecedee8125dfa4765136c6de5f6827ca116a2123`.
