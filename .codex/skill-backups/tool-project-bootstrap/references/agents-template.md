# agents.md Template

Use this as the project-level `agents.md`. Keep it near 150-250 lines.

```markdown
# {{PROJECT_NAME}} Agent Instructions

本文件是 {{PROJECT_NAME}} 项目专用规则。也需要遵守个人全局配置：

```text
{{PERSONAL_AGENTS_PATH}}
```

如果规则冲突，本文件优先约束 {{PROJECT_NAME}} 的项目安全和 source-of-truth；个人配置优先约束沟通偏好。

## 项目目标

{{PROJECT_PURPOSE}}

## 当前技术栈

- {{STACK_ITEM_1}}
- {{STACK_ITEM_2}}
- {{STACK_ITEM_3}}

## 项目目录结构

```text
{{TOOL_DIR}}\
  Handoff.md
  agents.md
  README.md
  src\
  tests\
  openspec\
  docs\
  examples\input\
  examples\output\
  knowledge_base\
  assets\
```

## 输出和生成物规则

- 原始/参考目录只读；任何派生文件都不能写进去。
- MVP 默认输出目录优先使用 `examples\output\`。
- 后续如生成较多分析材料，可新增 `knowledge_base\derived\...`，但必须与 `Original_*` 原始目录分离。
- 默认不覆盖旧输出；需要覆盖时必须由 CLI 参数或明确任务说明触发。

## 单位和格式约定

- 程序内部单位：{{INTERNAL_UNIT}}。
- 主要输出格式：{{PRIMARY_OUTPUT}}。
- 调试/中间格式：{{DEBUG_OUTPUTS}}。
- 必须记录所有单位换算和坐标系约定。

## 几何/数据/验证规则

- 输出必须能解释为真实业务数据，不要混入调试层。
- 主数据、辅助数据、调试数据、最终交付数据必须分离。
- 数据不合法时应失败并给出原因，不要静默输出空文件或残缺文件。
- 关键结果不能只靠肉眼判断；应有可复现验证或报告。

## 文本文件规范

- 项目文本文件统一 UTF-8（无 BOM）+ LF。
- 新建或重写中文文档、JSON、SVG、脚本文件时，先确认写入编码。
- 中文相关问题的修复结论应有证据：真实文件编码、读取方式、终端显示方式和修改后验证结果。

## MVP 工作前必读

- `Handoff.md`
- `README.md`
- `docs/{{IMPORTANT_DOC}}`
- `openspec/project.md`
- `openspec/changes/{{ROADMAP_CHANGE}}/proposal.md`
- `openspec/changes/{{MVP_CHANGE}}/proposal.md`
- `openspec/changes/{{MVP_CHANGE}}/design.md`
- `openspec/changes/{{MVP_CHANGE}}/tasks.md`

## 原始知识库只读

以下目录包含用户提供的原始/参考文件：

```text
{{READONLY_SOURCE_DIRS}}
```

规则：

- 不要编辑此目录内的文件内容。
- 不要覆盖此目录内的文件。
- 不要把文件移出此目录。
- 不要把派生产物生成到此目录。
- 如果需要处理参考文件，只读读取它，并将生成产物写入 `examples\output\` 或命名清晰的 derived 目录。

## 中文编码和终端安全

- 不要把终端 mojibake 直接判定为文件损坏。
- 重写疑似乱码文件前，先验证源文件 bytes，或用显式 UTF-8 方式读取。
- PowerShell 处理中文路径时，优先使用 `-LiteralPath` 或 `Get-ChildItem` 返回的对象路径。
- 不要手敲乱码中文路径后继续覆盖写入。
- 不要把终端渲染出来的中文文本当成唯一 source-of-truth。

## 红线

- 不要移动或复制工作区 `.codex` 到工具项目内。
- 不要把生成物写进原始目录。
- 不要在未更新 OpenSpec 的情况下扩大 MVP 范围。
- 不要把调试产物当作最终交付物。
- 不要静默忽略失败。

## 开发命令

从 `{{TOOL_DIR}}` 运行：

```powershell
{{VALIDATION_COMMANDS}}
```

## MVP CLI 契约

```powershell
{{CLI_CONTRACT}}
```

- CLI 参数变更会影响测试、Handoff、OpenSpec 和用户使用文档，必须同步更新。

## MVP 依赖版本记录

{{DEPENDENCY_VERSION_RECORD}}

## 实现边界

- MVP 工作必须对齐 OpenSpec tasks。
- 范围发生实质变化时，新增或更新 OpenSpec。
- 生成输出不要写进 source/reference folders。
- {{PROJECT_SPECIFIC_BOUNDARY}}
```
