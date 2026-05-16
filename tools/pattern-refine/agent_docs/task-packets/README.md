# Task Packets

本目录保存可直接下发给主线程或子代理的压缩任务包。每个任务包都应能独立阅读和执行，
避免把完整 Handoff、完整 OpenSpec、完整长版规则塞进上下文。

使用方式：

```text
请在 D:\my_project\Project_faster_working\tools\pattern-refine 工作。
按 agent_docs/task-packets/<task>.md 执行。
不要读取完整长版规则；需要项目硬规则时读 agents.md，需要验收口径时读 docs/acceptance-contract.md。
```

任务包约定：

- `ROUTE` 固定当前 MVP 主线。
- `READ_SCOPE` 只列必读文件。
- `WRITE_SCOPE` 明确允许修改的文件。
- `FORBIDDEN` 明确不能碰的目录和行为。
- `VALIDATION` 是本任务最低验收，不等于完整 MVP 完成。
- `RETURN` 使用固定状态包，方便用户只看结果。
