# PatternRefine OpenSpec Project

## 目标

PatternRefine 通过将扫描型纸样 PDF 和人工 reference SVG 组合成可验证的最终 SVG 生产几何，
加速 BJD 纸样准备流程。
工具目标是减少 Illustrator 清理工作，而不是取代最终人工复核。

## MVP 优先级

1. 针对当前粉裙样本输出 reference-guided `*.final.svg`。
2. 用逐裁片 `max deviation <= 0.2mm` 作为主验收门。
3. 保留扫描 PDF 的 render、scale、orientation 和 overlay 诊断链路。
4. 将 `candidate.svg`、`centerline.svg`、`cleaned.svg`、`semantic.svg` 和 `refined.pdf` 保持为内部验证产物。

## MVP 非目标

- Desktop UI。
- Adobe Illustrator `.ai` export。
- DXF 或 PLT export。
- 完整 OCR-driven text annotation reconstruction。
- Illustrator image trace automation。

## 开发规则

- `.codex` 保持在父工作区层级。
- 当前 MVP 的客户主交付物是最终 SVG。
- `refined.pdf` 只作为内部 vector export 检查，不是客户主交付物。
- 最终 SVG 必须按逐裁片 `0.2mm` 默认偏差阈值验证。
- 优先使用确定性处理流程，不依赖手工 Illustrator 步骤。
