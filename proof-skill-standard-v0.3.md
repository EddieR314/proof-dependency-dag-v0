# 竞赛数学 Proof Skill 统一规范 v0.3

状态：组内讨论稿  
适用范围：代数、数论、组合、几何证明的规范化、Proof DAG、形式化接地、错误注入与审核  
目标公共 Schema：`proof-dag-schema-v0.4`

```yaml
document_type: meta_standard
executable_skill: false
standard_version: "0.3"
public_baseline: "proof-dag-schema-v0.4"
```

本文件规定领域 Proof Skill 的公共语义、输入输出、验证和晋升要求；本文件本身不是可单独执行的 Agent Skill。具体任务必须由兼容本规范的公共基础 Skill 和领域 Skill 执行。

## 0. 规范依据与优先级

本规范综合以下既有材料：

- `Node规范化.zip`
  - Fact Node；
  - Inference Node；
  - SPU；
  - Canonical Form；
  - Rule Schema；
  - Scope 与局部证明分支；
  - 状态模型；
  - 来源、依赖与错误传播。
- `critical_node_definition_1.pdf`
  - Derivable；
  - Node Blocking；
  - Critical Node 的反事实定义。
- `error_injection.pdf`
  - 单一受控修改；
  - First Break；
  - 错误传播；
  - target effect；
  - Error Injection 与 Critical Node 的关系。
- `260722 DAG规范化.pptx`
  - 输入、分析、输出三层系统边界；
  - Rule Registry；
  - DAG Builder；
  - structured artifact；
  - student version 与 teacher audit；
  - 图文一致性门槛。
- 已跑通的 Proof DAG + Lean 试点
  - Lean declaration mapping；
  - 自动 artifact 检查；
  - 独立验证状态；
  - 人工审核与数据等级。

若领域 Skill 与本规范冲突，以公共 Schema 和团队确认后的本规范为准。领域 Skill 不得自行更改公共语义。

### 0.1 v0.3 兼容性

v0.3 是公共接口的破坏性升级。迁移时至少执行：

| v0.2 | v0.3 |
| --- | --- |
| `correct_solution` | `candidate_reference_solution` + proof review |
| 单一 `annotation_level` | `current` / `requested` / `achieved` 三段状态 |
| `Inference.order` | 唯一且连续的 `source_order` |
| `mutated_dag.json` | `mutated_graph.json` |
| 节点内 support/availability/validation | 独立 Fact/Inference Evaluation |
| 节点内 `lean_declaration` | 单一 `formal_mapping.json` |
| `primary_inference_id` | 通用 `primary_site` + `injection_anchor` |
| `expected_first_break` | declared 与 independently computed 两份记录 |

v0.2 Artifact 不得只改版本号伪装成 v0.3；必须经过显式迁移和重新验证。

## 1. Skill 分层

采用“公共基础 Skill + 领域 Skill”的两层结构。

### 1.1 公共基础 Skill

`proof-dag-lean` 统一负责：

- 自然语言证明的规范化接口；
- Fact-Inference 二部 DAG；
- SPU；
- Rule Schema 与 binding；
- scope 与状态语义；
- Derivable 重算；
- Critical Node；
- 单错误 mutation；
- First Break 与错误传播；
- 形式化声明 mapping（当前已实现 Lean）；
- 自动验证与审核记录。

### 1.2 领域 Skill

代数、数论、组合、几何 Skill 只补充：

- 适用题型与不适用边界；
- 领域证明骨架；
- 常用定义和定理；
- 对象与 canonicalization 规则；
- 常见 Lean lemma；
- 高风险推理；
- 真实错误类型；
- 领域审核清单。

领域 Skill 必须调用公共流程产生统一 artifact，不能另建一套不兼容的 DAG 或标签体系。

## 2. 统一输入、版本绑定与 Source Gate

每道题至少提供：

```yaml
problem_id: string
problem_statement: string
candidate_reference_solution: string
domain: algebra | number_theory | combinatorics | geometry
subtype: string
source:
  problem: string
  solution: string
  source_record_id: optional[string]
  source_hash: string
current_annotation_level: raw | synthetic | silver_verified | gold
requested_target_level: synthetic | silver_verified | gold
promotion_profile: string
requested_formal_backend: none | lean | formalgeo | symbolic | other
requested_formal_coverage: none | local | critical_only | end_to_end
versions:
  skill_standard: "0.3"
  dag_schema: string
  candidate_graph_schema: string
  fact_schema: string
  inference_schema: string
  scope_schema: string
  mutation_schema: string
  canonicalizer: string
  rule_registry: string
  common_tooling: string
  domain_skill: string
```

