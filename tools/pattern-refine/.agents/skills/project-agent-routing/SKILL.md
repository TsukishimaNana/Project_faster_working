---
name: project-agent-routing
description: Use when Codex handles PatternRefine MVP development, task routing, subagent coordination, validation gates, or project-direction decisions.
---

# Project Agent Routing

## 核心原则

先分级，再执行。主线程拥有最终状态写入权；推进子代理只拥有协调权；编程子代理只拥有局部执行权。

当前 PatternRefine 项目还必须遵守以下硬约束：

- 客户主交付物是最终 SVG，不是 `refined.pdf`。
- 内部主验收是逐裁片 `max deviation <= 0.2mm`。
- `debug-pass`、结构接近、object count 接近都不是通过。
- 当前单样本 MVP 主线是 reference-guided production reconstruction；scan-only centerline 只作为诊断和后续泛化路线。
- `knowledge_base/PDF-SVG/Original_PinkShirts` 只读。
- 主线程必须对“MVP 结果是否可交付”负责，不能把测试绿灯、文档完成或阶段完成等同于交付完成。

主线程负责读取完整 Handoff、agents 和 OpenSpec；子代理默认只接收压缩派工单，避免每个任务重复加载全量项目上下文。

## 任务分级

| 等级 | 判断标准 | 执行方式 |
|---|---|---|
| L0 | 只读状态、解释代码、定位信息、不改文件 | 主线程直接处理 |
| L1 | 1-3 个文件，边界明确，局部测试可覆盖，不改变 OpenSpec 范围 | 主线程按 TDD 实现和验证 |
| L2 | 多文件或单个 OpenSpec 小项，需要独立实现和审查 | 主线程派 1 个编程子代理，自己审查 diff 和最终验证 |
| L3 | 一个 OpenSpec 大项或阶段，需要拆分、协调、阶段验证 | 主线程派 1 个推进子代理；推进子代理可协调编程子代理 |

升级一档：跨前端/后端/文档、超过 3 个文件、OpenSpec/代码/计划不一致、验证失败原因不局部、主线程上下文压力明显增加。

降级处理：只读分析、单文件修复、单测试补充、文案或文档小修。

## 决策顺序

1. 判断是否只读。是则 L0。
2. 判断是否可由主线程在一个小步内完成。是则 L1。
3. 判断是否是单个明确小项。是则 L2。
4. 判断是否是阶段或大项推进。是则 L3。
5. 发现冲突、权限、验证失败或上下文膨胀时，重新分级。

## 角色边界

主线程：
- 读取 Handoff、agents、OpenSpec、计划和任务进度，并将其压缩成任务所需上下文。
- 决定 L0-L3 路由。
- 拥有 Git 写操作、OpenSpec 勾选/归档、依赖安装、网络访问、全量验证和长期服务。
- 对推进子代理返回的完成包做抽查，不只凭一句 DONE 勾任务。
- 决定当前结果属于：继续开发、内测版、可交付 MVP。
- 当 reference 路线、逐裁片 `0.2mm` 或 final SVG 目标发生冲突时，由主线程负责裁决并纠偏。
- 派发子代理时不要 fork 完整历史，除非任务确实依赖长对话细节。

推进子代理：
- 只用于 L3。
- 负责阶段上下文、任务拆分、编程子代理协调、diff 审查和验证汇总。
- 可调用推理子代理，但不得调用其他推进子代理。
- 不得 `git add`、`git commit`、`git push`、安装依赖、启动长期服务、修改 OpenSpec 勾选或归档 change。
- 收到 `BLOCKED_PERMISSION` 后必须暂停阶段，原样上报主线程。
- 不得擅自宣布“MVP 已完成”；你只能给出阶段完成判断和风险结论。

编程子代理：
- 只负责窄范围实现和局部测试。
- 默认不阅读 Handoff、完整 agents、完整 OpenSpec 或全仓库 diff；只读取派工单指定文件和必要邻近代码。
- 不得提交代码、安装依赖、访问网络、启动长期服务、修改 OpenSpec 勾选或归档 change。
- 遇到权限确认、登录、安装、网络、Git 写入、全局配置或长期服务需求时，立即返回 `BLOCKED_PERMISSION`，不要等待、重试或请求用户确认。
- 完成对应任务后应及时关闭，不保留空转会话。
- 不得把 outline 微调、中间 SVG 改善或宽松测试通过描述成“MVP 进展完成”。

## 并发上限

- 推进子代理同时最多 2 个。
- 推理子代理同时最多 4 个。
- 推进子代理和推理子代理总同时最多 4 个。
- 如果已经接近上限，主线程应优先减少并行度，避免写入范围冲突和上下文漂移。

## 上下文预算规则

