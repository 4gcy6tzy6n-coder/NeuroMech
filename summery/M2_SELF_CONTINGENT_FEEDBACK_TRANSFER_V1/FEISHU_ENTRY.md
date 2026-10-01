# 2026-10-01 M2 self-contingent feedback versus distribution-matched yoke V1

**实验代号：** `M2_SELF_CONTINGENT_FEEDBACK_TRANSFER_V1`

**问题与设计：** 在合成目标跟踪任务中，比较受体自身运动反馈进入感觉状态更新，与瞬时总体反馈分布完全匹配但来自其他个体轨迹的 yoke。主要条件为 `SLOW_TRANSIENT`；主要统计量为 `YOKED − SELF_SENSORY` movement MSE，正值表示自体反馈有利。

**实验结果：** 32 个配对训练 seed block 的主要差值为 `+0.009431`，95% seed-block bootstrap 区间 `[+0.007434, +0.011676]`。128 项反馈分布检查均通过。该差异只出现在 `SLOW_TRANSIENT`；快速瞬态和两个 clean 条件没有同方向优势。主要条件下 `SELF_SENSORY` MSE 为 `0.37930`，`SELF_OUTPUT` 为 `0.36819`，`GENERIC_RNN_1D` 为 `0.35484`，`GRU_8` 为 `0.30434`，`NO_FEEDBACK` 为 `0.38934`。

**分析与边界：** 结果支持一个很窄的解释：在该慢速瞬态合成环境中，保留“反馈属于当前受体”的对应关系，相较于总体分布完全匹配的跨个体 yoke，可降低误差。但效果没有跨条件复现，且输出端反馈、通用循环控制和 GRU-8 在主要指标上均优于目标机制模型。因此不能声称该机制改善整体 AI 性能或验证了生物因果机制。这是部分知情的探索性人工迁移。

**执行与复现：** 首次调用因 yoke 控制器误路由到通用 RNN 分支而在首个 seed block 训练阶段停止，未产生或查看 outcome。修复仅更正模型分支路由。修正后的 verifier 通过；独立完整复跑中，4 个科学结果文件逐字节一致，训练清单除 `training_seconds` 外一致。

**结论：** 保留为单一模拟条件下的受体特异反馈效应；不支持项目级 AI 优势或生物到 AI 的验证主张。