进入构图前必须完成 Source Gate：

1. 题面、定义域、量词和约束完整；
2. 自然语言证明没有明显缺页或文本污染；
3. 原证明已经通过相应等级的数学审核；
4. 题目对象和 Goal 明确；
5. 仍有歧义的内容写入 `unresolved_log`，不得让模型静默补全；
6. 未通过 Source Gate 的证明不能被标为 correct graph。

外部答案与独立证明审核必须区分。答案形式与官方答案一致，不等于所给证明已经正确。

`candidate_reference_solution` 只是待审核的来源证明。审核结果另行记录：

```yaml
reviewed_solution: optional[string]
reviewed_solution_hash: optional[string]
proof_review:
  status: not_run | passed | failed | partial
  method: automatic | human | hybrid
  reviewer_ids: []
```

只有 `proof_review.status = passed` 且审核对象的 hash 与当前候选证明一致时，才允许生成 `reviewed_solution` 并用于构造 reference correct graph。自动检查可以辅助审核，但 Silver 或 Gold 所需的证明正确性结论必须包含具名人工审核。

数据等级不能由输入预先宣称。处理结束后由独立 promotion 流程写入：

```yaml
achieved_annotation_level: pending | synthetic | silver_verified | gold
```

生成器和领域 Skill 不得自行写入 `silver_verified` 或 `gold`。公共 Schema 或工具升级后，领域 Skill 必须迁移或明确绑定旧版本，不得静默混用不兼容版本。

## 3. 从自然语言到规范化证明

按以下顺序处理，不允许直接把句子按先后顺序连成图。

### 3.1 定位命题片段

从题面和证明中提取可判断真假的陈述。连接词本身不是 Fact。

### 3.2 补全省略与指代

显式恢复：

- 省略的主语；
- “二者”“它们”等代词；
- 被省略的点、线段、变量、集合或函数；
- 对应关系和对象顺序；
- 必要但未写出的局部条件。

不能可靠恢复时，写入 `unresolved_log` 并请求人工确认。

### 3.3 分离语言外壳与逻辑依据

删除“因为、所以、显然、于是”等语言外壳，但保留“使用 SSS”“由中点定义”“根据归纳假设”等逻辑依据，并将其映射为 Inference 或 Rule Schema。

### 3.4 原子化

- 可被后续分别使用的合取结论应拆成多个 Facts；
- 一个 Inference 只表示一次规则应用；
- 一个 SPU 只产生一个输出 Fact；
- 不可独立使用的数学对象不能被强拆成无意义 Facts；
- 存在性、否定、条件和量词结构必须保留。

### 3.5 Canonical Form

每个 Fact 同时保存：

- `statement`：供人阅读；
- `canonical_form`：供机器去重、匹配和验证；
- `source_spans`：回溯原文。

Canonicalization 至少包括：

1. 文本补全；
2. 对象标准化；
3. 关系标准化。

必须保留否定、量词、条件和有意义的对象顺序。对称关系可以按数学语义归一化，但不能把三角形对应顺序等结构简单按字母排序。

Canonicalizer 必须有版本号。Canonical Form 只说明“表达了什么”，不能单独证明某条规则适用。

## 4. Reference Proof DAG 与 Candidate Proof Graph

共享图核心定义为有限有向二部图：

```text
G = (F, I, E_in, E_out)
```

其中：

- `F`：Fact Node 集合；
- `I`：Inference Node 集合；
- `E_in ⊆ F × I`：Fact 被 Inference 使用；
- `E_out ⊆ I × F`：Inference 产生或支持 Fact；
- `F ∩ I = ∅`；
- reference correct graph 中不得存在有向环。

只允许两类逻辑边：

```text
Fact → Inference
Inference → Fact
```

不得直接建立 `Fact → Fact` 或 `Inference → Inference` 逻辑边。文本相邻不等于逻辑依赖。

`producers` 和 `consumers` 由 `input_bindings` 与 `output_fact_id` 自动计算，不作为人工独立维护的第二事实源。

### 4.1 Reference Proof DAG

`correct_dag.json` 强制满足：

- 有向无环；
- 普通 Inference 至少一个输入且恰好一个输出；
- Scope、binding 和 Rule Schema 合法；
- 所有声明有效的 SPU 可执行；
- 全局 target 可推出；
- 来源证明已经通过相应等级的审核。

### 4.2 Mutated Candidate Proof Graph

