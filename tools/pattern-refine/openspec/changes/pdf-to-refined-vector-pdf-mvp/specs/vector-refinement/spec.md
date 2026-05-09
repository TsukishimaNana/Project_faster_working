# Vector Refinement MVP Specification

## ADDED Requirements

### Requirement: Scanned PDF Input

PatternRefine SHALL 支持扫描型 image-backed BJD pattern PDFs 作为 MVP input。

#### Scenario: Image-backed PDF is processed

- **WHEN** 输入 PDF 包含嵌入的 scanned page image
- **THEN** 工具将页面渲染为 high-resolution image
- **AND** 使用渲染图像作为 line extraction 的来源

### Requirement: Cleaned SVG Debug Output

PatternRefine SHALL 为每个处理成功的 PDF 输出 cleaned SVG debug output。

#### Scenario: MVP processing succeeds

- **WHEN** 扫描 PDF 处理成功
- **THEN** 工具写出 `*.cleaned.svg` 文件
- **AND** SVG 包含用于 PDF export 的 refined vector geometry
- **AND** SVG 应趋向对象级纸样轮廓表达，而不是扫描噪声、文字碎片或像素级 tracing 集合

### Requirement: Refined Vector PDF Output

PatternRefine SHALL 输出 refined vector PDF 作为 MVP 主要交付物。

#### Scenario: Supplier output is generated

- **WHEN** vector refinement pipeline 成功
- **THEN** 工具写出 `*.refined.pdf` 文件
- **AND** 输出必须是 vector-based，而不是 flattened raster image

### Requirement: Feature Preservation

PatternRefine SHALL 在 smoothing 过程中保留 production-critical pattern features。

#### Scenario: Critical features are detected

- **WHEN** path 包含 sharp corners、notches、right angles、triangle marks、short alignment marks 或 straight production edges
- **THEN** 这些特征必须被保护，不能被 smoothing 圆化、删除或明显位移

### Requirement: Smoothing Tolerance

PatternRefine SHALL 使用 `0.2mm` 作为 path smoothing 的默认 maximum geometric deviation。

#### Scenario: Proposed smoothing exceeds tolerance

- **WHEN** smoothed path segment 相对 source geometry 偏差超过 `0.2mm`
- **THEN** 该 smoothing 必须被拒绝，或用更保守的 settings 重试
