# Change: PatternRefine Development Roadmap

## Why

在实现具体 MVP changes 前，PatternRefine 需要一个总体开发方向。这个项目不只是 PDF-to-SVG converter：
它的目标是减少 BJD 纸样清理工作，并产出供应商可用的矢量交付物。

## What Changes

- 定义从扫描 PDF 输入到 refined vector outputs 的长期处理 pipeline。
- 确立 SVG 作为内部 normalized geometry format。
- 将 refined vector PDF 作为第一个可用输出。
- 在 geometry quality 被证明后，再推进 DXF 和 PLT export。
- Illustrator 和 `.ai` export 不进入 MVP。
- OCR 和 annotation reconstruction 作为后续能力跟踪，不阻塞线条质量验证。

## Roadmap

1. **Foundation**：项目结构、OpenSpec、Python 环境、样例 fixtures 和验证命令。
2. **MVP V1**：扫描 PDF 到 cleaned SVG 和 refined vector PDF。
3. **Geometry Quality**：改进圆顺、特征保护、偏差报告和视觉对比工具。
4. **Production Export**：基于 refined geometry model 增加 DXF 和 PLT exporters。
5. **Annotation Assist**：增加 OCR-based text/arrow extraction，并提供配置兜底。
6. **Workflow Polish**：批处理、review reports 和可选 Illustrator handoff helpers。

## Impact

这个 roadmap change 为后续 OpenSpec changes 提供共同方向，并明确哪些能力是前置条件，哪些属于后续扩展。