`mutated_graph.json` 共享 Fact、Inference、Scope 和边的核心 Schema，但允许显式表示循环依赖、缺少输入、非法 Scope 引用、无效规则应用和 unsupported Fact。异常必须出现在 evaluation 的状态与 reason codes 中，不能被当作 correct DAG 发布。

全文中的 “DAG” 默认指 reference correct graph；变异后的对象统一称为 candidate proof graph。实现宜使用共享 Graph Core Schema，再分别叠加 Reference 和 Candidate 约束，避免维护两套容易漂移的节点定义。

## 5. Fact Node 规范

Fact 表示一个完整、可判断、尽量原子的命题，但不承诺它已经被正确证明。

### 5.1 必需字段

```yaml
id: F...
statement: string
canonical_form: string
introduction_kind: given | assumed | case_assumed | constructed | derived
roles: [goal | intermediate | case_condition | contradiction | lemma_output]
scope: string
objects: []
source_spans: []
```

### 5.2 状态含义

Fact Node 只保存不随评价图变化的静态内容。支持和可用性写入独立评价记录：

```yaml
graph_id: string
fact_id: F...
support_status: pending | supported | unsupported
availability_cache: active | inactive | unknown
computed_by: string
evaluation_version: string
```

- `support_status`：在指定 `graph_id` 中是否有合法支持；
- `availability_cache`：可选的展示或加速缓存，不是权威逻辑；
- `consistency_status`：当前 scope 是否存在冲突，权威记录放在 `ScopeEvaluation`，不直接判断单个 Fact 为真或假。

Fact 对某个 Inference 可用，当且仅当：

```text
Available_G(f,i) = 1
```

其中 `Available_G(f,i)=1` 当且仅当：

```text
f 在 G 中得到支持
AND f 对 i 的 scope 可见
AND scope 生命周期允许该引用
AND f 未被 block
AND i 的规则允许这种跨 scope 使用
```

`supported` 不等于“由推理证明”。题设、合法局部假设和派生结论都可以在相应环境中被支持。

### 5.3 来源约束

- `given` 通常没有 producer；
- `derived + supported` 必须至少有一个合法 producer；
- Goal 在证明开始时可以是 `pending` 且没有 producer，证明完成后为原 Goal 增加 producer，不能复制第二个 Goal；
- `assumed` 或 `case_assumed` 必须记录其引入 scope 或 `introduced_by`；
- `constructed` 只表示通过合法构造引入对象相关命题，不表示构造规则已经被验证。

`introduction_kind` 只记录 Fact 如何进入图，`roles` 只记录它在证明中的功能。Goal 始终由 `roles: [goal]` 表达，不设置 `goal_declared` 来源类型。任何 Fact 都可能成为某个 Inference 的 premise，因此 `premise` 不作为固定 Fact role，而由 `input_bindings.premise_role` 表达。定义展开或定义判定属于 Inference 的 `rule_id`，例如 `definition_elimination` 或 `definition_introduction`。

### 5.4 ObjectExistence Fact

普通 Inference 不允许零输入。若自反性、构造或规则使用确实要求显式对象存在证明，可建立 ObjectExistence Fact，例如：

```text
Exists(Segment(A,D))
```

辅助构造在独立 Construction 规范完成前，不能被伪装成零输入 Inference。题图中“看起来存在”的对象也必须有可审计来源。

在 Construction Node 和对象生命周期规范冻结前，ObjectExistence Fact 是暂行建模规则，不得机械地为所有对象生成。若对象合法性已由 Lean 或其他类型系统保证，应在 formal mapping 中记录该类型来源。

## 6. Inference、SPU 与 Rule Schema

### 6.1 Inference

Inference 表示一次具体规则应用：

- 至少一个输入 Fact；
- 恰好一个输出 Fact；
- 输入通过 `premise_role` 绑定；
- 记录变量或对象绑定；
- 记录 scope、顺序、来源和验证状态。

必需字段：

```yaml
id: I...
spu_id: SPU...
source_order: integer
rule_id: string
scope: string
input_bindings:
  - fact_id: F...
    premise_role: string
variable_bindings: {}
output_fact_id: F...
source_spans: []
rule_application_group_id: optional[string]
risk_flags: []
```

`source_order` 表示 Inference 在原证明阅读顺序中的位置，不是拓扑序或执行序。它在全部 Inference 上构成到 `{1,...,|I|}` 的双射：不得重复、缺号或为空。一个源句拆成多个 Inference 时，使用连续 `source_order`，并通过共同 `spu_id` 或 `rule_application_group_id` 保留分组。

Inference 的图相关状态单独记录：

