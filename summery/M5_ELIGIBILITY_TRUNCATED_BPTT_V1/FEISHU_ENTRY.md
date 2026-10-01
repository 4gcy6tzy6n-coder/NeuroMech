## M5_ELIGIBILITY_TRUNCATED_BPTT_V1 — eligibility versus truncated BPTT

**实验结果：** 32 个 task-seed block，五种更新规则，均使用同一 24-unit、746 参数 RNN。Eligibility trace held-out XOR accuracy 为 0.6974；no-trace 和 TBPTT-1 均为 0.5562；TBPTT-4 为 0.9633；full BPTT 为 0.9996。主比较 eligibility−TBPTT-4 为 −0.26588，95% paired task-seed bootstrap CI [−0.32950, −0.20031]，只有 1/32 个 seed 有利于 eligibility。Eligibility 相比 no-trace 提升 +0.14125，但明显落后于 recurrent-gradient controls。

**分析与边界：** Full BPTT 明确通过 task-viability check，所以这是可解释的负面对照结果，不是任务不可学。该结果表明：eligibility 在这个任务中优于仅用当前步局部更新，但不能替代短截断 BPTT，更不能据此声称优于通用 RNN 学习。实验是 post-result exploratory synthetic test，不是生物验证或独立确认。

**经验：** eligibility 必须和 TBPTT/完整 BPTT 比较，不能只对比弱的 no-trace 更新；运行时优势需要和精度损失同时报告。预检发现并修复了 no-trace 输入梯度形状错误，修复后有限差分误差最大为 1.31e−10，才启动完整运行。
