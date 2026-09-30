## M2_FEEDBACK_SITE_SPECIFICITY_V4 — 多统计量持久性校准压力测试

**性质：** 结果知情、回顾性源模型仿真；不是确认性实验、动物新证据或 AI 迁移结果。

**实验结果：** 沿用 Ji et al. Figure 7 Python 源模型与 V3 开发集，针对平均、median、90 分位前向运行时长和 ≥30 s 比例选择 motor-only 系数；在 200 个新 seed block 上，感觉反馈减 motor-only 的 warm-direction index 均值为 `+0.14128`，95% seed-block bootstrap 区间 `[+0.13798, +0.14460]`，200/200 个 block 为正。

**关键失败与分析：** 四统计量损失只选择了最接近的网格系数，没有实现持久性等价。噪声 0.75 下，感觉反馈减 motor-only 的平均运行时长差仍为 `+2.506 s`，90 分位差为 `+8.810 s`；其余噪声尺度也存在差异。因此正向行为差异不能归因于反馈位置，V4 不比 V3 提供更强的机制特异性证据。更大的效应值可能来自较差的对照拟合。

**结论：** `SOURCE_MODEL_DIFFERENCE_PERSISTS_BUT_PERSISTENCE_MATCH_FAILED`。保留结果与对照失败；不能推断生物因果或 AI 迁移。下一次若继续，应使用独立开发数据构造完整持久性 yoke，并预先冻结对照匹配充分性检查。

**复核：** 独立 verifier 对 1,800 行、开发集校准选择、输出哈希及主估计复算均为 `PASS`。GitHub 文件目录：`summery/M2_FEEDBACK_SITE_SPECIFICITY_V4/`（`experiment-publication` 分支）。