```yaml
graph_id: string
inference_id: I...
intrinsic_status: unchecked | valid | invalid
effective_status: executable | blocked | invalid
reason_codes: []
computed_by: string
evaluation_version: string
```

`intrinsic_status` 判断规则应用本身；`effective_status` 区分可执行、因上游输入而阻塞和本步骤自身无效。下游 `blocked` 不是新的直接注错。

### 6.2 SPU

```text
SPU = Input Facts + One Inference + One Output Fact
```

SPU 不是第三类图节点，而是最小可独立检查的局部结构。

同一次自然语言规则应用产生多个直接结论时，从建图开始就拆成多个单输出 SPU，并用 `rule_application_group_id` 保留共同来源。

### 6.3 Rule Schema

Rule Schema 是可复用规则模板，不是某道题中的具体应用。至少描述：

```yaml
rule_id: string
name: string
category: string
input_patterns: []
variables: []
variable_constraints: []
output_pattern: {}
scope_constraints: []
version: integer
```

合法性检查包括：

1. 输入存在且当前可用；
2. 输入数量、谓词和 premise role 匹配；
3. 变量与对象绑定一致；
4. 附加条件满足；
5. 输出匹配当前单输出视图；
6. scope 合法；
7. 不产生循环。

规则应存入版本化 Rule Registry，并配套 binding、scope 和输出测试。Critical/Error 分析层不得临时依靠字符串或硬编码 `if-else` 猜规则。

### 6.4 高风险标记

高风险与 Critical 是两套概念。Critical 由反事实重算确定；风险标记只用于安排人工审核和形式化优先级。公共枚举至少包括：

```yaml
risk_flags:
  - hidden_domain_condition
  - quantifier_sensitive
  - scope_sensitive
  - case_exhaustiveness
  - existence_witness
  - floor_or_ceiling
  - wlog
  - nonlinear_arithmetic
  - large_lemma_compression
  - geometric_diagram_dependency
  - external_theorem_dependency
```

领域 Skill 可以提交新增枚举提案，但不得使用自由文本风险名污染公共数据。是否进入 `high_risk` 队列由版本化发布 profile 的规则或阈值决定。

## 7. Scope 与局部证明分支

Scope 使用层级结构，例如：

```text
global
global/contradiction_1
global/case_1
global/case_2
global/lemma_1
```

基本规则：

- 子 scope 可以使用合法祖先 Facts；
- 兄弟或子 scope 的 Fact 不能被直接跨域引用；
- 输出通常保留在 Inference 所在 scope；
- 局部结果进入父 scope 必须经过显式 discharge、merge 或 export；
- `promotion` 是合法跨 Scope 输出的上位概念，不作为第四种并列操作；
- 分支退出后，局部 Facts 对后续 Inference 通常不可见；
- 分支退出是生命周期变化，不是逻辑错误。

局部分支至少记录：

- scope ID 与 parent；
- 分支类型；
- 引入步骤；
- 局部条件；
- 活动状态；
- 退出条件；
- discharge、merge 或 export 的父 Scope 输出。

分类讨论必须验证覆盖性；互斥性是否必需由具体 aggregation rule 决定。

术语约定：

- `discharge`：消去局部假设，例如反证法或条件证明；
- `merge`：合并 case 分支；
- `export`：将局部引理的结论导出到父 Scope。

## 8. 状态模型与错误传播

必须区分静态节点和以下相对于 `graph_id` 的动态评价：

```text
FactEvaluation.support_status
Available_G(f,i)
ScopeEvaluation.consistency_status
InferenceEvaluation.intrinsic_status
InferenceEvaluation.effective_status
```

上游失效后，不能按文本顺序把后续全部标红。应：

1. 找到直接受影响的 Inferences；
2. 重新检查 input、rule、binding、output 和 scope；
3. 更新 Inference 的 intrinsic/effective status；
4. 重新计算输出 Fact 的全部合法 producers；
5. 只有所有合法 producers 都失效时，Fact 才变为 unsupported；
6. 继续传播到固定点。

下游因缺少支持而失败属于传播结果，不自动构成第二处注入错误。

Scope 中出现矛盾时，记录 `ScopeEvaluation.inconsistent` 和冲突 Fact 集合；不能仅凭冲突自动断言其中某个 Fact 为假。

## 9. Derivable 的统一语义

令 `R ⊆ F` 为当前证明环境接受的初始 Facts。定义：

```text
D0 = R

D(k+1) = Dk ∪ {
  Out(i) |
  i intrinsically valid,
  scope legal,
  ∀f ∈ Prem(i), f ∈ Dk and Available_G(f,i)=1
}

D_G = ⋃ Dk
```

