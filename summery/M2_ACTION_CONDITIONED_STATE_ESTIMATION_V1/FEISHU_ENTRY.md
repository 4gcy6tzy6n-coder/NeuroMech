## M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1 — action-conditioned signed-state estimation

**结果：sensory-site LTC 未通过冻结判据。** 32 个训练 seed block、7 个训练模型臂、3 种 held-out action-to-state coupling，共 196,608 条测试 episode。对齐条件 `c=+1` 下，sensory-site LTC 的 signed displacement MSE 为 1.9748；output-site LTC 为 1.8196，GRU-2 为 1.5657，GRU-4 为 0.6354，特权 oracle 为 0.0292。Sensory-site 相比 no-feedback 和 yoked 控制仅有很小的 MSE 改善（分别 +0.00249 和 +0.00229 的 comparator-minus-sensory 差值），但显著输给 output-site，未满足预注册的主判据。

**分析与边界：** 这是受先前 M2 结果启发的 post-result exploratory artificial computation test，不是独立确认或生物验证。GRU-4 的结果说明该对齐任务可学习；因此本轮主要是具体 sensory-site LTC 实现的负面结果，而不是“任务不可学”。生物文献支持 RIM 相关 motor-state 对 AIY 表征与行为持续性的影响，但不支持本试验的确切位移估计目标或 LTC 方程。

**经验：** 统计上可分辨的 ablation 差异仍可能小到没有实际价值；未来确认性实验应在运行前定义 SESOI。下一步不对本轮调参挽救；项目应回到源模型操作和表征的证据，或转向 cerebellar eligibility 主线。
