# 粉色连衣裙 Reference 分析

本文记录 `pink-dress-simple-reference.svg` 相对于
`pink-dress-original-scan.pdf` 和叠图文件
`pink-dress-original-scan-SVG-VS-PDF.pdf` 的真实语义。重点不是描述它“像不像扫描图”，
而是确认它作为验收参考时保留了什么、丢弃了什么、如何表达尖点和曲线。

## 来源文件

- 扫描来源：`knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-original-scan.pdf`
- 简化验收参考：`knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-simple-reference.svg`
- 叠图参考：`knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-original-scan-SVG-VS-PDF.pdf`
- 派生分析输出：`examples/output/reference-analysis/`

叠图 PDF 有两个 optional content group。一个图层是扫描来源图像，另一个图层是红色
reference vector 重绘线。工具渲染时图层名容易混淆，因此后续分析应按内容识别：
scan layer 是 raster，包含手写和服装示意图；reference vector layer 只包含干净的红色纸样几何。

## Reference 结构

`pink-dress-simple-reference.svg` 不是 raw trace，而是紧凑的对象级重绘：

- 9 个闭合 `path` 对象，表示纸样裁片。
- 1 个 `rect` 对象，表示长方形条。
- 10 个 `line` 对象，表示两组短 3 cm 标尺。
- 0 个文字对象，0 个手写对象，0 个服装示意图对象。

9 个裁片 `path` 不是纯曲线，也不是纯折线，而是 curve/line 混合：

- path 内 curve segment 总数：147。
- path 内 straight line segment 总数：43。
- 小于 80 度的 sharp turn：24。
- 短直线段通常是 intentional notch、corner 或 point feature，不是 simplification noise。

## Reference 保留什么

reference 保留的是生产纸样几何：

- 每个裁片的外轮廓线。
- 边上的 intentional triangular notch。
- 短 protruding/recessed alignment mark。
- construction corner 上的 right angle 和 near-right angle。
- 长 smooth curve，并用 Bezier curve 重绘，而不是 contour polyline。
- 两组 3 cm scale marker，作为独立 `line` 对象。
- 长方形条作为 `rect`，不是 traced closed contour。

reference 在曲线邻域被圆顺时仍会保留局部 sharp feature。notch 通常表现为短直线组成的
小三角或 V 形；这些点必须在 curve fitting 之前被保护。

## Reference 丢弃什么

reference 丢弃非生产扫描内容：

- 手写标签、圈号、勾选、箭头。
- 左上角服装示意图。
- 纸张边缘、页面框线和背景纹理。
- scan wobble、灰底噪声、线宽、double-edge ink contour。
- 未附着在真实纸样几何上的偶发小噪点。

扫描中的手写内容对后续 annotation/OCR 有价值，但它不是 simple geometry acceptance target
的一部分。

## 绘制方式

reference 的绘制方式更接近人工制版重绘：

- 曲线生产边使用平滑 Bezier segment。
- 直线生产边保持直线，不被拟合成 curved spline。
- sharp construction corner 保持尖锐。
- notch 保持角状，通常是局部 V 或小三角点。
- 裁片轮廓是 single centerline-like stroke，不是 ink-outline region。
- 对象尽量按语义分型：scale 用 `line`，长方形条用 `rect`，裁片用 `path`。

因此，一个好输出可以不逐像素贴合扫描墨迹，只要它遵循设计意图中的制版曲线并保留生产特征。
pixel-perfect contour trace 是错误目标。

## 对 MVP 的影响

当前 `cleaned.svg` 仍然不够 reference-like：

- 当前输出：`20 path / 0 line / 0 rect / 0 curved path`。
- reference 输出：`9 path / 10 line / 1 rect / 9 curved path`。
- 当前评估仍只是 `debug-pass`，并且 `mvp_ready=false`。

下一步不应该继续在当前 `cleaned.svg` 上调 simplification 参数，而应该从 high-fidelity
candidate 和/或 scan raster 重建 object-level geometry：

- 在最终 geometry export 前检测并移除 handwriting、illustration、noise。
- 识别 piece-level connected outline，并合并 broken contour fragment。
- 将 ink-outline contour 转成 centerline-like pattern edge。
- 在 curve fitting 前保护 notch、right angle、short alignment mark 和 scale marker。
- 只在未保护的 curved edge region 上拟合平滑 Bezier curve。
- 当 reference 语义需要时，输出 `line` 和 `rect` 对象。

## 建议验收门槛

本 sample 的 `MVP Pass` 应至少满足：

- 对象结构接近 reference：约 9 个 pattern path、1 个 rect、10 个 scale-marker line。
- pattern path 包含 curve command，用于表达 smooth edge。
- scale marker 是独立 line object，并在校准后测得 30 mm。
- 长方形条输出为 `rect` 或等价语义矩形。
- notch 和 short alignment mark 存在，并保持角状。
- 手写、圈号、箭头、服装示意图和纸张边框不进入 simple cleaned geometry。
- curve fitting 的偏差验证应围绕 reconstructed centerline geometry，而不是 raw ink outline。

`Debug Pass` 只能表示“可作为中间候选继续处理”，不能被当作 sample acceptance。
