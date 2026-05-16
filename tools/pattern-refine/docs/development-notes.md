# 开发说明

## 项目边界

PatternRefine 是 `Project_faster_working` 工作区下的独立小工具项目。它不应吸收工作区级 agent 配置，例如 `.codex`。

## 当前样例

当前样例 PDF 位于：

```text
knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-original-scan.pdf
```

检查结果显示，这个 PDF 是由 RICOH 设备生成的扫描/image-backed PDF，不是可直接抽取路径和文字的干净矢量 PDF。
因此 MVP 必须把扫描 PDF 清理和矢量化作为一等任务处理。

## 重要产品约束

难点不是“能不能生成 SVG”，而是生成可验收、可交付的纸样生产几何，同时保留生产关键特征：

- 纸样尖角
- 剪口
- 直角
- 三角标
- 短对位标
- 必须保持直线的生产边

逐裁片 `max deviation <= 0.2mm` 只能证明输出几何接近 reference，不能证明 SVG 达到生产级。
生产级验收还必须覆盖：无重合线、无双边线、轮廓连续闭合、对象语义清晰、少点数可编辑、
曲线/直线 primitive 表达合理，以及没有把扫描墨迹轮廓当生产线。

## 格式策略

当前 MVP 路线调整为 scan-evidence + feature recognition + rule-based production tracing。
扫描 PDF 负责页面归一化、黑线证据和特征候选；`pink-dress-simple-reference.svg` 与
`pink-dress-original-scan-SVG-VS-PDF.pdf` 作为规则样本和验收 oracle，说明哪些黑线应被抽象成
红色生产线，哪些噪声应被忽略。

`*.candidate.svg`、`*.centerline.svg`、`*.cleaned.svg`、`*.semantic.svg`、`*.refined.pdf`、
overlay 和 report 都是内部证据。最终 `*.final.svg` 必须来自规则化生产几何，而不是扫描轮廓
或骨架的直接矢量化结果。

DXF 和 PLT 应作为后续 export adapters 设计，并复用同一份 final SVG / production geometry。
