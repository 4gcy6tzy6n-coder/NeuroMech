---

## 实验代号：M2_AIY_STATE_CONDITIONAL_ENCODING_V1 — 恒温源数据中的 AIY 运动状态解码

**实验结果：** 对 Ji et al. Figure 2/5 的公开恒温源轨迹做逐动物、连续时间分块交叉验证。WT 与 RIM 消融各 5 只。AIY 单独解码前进/反转的平均 AUC 分别为 0.758 和 0.502；AVA 分别为 0.736 和 0.631。控制前一采样点运动状态后，AIY 增量 AUC 为 WT 0.01554、RIM 消融 0.000028，组间差 0.01551（动物级 bootstrap 95% 区间 0.01143–0.01913；精确组标签置换 p=0.00794，仅描述性）。AVA 也有同方向变化，增量组间差为 0.00943，因此不能据此认定效应特异于 AIY。独立复算通过，覆盖 10 只动物的全部输出和 252 种组标签分配。

**分析：** 轨迹与“RIM 完整时 AIY 含运动状态信息、RIM 消融后减弱”一致，但前一时刻行为状态本身几乎饱和地预测当前状态；神经活动在其上的增量很小。每组仅 5 只，结果是对已发表干预证据的公开源数据再分析，不是新动物实验或新因果验证。源表中 Figure 5 热刺激轨迹缺少运动状态列，故未用于状态×温度分析。组标签置换与动物级 bootstrap 只作描述，AVA 的相似变化也限制了 AIY 特异性结论。

**优点与失败经验：** 动物而非时间点作为分析单位；显式用上一时刻状态作为强基线，避免把行为持续性误写成神经信息增量。AVA 对照显示组间变化并非本分析所能定位到 AIY 独有，不能宣称 AIY 特异性。下一步 AI 实验必须比较 prior-state/action-only、神经样反馈、不同回路位置及强 action-conditioned recurrent baselines。

**仓库记录：** https://github.com/4gcy6tzy6n-coder/NeuroMech/tree/experiment-publication/summery/M2_AIY_STATE_CONDITIONAL_ENCODING_V1
