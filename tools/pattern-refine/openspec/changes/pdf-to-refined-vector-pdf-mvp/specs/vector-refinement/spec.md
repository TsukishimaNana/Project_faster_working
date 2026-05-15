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
- **AND** 该文件是 debug/intermediate output，而不是客户主交付物
- **AND** SVG 应趋向对象级纸样候选表达，而不是扫描噪声、文字碎片或像素级 tracing 集合

### Requirement: Final SVG Delivery

PatternRefine SHALL 输出 reference 级最终 SVG 作为当前样本 MVP 的主交付物。

#### Scenario: Sample SVG delivery is generated

- **WHEN** 当前样本的 vector reconstruction pipeline 成功达到内部验收门槛
- **THEN** 工具写出最终 SVG
- **AND** 该 SVG 应接近 `pink-dress-simple-reference.svg` 的裁片级生产几何语义
- **AND** 不得只是扫描墨迹 blob 的 outline tracing

#### Scenario: Sample SVG delivery uses reference-guided production geometry

- **WHEN** 当前样本存在用户提供的 `pink-dress-simple-reference.svg`
- **THEN** 工具 MAY 使用该 reference SVG 作为当前单样本 MVP 的 production geometry template
- **AND** 最终 SVG 的 report MUST 标明 geometry source 为 reference-guided
- **AND** 扫描 PDF 的 render、scale、orientation 和 overlay diagnostics MUST 作为验证输入保留
- **AND** 不得把该结果描述为 scan-only 自动重建

#### Scenario: Final delivery target is unique

- **WHEN** 当前样本进入交付判定
- **THEN** 最终 SVG 必须有唯一的输出目标和唯一的验收入口
- **AND** `candidate.svg`、`cleaned.svg`、`centerline.svg`、`semantic.svg`、`refined.pdf` 和其他 report 均不得被当作客户交付物替代

### Requirement: Intermediate Outputs Must Not Masquerade As Delivery

PatternRefine SHALL 将中间调试产物与最终交付物严格分离。

#### Scenario: Intermediate artifacts are present

- **WHEN** pipeline 生成 `candidate.svg`、`cleaned.svg`、`centerline.svg`、`semantic.svg`、overlay 或 `refined.pdf`
- **THEN** 这些文件只能视为内部调试、分析或验证产物
- **AND** 不得因为其中任一文件“结构接近”或“视觉上更好看”就宣称客户交付已经完成

### Requirement: Refined Vector PDF Output

PatternRefine SHALL 输出 refined vector PDF 作为内部验证和导出链路检查产物。

#### Scenario: Internal verification PDF is generated

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

### Requirement: Per-Piece SVG Acceptance

PatternRefine SHALL 以逐裁片最大偏差作为当前样本 MVP 的主验收标准。

#### Scenario: Final SVG is evaluated against the reference sample

- **WHEN** 最终 SVG 与 `pink-dress-simple-reference.svg` 做逐裁片对照
- **THEN** 每个裁片都必须满足 `max deviation <= 0.2mm`
- **AND** 不允许以整体平均值、对象数量接近或 `debug-pass` 替代该要求
- **AND** 任一裁片失败时，结果只能标记为内测版，不能视为客户可交付 MVP

#### Scenario: Piece matching fails

- **WHEN** 最终 SVG 的某个裁片无法与 reference 中对应裁片建立稳定匹配
- **THEN** 该裁片必须视为验收失败
- **AND** 不得以“其余裁片大体接近”或“整体结构接近”掩盖该失败

#### Scenario: A single piece exceeds tolerance

- **WHEN** 任一已匹配裁片的 `max deviation` 超过 `0.2mm`
- **THEN** 当前结果必须视为未通过最终交付验收
- **AND** 该结果只能标记为继续开发或内测版

### Requirement: Reference-Guided Reconstruction Is The Current Sample Geometry Path

PatternRefine SHALL 以 reference-guided production reconstruction 作为当前单样本 MVP 的最终几何路径。

#### Scenario: Reference production geometry is available

- **WHEN** 当前样本提供 `pink-dress-simple-reference.svg`
- **THEN** 工具使用该 SVG 的裁片级 path/line/rect geometry 生成最终 SVG
- **AND** 该 geometry MUST 归一化到 pipeline 的 1:1 mm 页面坐标
- **AND** 输出必须保留生产关键形状、直边、比例尺和对象层语义

#### Scenario: Scan analysis artifacts are available

- **WHEN** `candidate.svg`、`cleaned.svg`、`centerline.svg` 或 scan outline contour 已经可用
- **THEN** 它们只能作为裁片分区、局部搜索范围、比例/方向诊断或 overlay 辅助表达
- **AND** 不得被直接视为最终生产几何

#### Scenario: Reference-guided output is generated

- **WHEN** 最终 SVG 由 reference-guided production geometry 生成
- **THEN** 系统必须输出明确的 geometry source/report
- **AND** 必须继续运行逐裁片 `0.2mm` acceptance
- **AND** 必须保留扫描 PDF overlay 或诊断产物用于确认页面方向、比例和布局

### Requirement: Scan-Only Centerline Reconstruction Remains Diagnostic

PatternRefine SHALL 将 scan-only piece-wise centerline reconstruction 保留为诊断和后续泛化路线，而不是当前单样本 MVP 的最终几何 source-of-truth。

#### Scenario: Outline candidates are available

- **WHEN** `candidate.svg`、`cleaned.svg` 或 outline contour 已经可用
- **THEN** 它们只能作为裁片分区、局部搜索范围或调试表达
- **AND** 不得被直接视为最终生产几何

#### Scenario: Centerline candidate is not yet production-usable

- **WHEN** 某个裁片仍无法形成可接受的闭合中心线式轮廓
- **THEN** 系统必须明确保留失败、内测版或未完成状态
- **AND** 不得静默回退到 outline 后仍宣称当前样本已经通过 MVP 交付验收

#### Scenario: Scan-only result differs from reference production geometry

- **WHEN** scan-only centerline result 与 reference-guided production geometry 的逐裁片偏差超过 `0.2mm`
- **THEN** scan-only result MUST remain diagnostic/internal
- **AND** 当前单样本 MVP MAY still proceed with reference-guided final SVG if reference-guided acceptance passes

### Requirement: Result Classification

PatternRefine SHALL 对当前样本结果给出明确的内部状态分类。

#### Scenario: All delivery conditions are satisfied

- **WHEN** 已生成最终 SVG，且每个裁片都通过 `0.2mm` 最大偏差验收，并满足 overlay / 生产几何要求
- **THEN** 结果可标记为可交付 MVP

#### Scenario: Some delivery conditions are not satisfied

- **WHEN** 最终 SVG 尚未生成、任一裁片未通过、geometry source 未标明，或结果仍表现为 outline tracing
- **THEN** 结果必须明确标记为继续开发或内测版
- **AND** 不得向客户宣称 MVP 已完成
