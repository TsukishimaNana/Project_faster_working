# Handoff Template

Use this as `Handoff.md`. Replace placeholders and keep it concise.

```markdown
# Handoff

用途：让新会话在 30 秒内接手 {{PROJECT_NAME}}。保持精简；详细决策放在 OpenSpec。

## 接手 Prompt

```text
请在 `{{TOOL_DIR}}` 中工作。
先阅读 `Handoff.md`、`agents.md` 和当前 active OpenSpec changes，再做修改。
先汇报当前状态和风险，然后继续推进 MVP。
```

## 当前工作区

- 路径：`{{TOOL_DIR}}`
- 项目：{{PROJECT_NAME}}
- 目标：{{MVP_GOAL}}
- MVP 主要交付物：`{{PRIMARY_OUTPUT}}`
- 调试/中间输出：{{DEBUG_OUTPUTS}}
- 不进入 MVP：{{NON_GOALS}}

## 当前状态

- {{CURRENT_STATE_1}}
- {{CURRENT_STATE_2}}
- OpenSpec 当前 changes：
  - `{{ROADMAP_CHANGE}}`
  - `{{OVERVIEW_CHANGE}}`
  - `{{MVP_CHANGE}}`

## 必读文件

- `agents.md`
- `README.md`
- `docs/{{IMPORTANT_DOC}}`
- `openspec/project.md`
- `openspec/changes/{{ROADMAP_CHANGE}}/proposal.md`
- `openspec/changes/{{MVP_CHANGE}}/proposal.md`
- `openspec/changes/{{MVP_CHANGE}}/design.md`
- `openspec/changes/{{MVP_CHANGE}}/tasks.md`

## 原始/参考文件

只读目录：

```text
{{READONLY_SOURCE_DIRS}}
```

规则：不要修改、覆盖、移动原始文件；不要把生成物写入原始目录。

## 最近验证命令

从 `{{TOOL_DIR}}` 运行：

```powershell
{{VALIDATION_COMMANDS}}
```

最近已知结果：{{LAST_VALIDATION_RESULT}}

## 下一步 MVP

{{NEXT_STEP}}

## 风险

- {{RISK_1}}
- {{RISK_2}}

## 更新规则

- 保持精简。
- 每个重要里程碑后更新当前状态、最近验证、风险和下一步。
- 不贴长命令输出。
```
