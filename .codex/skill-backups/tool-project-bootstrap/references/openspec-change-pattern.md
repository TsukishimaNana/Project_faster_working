# OpenSpec Change Pattern

Create three initial changes for a new tool project.

## 1. Development Roadmap

Folder:

```text
openspec/changes/<tool-name>-development-roadmap/
```

Purpose:

- Define long-term direction.
- Identify major phases.
- Separate MVP from later extensions.
- Record future output formats or integrations without forcing them into MVP.

Typical files:

- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/development-roadmap/spec.md`

## 2. Project Overview

Folder:

```text
openspec/changes/<tool-name>-overview/
```

Purpose:

- Establish project directory.
- Record project boundary.
- Record setup decisions.
- Record what was scaffolded.

This change often becomes complete soon after project setup.

## 3. First MVP Change

Folder:

```text
openspec/changes/<first-mvp-change>/
```

Purpose:

- Define the first concrete vertical slice.
- Include input/output contract.
- Include CLI contract.
- Include acceptance criteria.
- Include non-goals.

## Requirement Syntax

OpenSpec strict validation requires each requirement body to include `SHALL` or
`MUST`.

Valid mixed-language example:

```markdown
### Requirement: Project Boundary

{{PROJECT_NAME}} SHALL 位于 `tools/{{TOOL_NAME}}`，并保持为独立小工具项目。

#### Scenario: Workspace contains multiple tools

- **WHEN** 未来添加更多 tools
- **THEN** {{PROJECT_NAME}} 仍保留在自己的 tool directory 下
```

## Tasks

Use checkboxes. Mark setup tasks complete only after validation has run.

```markdown
- [x] 创建项目目录结构。
- [x] 添加 README、Handoff 和 agents。
- [x] 添加 OpenSpec project overview。
- [ ] 实现第一条 MVP vertical slice。
```