于是：

```text
Derivable_G(f) = 1  iff  f ∈ D_G
```

有限图上该单调过程必然稳定。实现应使用 worklist 或等价固定点算法。

`Derivable_G(f)=0` 只表示当前图不能从当前根 Facts 推出 `f`，不表示数学上 `f` 为假。

以下功能必须共用同一 Derivable 引擎：

- correct graph validation；
- mutation 后的状态重算；
- First Break；
- Critical Node；
- target effect。

含环的 reference graph 直接判为结构非法且不可评估；mutation 新增的环可保留在 candidate proof graph 中，并使首次引入该循环依赖的 Inference 以 `cyclic_dependency` 失效。

## 10. Critical Node

Critical 不是节点的固有标签，而是相对于 `(graph, target, candidate)` 的反事实实验结果。

### 10.1 Node Blocking

对候选 `v ∈ (F ∪ I) \ {t}` 执行 full node block：

- 停用 `v` 及其 incident edges；
- 保留其他节点和边；
- 从初始 Facts `R` 重新计算 Derivable；
- 不按文本位置删除下游节点。

若 blocking 一个 root Fact，应在重算时从 `R` 中移除它。

### 10.2 正式定义

```text
Critical_(G,t)(v) = 1
iff
v != t
and
Derivable_G(t) = 1
and
Derivable_(G⊖v)(t) = 0
```

三种输出：

- `critical`：before=1，after=0；
- `noncritical`：before=1，after=1，存在不使用 `v` 的完整合法替代推导；
- `not_evaluable`：before=0，基线本来不能推出目标。

度数、下游数量、最小条件数和中心性可以作为候选排序特征，但不能代替 Critical 的定义。

### 10.3 Critical Evaluation Record

至少记录：

```yaml
graph_id: string
target_fact_id: F...
candidate_id: F... | I...
candidate_type: fact | inference
block_mode: full_node_block
candidate_is_target: false
derivable_before: boolean
derivable_after: boolean | null
critical_status: critical | noncritical | not_evaluable
```

同一节点对不同 target 可以得到不同结果。

## 11. Error Injection 与 First Break

### 11.1 Base Graph Gate

注错前必须满足：

- target 可推导；
- 所有被声明为有效的 Inferences 通过检查；
- 图无环；
- schema、binding 和 scope 合法；
- correct graph 已达到所声明的审核等级。

### 11.2 单一受控修改

一次 mutation `μ` 只允许一个可解释的主要逻辑意图，但该意图可以造成多个底层字段变化。

允许操作包括：

- 删除必要输入；
- 替换规则；
- 修改 variable/object binding；
- 修改唯一输出；
- 删除必要 Fact、Inference 或 dependency edge；
- 引入一次非法跨 scope 引用；
- 漏掉一个 case；
- 引入一次循环依赖；
- 完整 block 一个节点。

必须满足：

```text
Gμ ≠ G
```

只改写表面措辞、而 canonical form、依赖、规则和数学含义均未改变，不算错误注入。不能使用暴露标签的固定模板句硬凑错误。

### 11.3 Fact 替换

Fact 语义被替换时不能沿用原 ID 偷换含义：

- 保留旧 Fact 作为 `before`；
- 新建具有新 ID 和新 canonical form 的 Fact；
- 重绑定相关边；
- 保留 source span 与 provenance；
- 重新计算支持状态。

若替换 derived Fact，必须同时修改其 producer/output；否则新 Fact 应为 unsupported。

### 11.4 First Break

设 `source_order` 在全部 Inference 上构成双射，并定义：

```text
i ≺ j  iff  source_order(i) < source_order(j)

FB(Gμ) = min_≺ { i ∈ I : OK_(Gμ)(i)=0 }
```

即按原证明固定阅读顺序首次无法合法完成的单输出 SPU。`source_order` 缺失、重复或缺号时，Inference 级 First Break 不可评估，不能靠 ID 或拓扑排序代替。

检查顺序：

1. 输入是否存在且可用；
2. scope 是否可见；
3. rule 和 premise roles 是否匹配；
4. variable/object bindings 是否一致；
5. 输出是否为规则的直接结论；
6. 是否引入循环。

Fact 级 First Break 例外：

- 题设被错误转写；
- Goal 被错误解析；
- 量词、否定或对象被错误补全；
- Fact 被错误合并或拆分；
- canonicalization 把不同命题错误合并。