- Handoff 是新主线程接手包，不是子代理启动包。
- agents/OpenSpec 由主线程读取和裁剪；子代理不得被要求“先读全部项目必读文件”。
- L1 任务不转派；L2 只派一个窄范围编程子代理；L3 才派推进子代理。
- 单个子代理派工单目标控制在 30-60 行，只包含当前任务需要的路线、文件、命令和验收标准。
- 子代理输出只写摘要和关键证据，不贴完整 diff、完整测试日志或无关 `git status`。
- 子代理完成后主线程应及时关闭；同一子代理只在连续相关小任务中复用。
- 工作区存在大量既有改动时，主线程只给子代理指定写入范围，不要求它解释全仓库状态。

## 压缩派工单模板

```text
你是 [编程子代理/推进子代理]，不要读取完整 Handoff、完整 agents.md 或完整 OpenSpec；以下派工单是有效上下文。
WORKDIR: D:\my_project\Project_faster_working\tools\pattern-refine
ROUTE: 当前单样本 MVP = reference-guided production reconstruction。scan-only centerline 只作诊断；final SVG 是客户交付物；逐裁片 max deviation <= 0.2mm 才可交付。
TASK: [一个可验证小任务]
WRITE_SCOPE: [允许修改的文件/目录]
READ_SCOPE: [必须阅读的具体文件；不要扩展到全仓库，除非说明原因]
COMMANDS: [允许的只读/局部测试命令]
FORBIDDEN: git 写操作、安装依赖、网络、长期服务、OpenSpec 勾选/归档、修改 knowledge_base 原始目录。
VALIDATION: [父级期望的最小验证]
RETURN: STATUS, CHANGED_FILES, VALIDATION, RISKS, NEXT。不要粘贴完整 diff 或长日志。
```

## 状态码

| 状态 | 含义 | 父级处理 |
|---|---|---|
| `DONE` | 任务完成，允许范围内验证已通过 | 进入审查或最终验证 |
| `DONE_WITH_CONCERNS` | 完成但有风险、假设或未覆盖项 | 先评估风险，再决定是否审查 |
| `NEEDS_CONTEXT` | 缺少上下文 | 父级补充上下文后继续 |
| `NEEDS_MAIN_THREAD_COMMAND` | 需要主线程执行全量测试、build、Git 状态等命令 | 主线程执行并回传结果 |
| `BLOCKED_PERMISSION` | 遇到权限、安装、网络、Git 写入、长期服务或全局配置 | 必须逐级冒泡到主线程；暂停新任务 |
| `FAILED_VALIDATION` | 实现后验证失败 | 记录失败命令、输出和可能原因后修复 |

## 权限红线

子代理不得执行：

- `git add`、`git commit`、`git push`
- `npm install`、`pip install`、`uv sync`
- 创建或删除 worktree
- 修改全局 Git 配置
- 启动长期 dev server
- 网络下载依赖或登录外部服务
- 删除文件或大规模移动目录
- OpenSpec 勾选或归档操作；`validate` 仅在主线程明确允许时运行

权限事件不是普通失败。推进子代理不得把 `BLOCKED_PERMISSION` 改写成“未完成”，也不得继续派发新编程子代理。

## 完成包

子代理返回时必须包含：

```text
STATUS: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | NEEDS_MAIN_THREAD_COMMAND | BLOCKED_PERMISSION | FAILED_VALIDATION
SCOPE: 本次负责的任务和文件范围
CHANGED_FILES: 修改过的文件
VALIDATION: 已运行命令和结果；未运行命令及原因
RISKS: 风险、假设、半成品状态
NEXT: 建议父级下一步
```

涉及 MVP 质量的任务，必须额外包含：

```text
DELIVERY_IMPACT: 对 final SVG / per-piece 0.2mm / reference-guided 主线的影响
ROUTE_CHECK: 是否仍有 scan-only/outline 主线漂移风险
```

推进子代理的阶段完成包还必须包含：

```text
OPEN_SPEC_TASKS: 建议主线程勾选的任务
DIFF_REVIEW: 已审查的行为和文件
MAIN_THREAD_COMMANDS: 需要主线程执行的命令
```

## 常见错误

- 把 L1 小改动升级成 L3，浪费上下文。
- 每个子代理都重读 Handoff、agents 和完整 OpenSpec，导致两个任务后上下文耗尽。
- 转派时 fork 完整主线程历史，而任务实际只需要 30 行派工单。
- 子代理等待权限确认，导致超时。正确做法是立即返回 `BLOCKED_PERMISSION`。
- 推进子代理吞掉权限事件，只说“阶段未完成”。正确做法是原样冒泡。
- 主线程只看 DONE 就勾 OpenSpec。正确做法是抽查 diff、跑验证、再勾选。
- 让多个编程子代理同时改同一批文件。正确做法是拆成互不重叠的写入范围。
- 把 `cleaned.svg`、`semantic.svg`、`refined.pdf` 或结构级结果误当客户交付成功。正确做法是回到 final SVG 和逐裁片 `0.2mm` 证据。
- 主线程把“阶段治理已完成”误当作“客户结果已完成”。正确做法是治理层收口后立即进入 MVP 实现，并以最终 SVG 结果为唯一结束条件。
