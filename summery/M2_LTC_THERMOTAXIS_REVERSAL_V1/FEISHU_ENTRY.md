## M2_LTC_THERMOTAXIS_REVERSAL_V1 — LTC thermotaxis-like reversal test

**结果：未达到预注册的机制判据。** 在 32 个训练 seed block、7 个训练模型臂和 3 种梯度反转 hazard 下完成了 98,304 条测试 episode。主条件 hazard `1/20` 中，sensory-site LTC 与 output-site、no-feedback、dense-feedback 及 yoked 对照的配对差异都没有明确分离；sensory-site 对 GRU-4/GRU-8 的 MSE 较低，但所有学习模型的跟踪都很弱：sensory-site MSE 为 132.32，而获得特权梯度符号的 oracle 为 28.82。因此 GRU 对照不能被解释成机制优势。

**分析：** 这是由早期 M2 结果启发的探索性人工实验，不是独立确认，也不是生物验证。主要失败是学习到的控制器没有形成有效 setpoint tracking。下一版若要继续，须先冻结非特权任务可行性标准、记录 no-action baseline 与学习曲线；不得在本轮结果上调参后冒充确认性复现。

**经验：** 先证明普通学习控制器能完成任务，再解释机制对照；休眠参数要在有效参数量说明中披露。机制迁移假设中的 gradient-sign inference 尚非蠕虫实验证据。
