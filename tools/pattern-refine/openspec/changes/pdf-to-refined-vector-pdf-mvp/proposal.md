# Change: PDF to Refined Vector PDF MVP

## Why

第一个有用里程碑是证明：扫描型 BJD 纸样 PDF 可以被转换为更圆顺的 vector geometry，且不会破坏关键纸样特征。

## What Changes

- 将扫描 PDF 渲染为高分辨率图片。
- 从白底中提取黑色纸样线稿。
- 将提取出的线稿矢量化为内部 SVG。
- 在默认 `0.2mm` tolerance 下圆顺和简化 vector paths。
- 保留尖角、剪口、直角、三角标、短对位标和必须保持直线的边。
- 导出 refined vector PDF 作为主要输出。
- 输出 `*.cleaned.svg` 用于调试和检查。

## Out of Scope

- 完整 OCR annotation reconstruction。
- DXF/PLT export。
- Adobe Illustrator `.ai` export。
- Desktop UI。
