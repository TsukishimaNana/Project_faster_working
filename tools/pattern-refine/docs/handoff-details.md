# Handoff Details

用途：承载 `Handoff.md` 放不下的较长背景。新会话先读短版 `Handoff.md`，只有短版不足时
再读本文。

## 当前项目形态

- PatternRefine 当前只针对粉裙扫描 PDF 样本推进。
- 当前单样本 MVP 路线已调整为 scan-evidence + feature recognition + rule-based production tracing。
- `candidate.svg`、`centerline.svg`、`cleaned.svg` 和 `semantic.svg` 是 debug 或 diagnostic layers。
- `refined.pdf` 是内部 vector export 检查，不是客户交付物。
- `final.svg` 只有在通过几何接近和 production cleanliness/topology gate 后才是客户交付候选。

## 方向修正

旧实现里，reference-guided final SVG 可以通过逐裁片 `0.2mm` 偏差验收，但用户确认它仍不能代表
生产级 SVG：生产级 SVG 应像 `pink-dress-simple-reference.svg` 一样干净、少重合线、语义清晰、
可编辑。结论是：piece acceptance 是必要但不充分的几何 gate，不能单独驱动生产级 PASS。

新路线应先从 `pink-dress-original-scan.pdf` 得到页面归一化扫描证据层，再识别制版特征：
裁片、直边、曲边、尖角、剪口、短对位标、比例尺和非生产噪声。最终 SVG 应由规则化 primitive
graph 生成，而不是由扫描黑线轮廓或 skeleton 直接导出。

`pink-dress-simple-reference.svg` 和 `pink-dress-original-scan-SVG-VS-PDF.pdf` 是当前样本的
reference/oracle：前者展示干净生产 SVG 的目标结构，后者展示红色生产线与扫描黑线的关系。

## 当前实现说明

- 样本 reference/oracle 从 `knowledge_base/PDF-SVG/Original_PinkShirts` 只读加载。
- 生成文件必须写入 `examples/output`、测试临时目录或其他 derived 位置。
- `final-status-report.json` 必须标记 geometry source；scan evidence、centerline、semantic 或
  reference-guided 几何接近结果不能自动描述为生产级交付。
- 后续需要新增 production cleanliness/topology gate，并让 `delivery_ready/result_state` 同时消费
  piece acceptance 和该 gate 的证据。
- 当前 `pink-dress-simple-reference.svg` 的工作区改动已由用户确认保留；后续任务不得擅自回滚。

## 上下文控制

- 下一批窄任务优先读 `CURRENT_SLICE.md`。
- 用 `scripts/context_snapshot.py` 输出短状态摘要。
- 避免对 `src tests` 做 broad `rg`；优先搜索具体函数名、字段名或文件名。
- 调试 pytest 时使用仓库内 temp 和短 traceback：

```powershell
$env:TEMP = (Resolve-Path .pytest-tmp).Path
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```
