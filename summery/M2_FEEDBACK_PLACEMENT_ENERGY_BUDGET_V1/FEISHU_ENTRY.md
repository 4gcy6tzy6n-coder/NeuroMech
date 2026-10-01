<hr/>

# 实验代号：M2_FEEDBACK_PLACEMENT_ENERGY_BUDGET_V1

## 实验结果

本实验在 16 个配对 seed block 上，先用独立验证 episode 为各控制器选择能耗惩罚系数，再在 held-out transient-pulse episode 上比较感觉状态端反馈与输出端反馈。两组均满足验证阶段选出的策略及 held-out 测试能耗预算：感觉状态端 command energy 均值为 0.4401，95% seed-block 区间为 [0.4100, 0.4656]；输出端为 0.4558，[0.4300, 0.4825]。主要对比为 movement MAE（感觉状态端减输出端），均值 +0.01428，95% 区间 [−0.00106, +0.02960]。点估计偏向输出端，但区间跨过零，因此没有建立任一反馈位置的可靠优势，也没有证明二者等效。

修正后的 canonical run 包含 320 个拟合候选、30,720 条 validation episode、80 个选择策略、15,360 条 test episode 和 240 条 seed-block 汇总。独立 verifier 通过；独立全量重跑的验证、策略选择、测试 episode、seed 汇总及 summary JSON 均逐字节一致，fit manifest 除计时字段外一致。

## 分析与边界

本实验是受到先前结果启发的事后探索性人工控制实验。0.50 能耗预算是在查看前一轮能耗结果之后设定的，因此不能称为独立确认。结果只说明在该合成任务与该预算定义下，两种选定策略都满足测试能耗标准；感觉状态端没有显示 MAE 优势。它不是生物能效证据，不验证 C. elegans 神经机制，也不代表广泛 AI 性能收益。GRU-8 有 297 个参数，远多于标量控制器，本轮相关比较仅作描述。

首次运行因评估循环误把所有 16 个 evaluation block 都套用到每个训练模型，生成重复且错误标记的行数。冻结 verifier 在结果解释前通过行数检查将其拒绝；该轮全部数值无效并已排除。修复仅将评估限制在当前训练 block，未改变实验假设、预算、模型、endpoint 或统计规则。失败运行以压缩 CSV 和哈希索引保留，以便审计。

## 归档

完整结果、限制与失败记录见仓库 [README](../../README.md)、[实验结果](RESULTS.md)、[失败记录](FAILURE_LOG.md)、[执行事故](EXECUTION_INCIDENT_01.md) 和 canonical 数据目录。冻结协议、模型代码、验证器及数据已提交至 NeuroMech 的 `experiment-publication` 分支。