因此 First Break 默认定位 Inference/SPU。Fact extraction 错误属于 pre-graph 阶段，必须记录独立的 extraction order、source span 和 reason code，不能与 Inference 的 `source_order` 混用。

### 11.5 Propagation 与 Target Effect

mutation 后从根 Facts 重新执行整张图。分别记录：

- `target_breaking`：mutation 后 target 不可推导；
- `target_preserving`：局部步骤错误，但 target 仍由替代路径推出。

两类都可以成为有效错误样本。

### 11.6 与 Critical 的区别

- Critical 使用 full node block，回答候选对 target 是否不可替代；
- Error Injection 使用 local mutation，回答错误从哪里开始以及影响什么。

只有当：

```text
Gμ = G⊖v
```

时，Critical 结果才能与 mutation 的 target effect 直接对应。候选节点 critical 不意味着对它的任意局部修改都会破坏 target。

### 11.7 Mutation Record

Mutation Record 使用通用注入位置：

```yaml
base_graph_id: string
operation: string
primary_site:
  type: fact | inference | edge | scope
  id: string
injection_anchor:
  type: fact | inference | none
  id: optional[string]
declared_expected_first_break:
  type: fact | inference
  id: string
computed_first_break:
  type: fact | inference | none
  id: optional[string]
first_break_match: boolean
before: object
after: object
graph_changed: true
target_effect: target_breaking | target_preserving
seed: optional[integer]
provenance: object
```

- `primary_site` 是程序实际修改的位置；
- `injection_anchor` 是 reference graph 中用于 Critical 分析或溯源的节点；
- `declared_expected_first_break` 是生成器或人工的预测；
- `computed_first_break` 只能由独立评价器重新计算；
- 只有预期与计算结果一致，First Break 检查才通过。

`declared_expected_first_break` 不能自行充当 Gold 标签。

## 12. 形式化接地与验证边界

形式化后端和 DAG 回答不同问题：

- DAG 检查结构、依赖、scope、替代路径和传播；
- 形式化后端检查被编码声明是否被相应 verifier 接受。

统一声明：

```yaml
formal_backend: none | lean | formalgeo | symbolic | other
formal_backend_id: optional[string]
formal_backend_version: optional[string]
formal_coverage: none | local | critical_only | end_to_end
```

`other` 必须同时提供具体 backend ID、版本、验证命令和证据文件。当前公共工具链只实现并验收 Lean；其他选项只是前向兼容接口，接通并通过验收前不得声称已实现。

### 12.1 覆盖等级

- `none`：没有 Lean 声明；
- `local`：部分关键或高风险 Inference 被编译 lemma 覆盖；
- `critical_only`：声明的 Critical Inferences 已全部覆盖，但不保证非关键步骤或端到端目标；
- `end_to_end`：目标定理由原始假设完整编译。

不能因为一个局部 lemma 编译成功，就声称整个自然语言证明已经形式化。

### 12.2 Mapping 的单一事实源

Fact 和 Inference 节点本体不保存 `lean_declaration` 或其他后端声明。`formal_mapping.json` 是唯一权威映射；当后端为 Lean 时至少记录：

```yaml
formal_backend: lean
mapping:
  - inference_id: I...
    output_fact_id: F...
    declaration: string
    source_file: string
    expected_compile_result: pass
toolchain: string
mathlib_revision: string
```

界面或报告中的节点级映射必须从该文件派生，不能人工维护副本。

自动检查：

- DAG ID 存在；
- declaration 存在；
- Inference 与 output Fact 映射一致；
- 覆盖率；
- 无 `sorry`/`admit`；
- 实际 `lake build`。

人工检查：

- 自然语言命题与 Lean statement 是否等价；
- 定义域、量词、正负性和局部假设是否忠实；
- Lean 证明是否验证了原步骤，而不是更弱或不同的命题。

规模化阶段可以先对关键、高风险和 First Break 附近的 Inferences 做局部 Lean，不要求两万题全部先完成端到端 Lean。

## 13. 独立验证状态与数据等级

数据等级不能替代具体检查记录。自动验证与人工语义审核分别记录：

- `source_gate`
- `proof_review`
- `dag_schema_validation`
- `dag_structural_validation`
- `dag_derivability_validation`
- `dag_semantic_faithfulness_review`
- `scope_structural_validation`
- `scope_semantic_review`
- `formal_build`
- `formal_mapping`
- `formal_translation_review`
- `mutation_structural_validation`
- `mutation_semantic_review`
- `student_text_graph_consistency_review`

状态：

- `not_run`
- `passed`
- `failed`
- `partial`
- `not_applicable`

方法：

