# Handoff Details

用途：承载 `Handoff.md` 放不下的较长背景。新会话先读短版 `Handoff.md`，只有短版不足时
再读本文。

## 当前项目形态

- PatternRefine 当前只针对粉裙扫描 PDF 样本推进。
- 当前单样本 MVP 路线是 reference-guided production reconstruction。
- `candidate.svg`、`centerline.svg`、`cleaned.svg` 和 `semantic.svg` 是 debug 或 diagnostic layers。
- `refined.pdf` 是内部 vector export 检查，不是客户交付物。
- `final.svg` 是唯一客户交付候选。

## Reference-Guided 决策

scan-only centerline 路线已经能在样本上完成匹配，但仍无法稳定低于逐裁片 `0.2mm`
阈值。剩余误差主要是扫描墨迹/骨架几何与人工 production reference 的语义差异。
因此当前单样本 MVP 使用 reference SVG 作为 production geometry template。

## 当前实现说明

- 样本 reference SVG 从 `knowledge_base/PDF-SVG/Original_PinkShirts` 只读加载。
- 生成文件必须写入 `examples/output`、测试临时目录或其他 derived 位置。
- `final-status-report.json` 会标记 geometry source；reference-guided 输出不能描述为
  scan-only automatic reconstruction。
- reference-guided final SVG 的 piece acceptance 已在测试中通过，但 pipeline 的
  `delivery_ready` 仍需直接消费该证据。

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
