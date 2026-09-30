---

## 实验代号：M2_FEEDBACK_SITE_SPECIFICITY_V3

**记录日期：**2026-10-01　**类型：**outcome-informed source-model simulation follow-up

**研究问题：**在 Ji et al. 2021 Figure 7 导航模型中，将反馈放在感觉处理变量上，是否比仅增强 motor persistence 更能支持趋暖方向？motor-only control 按开发集平均 forward-run duration 校准，并在三个感觉噪声尺度上测试。

### 实验结果

使用 40 个开发 seed block 选择 motor-only 系数，使用 200 个全新测试 seed block；每个 block 含 50 个模拟个体。三个噪声乘数分别为 0.75、1.00、1.25。主要对比为 sensory-site feedback 减去 motor-only matched 的 warm-direction index，在每个 block 内对三种噪声条件等权平均。

总体差值为 **+0.08057**，seed-block bootstrap 95% CI **[+0.07752, +0.08357]**；**200/200** 个 block 的平均差值为正。按噪声乘数分别为：0.75 时 +0.08030 [0.07410, 0.08654]，192/200 为正；1.00 时 +0.09056 [0.08585, 0.09544]，199/200 为正；1.25 时 +0.07084 [0.06714, 0.07456]，198/200 为正。

### 分析与解释

在该作者模型的 Python 实现中，按开发集校准平均持续时间后，感觉位点反馈在三个施加的噪声水平下仍具有更高的 warm-direction index。该结果加强了“反馈位置在此模型中有作用”的证据。

但对照只匹配了平均持续时间，未匹配持续时间分布、forward occupancy、切换延迟及内部状态。测试集的中位持续时间仍有差异；因此结果不能唯一归因于反馈位点。噪声乘数是模型操作，不是从动物数据估计的生物边界条件。

### 限制与结论边界

此项为已知 V1/V2 结果后的探索性仿真；不是新生物实验，不提供动物层级推断，也不证明普遍 AI 优势或唯一因果突触。作者 MATLAB/Octave 实现与 Python runner 的数值一致性尚未独立验证。完整失败与限制记录见 GitHub 项目中的 `summery/M2_FEEDBACK_SITE_SPECIFICITY_V3/FAILURE_LOG.md`。

### 复现与归档

合同、runner、原始模拟指标、校准数据、summary、manifest 和独立校验文件均单独归档于 NeuroMech 的 `experiment-publication` 分支。本实验独立形成一个提交；下方 GitHub 链接在推送完成后补入。

---