- `automatic`
- `human`
- `hybrid`

### 13.1 Promotion 权限

生成器和领域 Skill 只提交检查结果与 promotion request。独立 promotion 流程根据状态、审核签名和发布 profile 写入 `achieved_annotation_level`。

### 13.2 数据等级

`synthetic`：

- 所有发布 profile 声明为强制的自动检查通过；
- 尚未完成具名人工语义审核。

`silver_verified`：

- 满足 Synthetic；
- 至少一名具名人工审核者通过 proof review；
- 通过 DAG semantic faithfulness review；
- 通过适用的 scope semantic review；
- 通过 mutation semantic review；
- 形式化后端和覆盖范围已如实声明；
- 不存在未解决的 critical issue。

`gold`：

- 满足 Silver；
- 至少一名独立于构建者的第二审核者完成复核；
- 不存在未解决的 critical 或 major issue；
- 达到数据集发布 profile 规定的最低 formal backend/coverage，而不是由单个样本任意降低要求；
- 所有自动结果能在干净环境中复现；
- 所有 Gold 标签可追溯到明确证据。

Gold 不默认等于端到端 Lean；但 `formal_coverage: none` 只有在发布 profile 明确允许时才可能晋级。

Schema 合法、图无环或 Lean 编译通过都不能单独把样本提升为 Gold。

## 14. 输出 Artifact 与系统边界

### 14.1 当前必须产出

每道题至少包含：

- 不可变的题面、候选参考证明与 source hashes；
- reviewed solution（若 proof review 通过）及 proof review 记录；
- 规范化 SPU；
- correct graph；
- correct evaluation；
- Lean 源文件或明确的未覆盖记录；
- Lean mapping；
- mutated graph；
- mutation 与 First Break；
- mutated evaluation；
- Critical evaluation（若执行）；
- verification report；
- human review checklist；
- unresolved log；
- provenance。
- manifest、版本、校验和与复现说明。
- promotion request、实际 achieved level 与决策证据。

推荐结构：

```text
problem.md
source_record.json
proof_review.json
correct_dag.json
correct_evaluation.json
mutated_graph.json
mutated_evaluation.json
critical_evaluation.json
Proof.lean
formal_mapping.json
verification_report.json
review_checklist.md
unresolved_log.json
promotion_record.json
artifact_manifest.json
VERSION
checksums.sha256
REPRODUCE.md
tooling_versions.json
source_change_log.md
zip_integrity_report.txt
```

内容可以内嵌，不强制每项独立成文件。SPU 可内嵌在 Inference 中，mutation 可内嵌在 mutated graph 顶层。不得同时人工维护重复字段。

`artifact_manifest.json` 至少记录 artifact/problem ID、版本、source hashes、Schema 和工具版本、领域 Skill 版本、Git commit、形式化后端与工具链、生成文件以及人工审核者。

发布前必须在干净目录重新生成图和报告，运行单元测试，检查标准 ZIP 兼容性，验证校验和，并确认 Checker、Core、Schema、测试和报告来自同一版本。

### 14.2 Structured Artifact 与自然语言错题分层

Error Injection 当前直接产出的是结构化错误图和审计记录，不等于已经生成可信的学生版自然语言错题。

自然语言输出应由独立 Graph Interpreter 或 surface realizer 完成：

```text
mutated graph
→ source-span 局部编辑
→ rule template fallback
→ 必要时 LLM polish
→ 图文一致性复核
```

两种输出：

- Student Version：只显示可读错误证明，不泄露错误标签；
- Teacher Audit：包含 mutation、First Break、reason codes、criticality、target effect 和节点溯源。

文本与图语义不一致时不得发布。

### 14.3 当前不能夸大的能力

在相应模块真正通过验收前，不能声称已经实现：

- 全自动自然语言 DAG Builder；
- 完整统一 Rule Registry；
- 两万题端到端 Lean；
- 自动生成真实学生风格错题；
- 自动证明自然语言到 Lean 翻译忠实；
- 整个领域的通用 Skill。

## 15. 领域 Skill 文件规范

推荐结构：

```text
skill-name/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── domain-playbook.md
│   ├── rule-inventory.md
│   └── review-checklist.md
└── scripts/
    └── deterministic-checks.py
```

要求：

- Skill 名称只使用小写字母、数字和连字符；
- `SKILL.md` frontmatter 只保留 `name` 和 `description`；
- description 写清功能、触发场景和适用边界；
- `SKILL.md` 保留核心工作流与资源入口；
- 详细规则放入 `references/`；
- 可重复、确定性检查放入 `scripts/`；
- 不重复维护同一规则；
- 新 Skill 使用初始化工具创建；
- 完成后运行 `quick_validate.py`；
- 领域 Skill 必须引用公共输入输出与验收规范。

