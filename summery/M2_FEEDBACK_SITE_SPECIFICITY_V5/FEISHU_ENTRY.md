## M2_FEEDBACK_SITE_SPECIFICITY_V5 — 修正感觉延迟索引后的源模型对照

**实验代号：** `M2_FEEDBACK_SITE_SPECIFICITY_V5`

**实验问题：** 修正 Ji et al. Figure 7 MATLAB 源码到 Python 移植中的感觉延迟索引后，感觉处理位点反馈相对 motor-only feedback 的趋暖方向差异是否仍存在？

**实验结果：** 在三个模拟噪声尺度上，感觉位点减 motor-only 的 warm-direction index 等权差为 `+0.13936`，95% seed-block bootstrap 区间 `[+0.13572, +0.14295]`，200/200 个测试 seed block 为正。四项前向运行持续性统计的 motor-only 对照仍未匹配：其平均和 P90 时长更短、中位时长更长、≥30 秒运行比例更低。

**实现纠正：** 源 MATLAB 的 `lagi=max(1,ti-delti)` 对应 Python 的 `max(0,t-delti)`；V3/V4 用了 `max(0,t-1-delti)`，额外滞后一个采样点（约 `0.1333 s`）。V5 在新版本中修正该索引，没有改写旧脚本或历史结果。该结论来自源码索引推导；由于没有 MATLAB/Octave 执行，完整数值移植一致性尚未验证。

**分析与边界：** 修正索引后正向差异仍存在，说明该差异不太可能仅由这一处索引偏移造成；但 persistence 对照继续失配，因此不能把差异归因为 feedback-site specificity。该实验是看过先前 M2/V3/V4 结果后的探索性源模型分析，不是新的生物实验、动物层推断或 AI 迁移结果。

**失败经验：** 多指标校准规则只能返回网格中最接近的标量系数，不能保证运行持续性分布等价。下一次若继续，应先使用独立开发数据建立更灵活的 persistence yoke/control，并在分析方向性 outcome 之前报告匹配充分性；不再重复标量系数拟合。

**材料：** [实验结果与限制](RESULTS.md)；[索引审计](SOURCE_INDEX_AUDIT.md)；[实验契约](CONTRACT.md)。
