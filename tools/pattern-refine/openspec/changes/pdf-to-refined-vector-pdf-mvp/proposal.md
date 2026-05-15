# Change: PDF to Refined Vector PDF MVP

## Why

第一个有用里程碑是证明：扫描型 BJD 纸样 PDF 可以进入一条可验证的生产几何重建链路，并输出当前样本的 reference 级最终 SVG。

实现复盘显示，scan-only centerline reconstruction 能把裁片匹配推进到 `10/10`，但剩余误差主要来自扫描墨迹/骨架与人工制版 reference 之间的语义差异，而不是缺段、方向或比例问题。继续局部补洞和 snap 会越来越像扫描墨迹，不能稳定保证逐裁片 `0.2mm`。因此当前单样本 MVP 改为 reference-guided production reconstruction：使用用户提供的 `pink-dress-simple-reference.svg` 作为当前样本的生产几何模板，扫描 PDF 负责方向、比例、布局、overlay 和诊断验证。

## What Changes

- 将扫描 PDF 渲染为高分辨率图片。
- 从白底中提取黑色纸样线稿。
- 将提取出的线稿矢量化为内部 SVG，用作分区、定位、诊断和 overlay，不作为最终生产几何真相。
- 读取当前样本 reference SVG，归一化为 pipeline 的 1:1 mm 坐标，生成唯一 `final.svg` 交付候选。
- 以扫描 PDF 的页面方向、比例尺和 overlay 结果验证 reference-guided 输出没有坐标、比例或页面方向错误。
- 保留尖角、剪口、直角、三角标、短对位标和必须保持直线的边；这些生产语义以 reference production geometry 为准。
- 导出 refined vector PDF 作为内部验证和导出链路检查产物。
- 输出 `*.cleaned.svg` 用于调试和检查。

## Out of Scope

- 完整 OCR annotation reconstruction。
- DXF/PLT export。
- Adobe Illustrator `.ai` export。
- Desktop UI。
