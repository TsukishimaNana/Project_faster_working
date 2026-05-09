# Development Roadmap Specification

## ADDED Requirements

### Requirement: Roadmap Sequencing

PatternRefine SHALL 先证明 geometry quality，再实现 laser-specific exports 和 annotation reconstruction。

#### Scenario: Planning future work

- **WHEN** 提出一个新 feature
- **THEN** 它需要被归类为 foundation、geometry MVP、geometry quality、production export、annotation assist 或 workflow polish
- **AND** 依赖 refined geometry 的工作必须排在 geometry MVP 之后

### Requirement: Export Adapter Direction

PatternRefine SHALL 将后续 export formats 设计为 refined geometry model 的 adapters。

#### Scenario: Adding a new export format

- **WHEN** 增加 DXF、PLT 或其他 vector export
- **THEN** 它必须消费 vector PDF export 使用的同一份 refined geometry
- **AND** 不应重新运行独立 tracing 或 smoothing logic

### Requirement: OCR as Later Capability

PatternRefine SHALL 将 OCR-based text 和 arrow reconstruction 视为第一版 geometry MVP 之后的后续能力。

#### Scenario: Geometry MVP is implemented

- **WHEN** 第一版 MVP 定义 scope
- **THEN** OCR annotation reconstruction 不作为验收必需项
- **AND** line cleanup、feature preservation 和 vector PDF export 仍是验收重点
