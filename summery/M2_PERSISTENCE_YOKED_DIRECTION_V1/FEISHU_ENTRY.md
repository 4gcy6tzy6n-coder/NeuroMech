## M2_PERSISTENCE_YOKED_DIRECTION_V1 — 边际运动持续性 yoke

**实验代号：** `M2_PERSISTENCE_YOKED_DIRECTION_V1`

**实验问题：** 从校正后的感觉反馈模型开发集抽取 forward/reverse bout 时长，构造不依据当前位置、朝向和温度采样的 motor-state yoke，检验边际持续性分布是否足以重现趋暖方向行为。

**实验结果：** 跨三个模拟噪声尺度，感觉位点模型减边际 yoke 的 warm-direction index 等权差为 `+0.45489`，95% seed-block bootstrap 区间 `[+0.44770, +0.46211]`，200/200 个测试 block 为正。标量 motor-only 对照差为 `+0.13997`（95% 区间 `[+0.13637, +0.14352]`）。

**匹配审计：** 在 noise `1.00` 和 `1.25`，held-out forward bout 的均值、中位数、P90、长运行比例和占用率差值相对较小；但实验没有预先冻结等价界限，不能称为匹配通过。在 noise `0.75`，均值时长差 `+0.609 s`、P90 差 `+2.623 s`、≥30 秒比例差 `+0.00878`、占用率差 `−0.01495`，yoke 匹配不足，因此跨噪声主对比不能被当作干净的 matched-control 结果。

**分析与边界：** yoke 的时长样本不依赖位置、heading 或温度，因而其趋暖指数接近零是这个设计下的预期。该结果提示单独的边际 bout-duration 采样未复现定向行为，但 V1 不能排除低噪声条件的 persistence mismatch，也不能识别被移除的条件依赖具体是哪一种。结果是先前 M2/V3/V4/V5 结果已知后的探索性源模型分析；没有新增动物证据、唯一突触机制或 AI 迁移证据。

**失败经验：** 独立采样 bout 时长丢掉完整轨迹的序列结构和终点删失信息，导致最低噪声条件下 yoke 与 source model 的运动分布偏离。下一轮若继续，改为从独立开发数据重放完整 motor-state trajectory，并在解释方向指标前先报告 held-out persistence adequacy。

**实现 incident：** 初次运行完成模拟后因各 arm CSV 字段不同而在写文件时中止；修正 union schema 后用相同固定种子重跑。首次运行未生成 held-out 结果或 summary，数值没有用于分析。

**材料：** [结果与分析](RESULTS.md)；[失败记录](FAILURE_LOG.md)；[实验契约](CONTRACT.md)。
