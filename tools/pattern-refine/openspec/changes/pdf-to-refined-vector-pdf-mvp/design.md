# Design: PDF to Refined Vector PDF MVP

## Pipeline

1. 将每个输入 PDF 页面渲染为高分辨率 raster image。
2. 通过 grayscale conversion、thresholding、denoising 和可选 line enhancement 标准化图像。
3. MVP 的 `*.cleaned.svg` 应表达对象级纸样轮廓，而不是像素级 tracing。第一步应过滤文字、扫描噪声和碎线，只输出主裁片轮廓候选；后续再做 feature classification、圆顺和偏差验证。
4. 将 path features 分类为 smooth curves、straight segments、corners、notches、right angles、triangle marks 和 short alignment marks。
5. 只对符合条件的 curve regions 做圆顺。
6. 按 `0.2mm` 默认 tolerance 验证最大 geometric deviation。
7. 将 refined geometry 导出为 vector PDF 和 debug SVG。

## Cleaned SVG 质量参考

`knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-simple-reference.svg` 是当前只读验收参考。它的表达特点是：

- 少量对象级 geometry：主要裁片用少数 path/rect/line 表达。
- 不包含扫描噪声、文字碎片和像素级短线。
- 输出应能被后续算法继续处理，而不是需要人工从上千个碎 path 中重建。

因此 `pink-dress-original-scan.cleaned.svg` 的阶段性验收目标是接近 `pink-dress-simple-reference.svg` 的对象粒度和可读性；它可以先是候选轮廓，但不能退化为不可辨认的像素碎片集合。

## CLI 契约

第一版命令形态：

```powershell
pattern-refine refine <input.pdf> --out <dir> --dpi 600 --scale auto
```

- 默认不覆盖已有输出；覆盖必须显式传 `--overwrite`。
- 默认输出：
  - `*-page-001-render.png`
  - `*-page-001-lines.png`
  - `*.cleaned.svg`
  - `*.refined.pdf`
  - `*.deviation-report.json`
- `--scale auto` 优先使用 PDF 上的厘米尺/英寸尺校准；自动失败时报告原因。
- 后续可增加手动比例尺参数，但不能改变默认 1:1 mm 输出目标。

## PDF 导出策略

参考 SVG 主要由 path、rect、line、polygon、text 和简单 CSS class 组成，没有复杂 gradient、filter、mask、clipPath 或 embedded image。
MVP 主路径采用 refined geometry 直接绘制 vector PDF，而不是依赖 SVG 转 PDF。

理由：

- 更容易保证 1:1 mm 输出。
- 更容易控制 line width、page size、坐标换算和图层取舍。
- 避免 SVG 转换器对 viewBox、字体和单位的隐式处理影响供应商交付物。

SVG 转 PDF 可保留为后续对照或 fallback，不作为 MVP 主输出路径。

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

该能力属于 geometry MVP 之后的后续 change，不阻塞当前线稿清理和 vector PDF 几何质量验证。

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

## 关键风险

主要风险是过度圆顺生产关键纸样特征。输出可信前，必须有 feature protection 和 deviation checks。

## 实现倾向

优先使用确定性的 geometry rules 和可复现参数，而不是手工 Illustrator cleanup。
Illustrator 可以作为 review tool，但不是 MVP pipeline 的一部分。
