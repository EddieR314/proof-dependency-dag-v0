# 代数题 Proof DAG 适合度初筛：本周执行规范 v0.1

## 范围

只处理题库中 `proof_domain_bucket=algebra` 的记录，并按证明机制候选路由到：函数方程、不等式、多项式、递推数列、复代数、离散代数。来源标签不能直接作为最终路由。

## 流程

1. 用 `prepare_screening_batch.py` 生成代数候选输入和机械风险提示。
2. Agent 按 Skill rubric 输出 `suitable / borderline / unsuitable`，但状态固定为 `not_reviewed`。
3. 用 validator 检查字段、ID、硬门槛和伪造人工状态。
4. 对全部 `borderline`、低置信结果和每个模块的 suitable/unsuitable 分层抽样。
5. 人工只确认三件事：来源是否完整、证明是否能忠实拆成 Fact-Inference、模型路由与拒绝理由是否合理。
6. 人工确认的 `suitable` 才进入完整 Proof DAG 构建；初筛本身不宣称证明正确、DAG 已完成或 Lean 已验证。

## 本轮基线

- 原始题库：750 条。
- 代数范围：250 条。
- 已验证 suitable 正例锚点：`0gif, 00q2, 06og, 0ldq, 0le0, 0chi`。
- 机械风险记录：8 条。风险提示只用于优先抽查，不等于 unsuitable。
- 先跑校准批次，通过人工误差分析后再扩到全部 250 条。

## 验收指标

- 人工确认后的 suitable precision；
- unsuitable 中的 false reject rate；
- 模块路由准确率；
- 各 reason code 的错误分布；
- 两名审核者在决策和主理由上的一致率。

初期不以“筛掉多少题”为目标，也不以模型能否解题或 Lean 成本作为 DAG 适合度指标。

