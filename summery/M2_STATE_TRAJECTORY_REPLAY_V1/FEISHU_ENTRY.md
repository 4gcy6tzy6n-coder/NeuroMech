## M2_STATE_TRAJECTORY_REPLAY_V1 — 完整 motor-state trajectory replay

**实验代号：** `M2_STATE_TRAJECTORY_REPLAY_V1`

**实验问题：** 将校正后感觉反馈模型开发集中的完整 200 秒 forward/reverse mode 序列独立重放到 held-out heading stream，保留 bout 次序、序列相关和边界删失，检验这样的 motor-state replay 是否足以复现趋暖行为。

**实验结果：** 三种噪声尺度等权的感觉位点模型减完整 trajectory replay warm-direction index 差为 `+0.44742`，95% seed-block bootstrap 区间 `[+0.43988, +0.45497]`，200/200 个 block 为正。replay arm 的 warm-direction index 接近 0；相较之下，感觉位点模型均值约为 `0.59 / 0.43 / 0.33`。标量 motor-only control 的差为 `+0.13781`（95% 区间 `[+0.13454, +0.14112]`）。

**持续性核验：** held-out forward duration summaries 在三个噪声尺度均接近；reverse summaries 在 `1.00` 和 `1.25` 接近，但 noise `0.75` 仍有 reverse mean 差 `+0.784 s`、P90 差 `+3.513 s`。实验没有冻结等价界限，不能宣称 matched-control 通过。

**分析与边界：** 在这个校正后的 Python source model 中，只重放完整 motor-state 时序而切断它与 held-out sensory/environmental context 的关系，不能重现趋暖方向行为。这支持有限的模型层结论：边际或独立重放的 motor-state timing 本身不足，state timing 与感觉/环境上下文的关系会影响该模拟任务。它不能证明唯一机制是 sensory-site feedback，也不是新动物证据、AI 迁移或 NMI-ready 结论。此前 M2/V1/V5 结果均已知，研究属于探索性；MATLAB/Octave 数值复现尚未完成。

**材料：** [实验结果](RESULTS.md)；[限制记录](FAILURE_LOG.md)；[契约](CONTRACT.md)。
