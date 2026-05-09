# Change: Establish PatternRefine Project

## Why

父工作区需要一个专门的小工具项目来处理 BJD 纸样清理。当前手工 Illustrator 流程可以产出可用的 SVG/PDF，
但图像描摹和清理仍需要反复人工修正。

## What Changes

- 创建 `tools/pattern-refine` 作为工具项目目录。
- 将 PatternRefine 定义为 PDF-to-refined-vector-output pipeline。
- 将 SVG 定位为 internal/debug format。
- 将 vector PDF 作为第一个 MVP deliverable。
- 记录未来 DXF/PLT export，但不放入 MVP。

## Impact

这为 specs、tasks、Python code、fixtures 和 generated examples 建立稳定项目边界，同时不移动工作区级 agent 配置。
