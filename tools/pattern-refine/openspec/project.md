# PatternRefine OpenSpec Project

## 目标

PatternRefine 通过将扫描型纸样 PDF 转换为更干净的矢量输出，加速 BJD 纸样准备流程。
工具目标是减少 Illustrator 清理工作，而不是取代最终人工复核。

## MVP 优先级

1. 清理并矢量化扫描 PDF 中的纸样线稿。
2. 在保留生产关键特征的前提下圆顺路径。
3. 导出供应商可用的 vector PDF。
4. 输出 SVG 用于调试和内部处理。

## MVP 非目标

- Desktop UI。
- Adobe Illustrator `.ai` export。
- DXF 或 PLT export。
- 完整 OCR-driven text annotation reconstruction。
- Illustrator image trace automation。

## 开发规则

- `.codex` 保持在父工作区层级。
- SVG 只作为中间格式，不作为最终产品。
- 圆顺结果必须按 `0.2mm` 默认偏差阈值验证。
- 优先使用确定性处理流程，不依赖手工 Illustrator 步骤。