## 16. 自动建图与人工协同

AI Assistant DAG Builder 可以：

- 提议 Fact/SPU 切分；
- 提议 canonical form；
- 提议 Rule Schema 和 dependency；
- 标记 unresolved 或低置信度部分；
- 生成形式化候选声明（当前为 Lean）。

AI 不能静默定稿以下内容：

- 原证明数学正确性；
- 复杂依赖的语义充分性；
- 自然语言到形式化声明的忠实性；
- scope discharge；
- 错误真实性与单一性。

审核顺序建议：

```text
A：原证明与 formal translation review
→ B：DAG semantic review
→ C：promotion / annotation level 确认
```

自动检查可并行执行，但 promotion 必须以全部必要记录为依据。

## 17. 前向测试与扩展到两万题

### 17.1 Smoke Test

每个领域 Skill 先使用至少 3–5 道未参与 Skill 编写的新题，确认接口、完整流程和错误退出机制可以运行。Smoke Test 只能证明流程没有立即失效，不能证明领域 Skill 已成熟。

### 17.2 Acceptance Evaluation

正式扩规模前，使用覆盖主要 subtype 的更大未见样本，并由团队预先冻结验收阈值。至少记录：

- Source Gate 通过率；
- SPU/DAG 自动生成率；
- unresolved 数量；
- DAG schema 通过率；
- DAG semantic 人工修改率；
- Lean local 与 end-to-end 覆盖率；
- Lean translation 修改率；
- mutation 成功率；
- First Break 准确率；
- 图文一致性通过率；
- 单题人工时间；
- p50 / p95 运行时间；
- 主要失败类型。

扩大规模的门槛不是“某一道题跑通”，而是：

- 格式统一；
- 标签可靠；
- Skill 在未见题上可复用；
- 人工成本可测量且可接受；
- 失败能够显式退出而不是伪造结果。

## 18. Failure / Stop Rules

1. 候选参考证明存在未解决数学漏洞：停止构建 reference correct graph，状态保持 unresolved。
2. 只能通过加强前提或削弱结论使形式化声明通过：不得静默修改，记录 `translation_mismatch`。
3. 无法确定 Fact、Inference、Rule 或 Scope：写入 `unresolved_log`，不得猜测为定稿。
4. 领域需求与公共 Schema 冲突：提交公共规范变更，不得在领域 Skill 中私改公共字段。
5. Mutation 无法证明是真错误，或产生多个独立错误：拒绝该 mutation。
6. Student Version 与 candidate proof graph 不一致：不得发布。
7. 形式化后端失败：不得使用 `sorry`、`admit` 或等价占位伪造通过，应记录失败状态和日志。
8. 版本、source hash、mapping 或 reviewer 证据无法对齐：不得 promotion。

AI Agent 遇到 Stop Rule 时必须留下结构化失败记录，而不是为了完成任务生成看似完整的 Artifact。

## 19. 尚未统一的开放问题

以下问题不得在单个领域 Skill 中私自定案：

- Construction Node 或辅助构造的正式表示；
- 反证 discharge 与 case merge 的统一 Rule Schema；
- 隐含常识是否全部进入 Rule Registry；
- 代数化简、数值计算和领域定理是否共用一套规则层；
- Fact-level First Break 的统一数据 Schema；
- Graph Interpreter 的图文一致性自动验证；
- 各发布 profile 的 Gold 最低形式化后端与覆盖要求；
- 大规模 benchmark 的运行时间和 p95 延迟。

## 20. 来源覆盖表

| 原始来源 | v0.3 对应章节 |
| --- | --- |
| Fact Node 规范 | 3、5 |
| Fact Node 建立流程 | 3 |
| Inference Node 与 SPU 规范 | 4、6 |
| Canonical Form | 3.5 |
| Rule Schema | 6.3 |
| Scope 与局部分支 | 7 |
| 状态模型、来源与错误传播 | 5、8 |
| First Break | 11.4 |
| `critical_node_definition_1.pdf` | 9、10 |
| `error_injection.pdf` | 11 |
| `260722 DAG规范化.pptx` | 9、10、11、14、16、17、18 |
| Proof DAG + Lean 试点 | 12、13 |
| 组内关于四领域 Skill 的讨论 | 1、15、16、17 |
| `proof-skill-standard-v0.2_修改意见.md` | 2、4–14、17–20 |
