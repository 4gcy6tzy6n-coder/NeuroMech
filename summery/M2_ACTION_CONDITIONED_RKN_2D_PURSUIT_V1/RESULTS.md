# M2 action-conditioned state-space comparison on 2D pursuit — V1 results

**Status:** completed and independently checked. **Classification:** post-result exploratory artificial comparison; not biological validation, independent task-family generalization, or a general AI result.

## Frozen primary result

The primary endpoint was final target distance in the aligned condition; lower is better. The frozen contrast was `ACRKN_L1 − MODE_GAIN`, so a positive value favors the M2-inspired mode-gain estimator. Across 24 training-seed blocks and 256 paired held-out episodes per seed, the contrast was **+0.88785** (crossed 95% bootstrap interval **[+0.59512, +1.23230]**; 24/24 seed-block means positive). Mean final distance was 1.02141 for the adapted one-dimensional-latent ac-RKN cell and 0.13356 for mode-gain.

This primary comparison does not establish a distinctive M2 computation. The 8-parameter bilinear recurrent control achieved lower aligned final distance than mode-gain: `BILINEAR_RNN_8P − MODE_GAIN = −0.03035` (95% interval **[−0.04391, −0.01786]**; bilinear had lower seed-block mean in 20/24 blocks). Its aligned success fraction was 0.84245 versus 0.76042 for mode-gain. The task-aware Kalman reference also had lower final distance (0.09223) and higher success (0.88477), but it uses known task parameters and is not a matched learned baseline.

Under the reversed sensor mapping, bilinear RNN again outperformed mode-gain by 0.26186 final-distance units (95% interval **[−0.27890, −0.24519]** for `bilinear − mode`; 0/24 positive seed blocks), while the oracle achieved 0.08722 mean final distance. Mode-gain's mean final distance increased from 0.13356 aligned to 0.41029 reversed. This is evidence of a strong mapping-specific weakness in this artificial task.

The recipient-specific action yoke was worse than mode-gain in aligned final distance (`yoke − mode = +0.02376`, interval **[+0.01515, +0.03209]**) and reversed final distance (`+0.11381`, interval **[+0.09441, +0.13364]**). The donor action marginal audit passed for every seed and condition. This supports recipient-contingent action feedback within this simulator, but it does not isolate biological feedback-site specificity: recipient trajectories and observation histories differ after yoking, and the bilinear control performs better.

## Scope and interpretation

The artificial task uses a two-dimensional fixed target, movement-dependent sensor gain, noisy observations, and 20% whole-vector observation dropout. The experiment adapted the AcRKN cell from ALRhub's official implementation; it is not a complete reproduction of the published robotics model. Its learned baseline has 32 trainable parameters and only one latent observation dimension. It receives actions and context as encoded inputs; the M2 and bilinear arms each have eight parameters. All fits used the same episode count and update count, but wall-clock costs differ, and parameter counts are not matched for AcRKN or the Kalman oracle.

The strongest defensible conclusion is mixed and narrow: **mode-gain beats this small adapted AcRKN baseline in the frozen aligned primary contrast, and self-contingent feedback beats the yoke, but a parameter-matched generic bilinear estimator beats mode-gain in both tested mappings.** Therefore this round does not support unique M2 algorithmic value over a generic matched recurrent update. The result is a task-specific boundary and should not be used as evidence of biological causality or general AI benefit.

## Reproduction and verification

From the repository root:

```bash
python3 model/M2_ACTION_CONDITIONED_RKN_2D_PURSUIT_V1/run_experiment.py
python3 model/M2_ACTION_CONDITIONED_RKN_2D_PURSUIT_V1/verify_results.py
```

The canonical output contains 61,440 episode rows, 72 training fits, per-seed yoke checks, a summary, and a SHA-256 manifest. The independent verifier passed on the canonical output and recomputed the primary mean from episode-level rows. A separate one-seed pilot was used only for implementation debugging and is not part of the archived canonical output.
