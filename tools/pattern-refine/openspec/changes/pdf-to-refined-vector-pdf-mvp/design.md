# Design: PDF to Refined Vector PDF MVP

## Pipeline

1. 将每个输入 PDF 页面渲染为高分辨率 raster image。
2. 通过 grayscale conversion、thresholding、denoising 和可选 line enhancement 标准化图像。
3. 将 raster 线稿转成可分析的候选几何，但这一步只承担裁片分区、定位、诊断和 overlay 用途，不承担最终生产几何表达。
4. 读取当前样本 reference SVG，将其归一化到 pipeline 的 1:1 mm 页面坐标，作为当前单样本 MVP 的 production geometry template。
5. 使用扫描 PDF 的页面方向、比例尺和候选分区结果验证 reference-guided geometry 的页面方向、布局和比例没有错误。
6. 对 reference-guided production geometry 保留 path/line/rect、尖角、直角、短对位标、比例尺和必须保持直线的边。
7. 按逐裁片 `0.2mm` 默认 tolerance 验证最终 SVG 与 reference production geometry 的最大 geometric deviation。
8. 输出最终 SVG 作为 MVP 交付物，并保留 debug SVG / report / PDF 作为内部验证产物。

## Geometry Source Of Truth

- `pink-dress-original-scan.pdf` 是扫描观察源，用于渲染、方向、比例、布局和 overlay 验证，不是最终生产几何真相。
- `pink-dress-simple-reference.svg` 是当前单样本 MVP 的 production geometry template 和最终 SVG 的几何 source-of-truth。
- `pink-dress-original-scan-SVG-VS-PDF.pdf` 是当前样本的叠图验收参考。
- `candidate.svg`、`cleaned.svg`、outline contour 和中间骨架都只是重建过程中的辅助表达，不是最终交付物。
- 最终几何真相是 reference-guided production geometry；scan-only centerline reconstruction 当前保留为诊断和后续泛化研究路线。

## Final Output

- MVP 最终交付物是 reference 级最终 SVG。
- `refined.pdf` 保留为内部验证和导出链路检查，不是客户主交付物。
- `cleaned.svg`、`candidate.svg`、`centerline.svg`、`semantic.svg` 和 overlay/report 继续保留为调试产物。
- 当前单样本 MVP 可以使用 reference-guided geometry 生成 `final.svg`，但必须在 report 中明确该 final SVG 的 geometry source 是 reference-guided，而不是 scan-only reconstruction。

## Acceptance Baseline

- 验收对象是最终 SVG，不是中间 debug 文件。
- 主验收是逐裁片 `max deviation <= 0.2mm`。
- 质量门槛是每个裁片都过，不允许用整体平均值掩盖局部失败。
- `debug-pass`、结构接近、对象数量接近都不能视为通过。
- 合格结果必须同时满足：
  - 与 reference / overlay 的裁片级几何关系一致。
  - 保留 notch、尖角、直角、短对位标、比例尺和直边语义。
  - 不再沿扫描墨迹两侧描边，不产生双边线式 outline geometry。
  - 标明 geometry source，避免把 scan diagnostics 或 reference-guided 输出混淆为 scan-only 自动重建。

## CLI 契约

第一版命令形态：

```powershell
pattern-refine refine <input.pdf> --out <dir> --dpi 600 --scale auto
```

- 默认不覆盖已有输出；覆盖必须显式传 `--overwrite`。
- 默认输出：
  - `*-page-001-render.png`
  - `*-page-001-lines.png`
  - `*.candidate.svg`
  - `*.centerline.svg`
  - `*.cleaned.svg`
  - `*.semantic.svg`
  - `*.refined.pdf`
  - `*.deviation-report.json`
- `--scale auto` 优先使用 PDF 上的厘米尺/英寸尺校准；自动失败时报告原因。
- 后续可增加手动比例尺参数，但不能改变默认 1:1 mm 输出目标。

## PDF 导出策略

参考 SVG 主要由 path、rect、line、polygon、text 和简单 CSS class 组成，没有复杂 gradient、filter、mask、clipPath 或 embedded image。
MVP 内部 PDF 路径采用 refined geometry 直接绘制 vector PDF，而不是依赖 SVG 转 PDF。

