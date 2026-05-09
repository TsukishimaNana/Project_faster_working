# PatternRefine Project Specification

## ADDED Requirements

### Requirement: Project Boundary

PatternRefine SHALL 位于 `Project_faster_working` 工作区内的 `tools/pattern-refine`。

#### Scenario: Workspace contains multiple tools

- **WHEN** 未来添加更多 work-acceleration tools
- **THEN** PatternRefine 仍保持在自己的 tool directory 下
- **AND** shared workspace-level agent configuration 仍保留在工具目录外

### Requirement: Format Positioning

PatternRefine SHALL 将 SVG 视为 internal/debugging format。

#### Scenario: MVP output is generated

- **WHEN** MVP 处理 scanned pattern PDF
- **THEN** 工具输出 debug SVG
- **AND** primary deliverable 是 refined vector PDF

### Requirement: MVP Non-Goals

PatternRefine MVP SHALL NOT 要求 Illustrator `.ai`、DXF、PLT、desktop UI 或完整 OCR annotation reconstruction。

#### Scenario: MVP scope is reviewed

- **WHEN** 选择 implementation tasks
- **THEN** MVP non-goals 之外的工作必须推迟到 later changes
