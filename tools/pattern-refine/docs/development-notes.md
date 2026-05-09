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

难点不是“能不能生成 SVG”，而是生成圆顺、可用的纸样几何，同时保留生产关键特征：

- 纸样尖角
- 剪口
- 直角
- 三角标
- 短对位标
- 必须保持直线的生产边

默认几何偏差阈值为 `0.2mm`。

## 格式策略

SVG 是内部 normalized format，因为它便于检查和程序处理。MVP 交付物是 vector PDF。
DXF 和 PLT 应作为后续 export adapters 设计，并复用同一份 refined geometry。