理由：

- 更容易保证 1:1 mm 输出。
- 更容易控制 line width、page size、坐标换算和图层取舍。
- 避免 SVG 转换器对 viewBox、字体和单位的隐式处理影响供应商交付物。

SVG 转 PDF 可保留为后续对照或 fallback，不作为客户 MVP 主输出路径。

## 字体策略

MVP 线稿输出不要求中文文字层。若后续 PDF 输出包含中文文字：

- 优先使用 `assets/fonts/NotoSansSC-VF.ttf`。
- 字体已从 `C:\Windows\Fonts\NotoSansSC-VF.ttf` 复制到项目资产目录。
- 运行时引用项目内字体文件，避免依赖系统字体路径。
- PDF 输出必须显式嵌入中文字体。

## 文字识别与映射策略

扫描图中的文字不应作为普通线稿路径进入 `*.cleaned.svg` 的生产几何层。后续 Annotation Assist 应采用：

- OCR 识别文字内容和候选 bounding boxes。
- 输出结构化候选表，例如 JSON/CSV，包含原始识别文本、置信度、位置、旋转方向和关联裁片候选。
- 通过人工确认表单建立“识别文本 -> 标准输出文字/裁片字段/数量标注”的映射。
- 最终导出时从确认后的映射重建文字层，并嵌入支持中文的字体。

该能力属于 geometry MVP 之后的后续 change，不阻塞当前样本 SVG 几何质量验证。

## 依赖版本基线

MVP 阶段先记录关键依赖版本，稳定后再引入 Python lock 文件。

- PyMuPDF `1.27.2.3`
- opencv-python `4.13.0`
- numpy `2.4.4`
- Pillow `12.2.0`
- lxml `6.1.0`
- reportlab `4.5.0`
- svgwrite `1.4.3`

## 样例 Fixture 引用

当前规划 fixture 是以下扫描 PDF：

```text
knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-original-scan.pdf
```

该文件保留在只读知识库目录中，不复制到生成输出目录，也不在原目录中生成派生产物。

## 路线决策

已验证的 scan-only centerline 路线可以达到：

- `centerline_missing_reference_count = 0`
- `matched_piece_count = 10/10`
- 当前整体 max deviation 约 `2.05mm`

但剩余误差集中在扫描墨迹/骨架与人工 reference 制版几何之间的语义差异，特别是细长件局部双边回环无法自然塌缩为人工 reference 的单中心趋势。继续堆叠局部补洞、snap 和 scorer 会变成样本特化调参，不能可靠达到逐裁片 `0.2mm`。

因此当前单样本 MVP 改为 reference-guided production reconstruction：

```text
scan PDF -> render / scale / orientation / diagnostic overlay
reference SVG -> production geometry template -> final.svg
final.svg + scan overlay + reference acceptance -> delivery decision
```

scan-only centerline reconstruction 不删除，但降级为：

- 分区和候选诊断
- overlay 风险定位
- 后续多样本泛化研究路线
- 验证 reference-guided 输出没有明显页面方向、比例或布局错误的辅助证据

## 关键风险

- 继续沿 outline refinement 或 scan-only centerline 局部调参路线叠加复杂度，而不是转到 reference-guided production reconstruction。
- 在已经确认 scan-only 路线无法稳定达到当前单样本 `0.2mm` 后，继续堆叠局部补丁，而不是切换到 reference-guided MVP。
- 用结构接近、`debug-pass` 或中间 SVG 质量替代最终逐裁片验收。
- 在 scale source-of-truth 未决定前静默修改 geometry/export 尺寸。
- 过度圆顺 notch、尖角、直角、短对位标和必须保持直的生产边。

## 实现倾向

优先使用确定性的 geometry rules 和可复现参数，围绕单样本 reference-guided production geometry 和逐裁片验收推进，而不是继续强化 outline tracing 或 scan-only centerline 局部调参。
Illustrator 可以作为 review tool，但不是 MVP pipeline 的一部分。
