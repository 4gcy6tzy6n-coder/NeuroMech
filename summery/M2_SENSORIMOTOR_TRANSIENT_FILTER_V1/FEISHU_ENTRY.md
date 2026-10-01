# M2_SENSORIMOTOR_TRANSIENT_FILTER_V1 — 感觉状态端与输出端运动反馈比较

日期：2026-10-01

## 实验结果

这是一个受 Ji et al.（eLife 2021）生物学结果启发的合成控制任务，不是生物验证。20 个配对 seed block、7 个模型/参照、5 种测试条件、每格 64 集，共 44,800 条 episode-arm 记录。冻结前提交：`9f70f60`。

主要终点为 `TRANSIENT_PULSE` 中 pulse 窗口及其后两个时间步的 movement MAE。主要差值定义为 `OUTPUT_SITE_1D − SENSORY_SITE_1D`，正值才支持感觉状态端反馈。

结果方向相反：差值均值 **−0.0921**，95% seed-block bootstrap CI **[−0.1081, −0.0766]**（20 个 seed block）。感觉状态端 MAE 为 0.6458，输出端为 0.5537。输出端在该合成任务的主要指标上更好，因此预注册方向未获支持。

## 分析与边界

no-feedback 模型的 pulse-window MAE 为 0.7228，高于两种反馈模型；这只与“此模拟器中加入运动状态反馈可能有用”相容，不证明生物机制。感觉状态端的 command energy 较低（0.460 vs 输出端 0.576），但这伴随更高主要误差。GRU、直接传感器和可读取隐藏目标的 oracle 均已报告；oracle 是特权上界，不能作为公平学习对照。两种 4 参数模型参数量相同，但计算结构和优化性质并不相同。

结论仅针对这一个人工任务和实现，不能否定 Ji et al. 报告的 RIM 依赖运动状态反馈，也没有证明一般 AI 收益。全量复跑中 episode metrics、seed summary 与 summary JSON 字节级一致；独立 verifier 通过完整性和聚合核验。训练耗时字段因运行负载变化，不要求字节级一致。

## 优点与失败经验

本轮在运行前统一了合同和代码的 MAE 定义，固定了重叠 pulse 窗口采用时间点并集而不重复计数，避免 endpoint 实现漂移。失败经验是：即使参数数量匹配，感觉状态更新端并不因此优于输出反馈；任务、控制结构与优化几何都会影响结果。保留这次反向结果，不据此事后改 primary 指标或任务统计。

复现文件：NeuroMech GitHub `experiment-publication` 分支，实验合同、runner、verifier、canonical outputs 与结果/失败分析均按 `M2_SENSORIMOTOR_TRANSIENT_FILTER_V1` 独立归档。
