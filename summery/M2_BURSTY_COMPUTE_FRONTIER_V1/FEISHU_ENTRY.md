# 实验代号：M2_BURSTY_COMPUTE_FRONTIER_V1

## 实验问题

在固定 bursty-observation tracking 任务和训练数据量下，增加优化步数后，感觉位 motor-state feedback 的低容量优势是否仍存在；此前对比中 GRU 的不确定性是否会随训练预算变化？这是已看过相关 M2 结果后的探索性扩展，不是独立确认实验。

## 实验设置

使用 32 个新训练 seed block。比较 4 参数感觉位反馈、4 参数输出位反馈、4 参数无反馈、4 参数 scalar RNN 和 321 参数 GRU-8。训练集每个 seed 160 条、每条 160 步；固定训练可见性转移概率 `q=0.25`，分别在 60、120、240 次优化更新保存 checkpoint。测试使用同一配对轨迹，在 `q=0.50/0.25/0.125` 三种可见性转移概率下评估，每格 128 个 episode。episode 嵌套于训练 seed；区间按 32 个 seed block 重采样。

## 实验结果

主条件为长缺失段 `q=0.125`、240 次更新。感觉位反馈 tracking MSE 为 `0.66569`。它优于等参数 scalar RNN，差值 `MSE(RNN)−MSE(sensory)=+0.06183`（95% seed-block bootstrap 区间 `[+0.05816,+0.06580]`，32/32 seed block 为正）；也优于输出位和无反馈，差值分别为 `+0.01531` 与 `+0.01209`。GRU-8 随训练预算提高而明显改善：60 次更新时与感觉位反馈差异未定，120 和 240 次更新后 MSE 更低；240 次更新下 `MSE(GRU)−MSE(sensory)=−0.07726`（95% 区间 `[−0.08775,−0.06633]`，0/32 seed block 为正）。

感觉位反馈的 action energy 低于输出位反馈，但 MAE 更高、post-gap recovery 更慢。由此，MSE 的优势不是总体控制质量上的无条件优势，而是准确度、能量与恢复速度之间的权衡；更大的训练后 GRU 在 MSE 上占优。

## 分析与边界

结果支持一个窄的人工算法判断：在该模拟任务中，把上一时刻 motor output 放进 sensory-state update，相比相同参数量的 output-site、no-feedback 和 scalar-RNN 控制，能降低长缺失段下的 MSE；该优势随着训练削弱，且不胜过训练后的较大 GRU。任务中的 Markov 缺失过程是人工设定，不是 *C. elegans* RIM–AIY 回路的实测条件。因此本实验没有证明生物因果性、AI 的普遍收益或 NMI 级别的项目结论。

运行结果由独立核验器通过：184,320 episode rows、480 checkpoint rows；完整 seed × arm × update × visibility 网格齐全，主要 contrast 按 seed block 独立复算。首次 verifier 运行因 primary-condition 文本精确匹配错误而失败；修复核验字符串条件后通过，未改动 experiment output。

## 文件与 GitHub

- 合约：`summery/M2_BURSTY_COMPUTE_FRONTIER_V1/CONTRACT.md`
- 结果与失败经验：`summery/M2_BURSTY_COMPUTE_FRONTIER_V1/RESULTS.md`、`FAILURE_LOG.md`
- 模型和核验器：`model/M2_BURSTY_COMPUTE_FRONTIER_V1/`
- 数据、摘要、图和哈希：`data/results/M2_BURSTY_COMPUTE_FRONTIER_V1/`
- GitHub commit：待提交后补入
