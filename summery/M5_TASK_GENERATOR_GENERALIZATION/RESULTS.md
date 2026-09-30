# M5 跨输入生成器验证：结果与经验

## 本轮结论

这是在已经观察到 M5-v3 正结果后设计的事后验证；本轮固定学习率和迹线衰减，不是确认性实验。三个固定输入生成器下，norm-matched eligibility trace 相对 no-trace 的四延迟平均准确率差为 `+0.2284`，分层 task-seed bootstrap 95% CI 为 `[+0.2213, +0.2357]`。每个生成器的 30 个 task-seed 四延迟平均差均为正。

## 优点

- 三个输入统计条件均使用固定且相同的模型、教师目标、训练量、测试量、学习率和迹线衰减。
- 按 task seed 配对比较，bootstrap 时保留种子内四个 delay 和三种 arm 的配对。
- 保留 exact replay 强基线；没有把相对 no-trace 的优势误写成优于精确回放。
- 结果有完整逐任务 CSV，并通过独立重算核对主差值、区间、哈希和配对单元完整性。

## 失败与边界

- AR(1) 输入下短延迟出现反转：delay 1 trace-no-trace 为 `−0.1210`，delay 4 为 `−0.0123`；迹线优势只在 delay 16/64 出现。强时间相关输入让“当前样本替代延迟样本”的 no-trace 更新在短延迟时占优。
- Exact replay 在所有 12 个 generator×delay cells 都优于 trace；全条件平均准确率分别为 replay `0.761`、trace `0.559`、no-trace `0.331`。
- 本轮改变的是输入流分布，仍是同一个合成分类目标，并未跨到不同任务目标或真实神经数据。
- 本轮是 outcome-informed engineering validation；不能称为小脑机制验证、connectome motif transfer 或广义 AI 优势。

## 下一步纪律

本合同的实验已经结束，不根据结果调 `gamma` 或学习率。后续若要检验不同任务目标，必须另开新版本合同；本结果只支持三个已测试输入分布上的限定表述。

详见 [`RESULTS.md`](RESULTS.md)、[`M5_TASK_GENERATOR_GENERALIZATION_CONTRACT.md`](M5_TASK_GENERATOR_GENERALIZATION_CONTRACT.md) 与 [`POSTRUN_VERIFICATION.json`](../../data/results/M5_TASK_GENERATOR_GENERALIZATION/POSTRUN_VERIFICATION.json)。
