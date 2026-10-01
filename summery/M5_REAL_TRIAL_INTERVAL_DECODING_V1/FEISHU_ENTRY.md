# M5_REAL_TRIAL_INTERVAL_DECODING_V1 — real-trial CF-LTD interval decoder

**数据来源。** Garcia-Garcia et al. 2024 的小脑 GrC/CF 长时间间隔学习数据（[Neuron](https://doi.org/10.1016/j.neuron.2024.05.019)；[Dryad v4](https://doi.org/10.5061/dryad.bk3j9kdm6)）。**结果。** 在 16 个 session、1,004 个 QC trial 上完成五折 session 内预测，共产生 7,028 条 held-out trial×模型记录。CF-LTD 投影相对训练集均值预测的 session 等权 MAE 差为 +0.00970 s（越大越差），只在 1/16 个 session 改善；三个来源组的均值差均为正。原始 GrC PCA16/ridge 平均改善 0.00265 s，在 11/16 个 session 改善，但过渡组基本持平（Δ=+0.00003 s），且其各组 MAE 均优于 CF-LTD 投影。

**分析。** 本结果不支持当前 source-defined CF-LTD 投影在固定 0–0.80 s 预奖励窗口内提供超出 session timer 的 held-out interval 解码优势。它是对该投影/readout 实现的探索性负结果，不能推断生物体内因果、突触权重测量、跨动物泛化或 AI 迁移。动物 ID 缺失，因此 session 只作描述单位。一个 session 的四折没有训练折 CF candidate，按零投影保留；协议在部分运行后调整，未查看部分运行预测值，故不是确认性预注册。

**复现与经验。** 完整性 verifier 通过（7,028 行、1,004 trial、480 个拟合记录、6 个输出文件哈希）；独立完整重跑逐字复现 trial predictions 和 fold manifest。故障记录包括未初始化 shuffle RNG、空 CF candidate fold，以及异构拟合 manifest 写入问题。修复、哈希和协议更新均在有效完整运行前提交；部分运行事件留档。

**仓库：** https://github.com/4gcy6tzy6n-coder/NeuroMech/tree/experiment-publication

飞书实验记录：主线实验文档 revision 87，独立章节已回读核实。
