# Design: Development Roadmap

## 架构方向

PatternRefine 应实现为带明确中间产物的 pipeline：

1. PDF page render。
2. Cleaned raster line image。
3. Initial vector trace。
4. Normalized SVG/path geometry。
5. 带 protected features 的 refined geometry。
6. Export adapters。

geometry model 应位于 export formats 之前，使 vector PDF、DXF 和 PLT 最终都能复用同一份 refined source。

## 里程碑边界

第一个实现里程碑应先验证 line cleanup 和 vector PDF export，再增加 annotation reconstruction 或 laser-specific formats。

OCR 有价值，但不应阻塞 geometry MVP；最高风险问题是圆顺线条时不能破坏纸样关键特征。

## 工具方向

OpenSpec 负责 roadmap、MVP 和后续 feature changes。Python 负责 processing pipeline。
Skills 是开发辅助，不是 runtime dependencies。
