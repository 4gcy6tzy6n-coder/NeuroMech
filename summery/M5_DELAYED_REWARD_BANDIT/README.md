# M5 延迟奖励 contextual bandit：经验总结

## 优点

- 把同一 eligibility update 从 delayed supervised labels 搬到不同目标：contextual bandit 的延迟二元奖励。
- 三种 arm 的策略参数、每步 score norm、baseline、学习率一致；共享任务、上下文、动作采样和潜在奖励随机数。
- 以 30 个任务种子为独立单位，将四种延迟作为配对条件；held-out expected reward 消除了测试动作采样噪声。
- 每任务/延迟/arm 原始结果及训练奖励轨迹完整保存，主估计从原始记录独立复算。

## 失败经验与边界

- 效果不大：trace 相对 no-trace 的总体增益约 `0.00914`，且随延迟从 1 增至 64 而递减。
- Exact replay 的 held-out expected reward 为 `0.5525`，高于 trace 的 `0.5096`；迹线不是最优 credit assignment。
- 这是一个线性 softmax policy 的 synthetic bandit，不是 LNN/RNN，也没有测量真实小脑或 connectome。
- 本轮在已知 M5 分类结果后设计，属于事后探索性跨目标测试。

详见 [`RESULTS.md`](RESULTS.md) 与 [`M5_DELAYED_REWARD_BANDIT_CONTRACT.md`](M5_DELAYED_REWARD_BANDIT_CONTRACT.md)。代码位于 [`model/M5_DELAYED_REWARD_BANDIT/`](../../model/M5_DELAYED_REWARD_BANDIT/)，结果数据位于 [`data/results/M5_DELAYED_REWARD_BANDIT/`](../../data/results/M5_DELAYED_REWARD_BANDIT/)。
