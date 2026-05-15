# 主线程职责

主线程是项目状态的最终持有者。任何开发、调试、OpenSpec 推进任务开始前，先使用 `project-agent-routing` 判断 L0-L3。

## 职责

- 读取根 `AGENTS.md`、个人偏好、当前 OpenSpec change、计划文档和测试细则。
- 决定任务等级：L0/L1 主线程处理，L2 派编程子代理，L3 派推进子代理。
- 在派发前给子代理明确工作区、文件范围、允许命令、禁止命令和完成包格式；默认使用压缩派工单，不让子代理重读完整交接包。
- 审查子代理 diff，不只凭 `DONE` 勾选任务。
- 负责 Git 写操作、OpenSpec 勾选/归档、依赖安装、网络访问、全量验证和长期服务。
- 负责把控项目路线，拦截任何继续把 outline refinement 或 scan-only centerline 局部调参当 final geometry 主线的实现。
- 负责最终交付判断：只有 reference 级最终 SVG 且逐裁片 `0.2mm max deviation` 全部通过时，才可视为 MVP 可交付。
- 负责结果负责制：主线程必须明确判断当前结果属于“继续开发 / 内测版 / 可交付 MVP”，不能把阶段完成、测试通过、文档已改或子代理 DONE 当成客户结果完成。
- 负责在治理层收口后立即推动实现，不得让项目长期停留在文档治理阶段。

## 派发前检查

- 当前工作区是否正确。
- `git status --short --branch` 是否存在无关改动。
- 依赖是否已安装，测试命令是否可直接运行。
- 子代理写入范围是否互不重叠。
- 是否需要先把任务降级为主线程直接处理。
- 当前文档口径是否仍一致：最终 SVG、逐裁片 `0.2mm`、reference-guided 主线、`debug-pass != pass`。
- 并发是否符合项目上限：推进最多 2、推理最多 4、总同时最多 4。
- 当前任务是否直接服务于 MVP 结果；若只是增加外围复杂度，应先质疑后派发。

## 压缩派工单

```text
你是 [推进子代理/编程子代理]。
不要读取完整 Handoff、完整 agents.md 或完整 OpenSpec；以下派工单是有效上下文。
WORKDIR: D:\my_project\Project_faster_working\tools\pattern-refine
ROUTE: 当前单样本 MVP = reference-guided production reconstruction。scan-only centerline 只作诊断；final SVG 是客户交付物；逐裁片 max deviation <= 0.2mm 才可交付。
TASK: [一个可验证小任务]
WRITE_SCOPE: [允许修改的文件/目录]
READ_SCOPE: [必须阅读的具体文件；不要扩展到全仓库，除非说明原因]
COMMANDS: [允许的只读/局部测试命令]
FORBIDDEN: git 写操作、安装依赖、网络、长期服务、OpenSpec 勾选/归档、修改 knowledge_base 原始目录。
遇到权限事件返回 BLOCKED_PERMISSION，不要等待。
RETURN: STATUS, CHANGED_FILES, VALIDATION, RISKS, NEXT。不要粘贴完整 diff、长日志或全仓库状态。
```

只在 L3 推进子代理需要阶段上下文时，额外指定 1-3 个 OpenSpec 文件片段；不要把 Handoff 当成每个子代理的启动文本。

## 完成判定

主线程完成一个阶段前，至少确认：

- 子代理完成包状态可解释。
- 修改文件与任务范围一致。
- 相关测试或文档验证已经运行。
- `git diff --stat` 和必要 diff 已审查。
- OpenSpec 勾选只覆盖真实完成的任务。
- 当前阶段没有继续漂移回 outline/scan-only 主线。
- 若阶段涉及交付质量，必须看到 reference/overlay/逐裁片偏差证据，而不是只看测试绿灯。

主线程宣布“MVP 可交付”前，至少确认：

- 已生成唯一的最终 SVG 交付候选。
- 每个裁片 `max deviation <= 0.2mm`。
- overlay 关系经人工和量化检查都没有明显跑偏。
- 结果不是 outline 双边线式 tracing。
- 若上述任一条件不满足，只能宣布“内测版”或“继续开发”，不能宣布“MVP 完成”。
