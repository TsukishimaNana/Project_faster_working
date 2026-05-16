# Handoff

用途：让新会话快速接手 PatternRefine。本文保持短版；较长背景放在
`docs/handoff-details.md`，当前批次上下文放在 `CURRENT_SLICE.md`。

## 接手 Prompt

```text
请在 `D:\my_project\Project_faster_working\tools\pattern-refine` 中工作。
先读 `CURRENT_SLICE.md` 和 `agents.md`；只有本轮任务需要历史状态时再读 `Handoff.md`。
只有要汇报交付验收或修改验收逻辑时再读 `docs/acceptance-contract.md`。
不要默认读取完整 OpenSpec、长版规则、历史 delivery closure 文档，或长 Python 文件全文。
读代码前先读 `docs/code-map.md`，再按目标函数读取局部窗口。
先汇报路由等级、当前路线、最小任务批次和主要风险。
只做 `CURRENT_SLICE.md` 的本轮任务；文档-only 任务不要运行交付验收。
子代理只使用压缩派工单，不 fork 完整对话上下文。
```

## 默认上下文

1. 本轮任务切片：`CURRENT_SLICE.md`
2. 永久硬规则：`agents.md`
3. 代码定位地图：`docs\code-map.md`，仅在需要读代码时读取

只有短版信息不够时，再读：

- 当前接手状态：`Handoff.md`
- 固定验收契约：`docs\acceptance-contract.md`
- 长版背景：`docs\handoff-details.md`
- 长版规则：`agent_docs\rules-detail.md`
- 当前 OpenSpec：`openspec\changes\pdf-to-refined-vector-pdf-mvp\tasks.md`

## 当前状态

- 当前样本 MVP 路线已调整为：scan evidence + feature recognition + rule-based production tracing。
- 旧的 reference-guided `final.svg` 能通过逐裁片几何偏差，但用户已判定它不足以代表生产级 SVG。
- `max_deviation <= 0.2mm`、piece acceptance 和 `delivery_ready=true` 只能作为几何接近证据，
  不再足以报告生产级 PASS。
- 新路线必须先从 `pink-dress-original-scan.pdf` 建立页面归一化和扫描证据层，再识别裁片、
  直边、曲边、尖角、剪口、短对位标、比例尺和非生产噪声，最后按制版规则生成干净 SVG。
- `pink-dress-simple-reference.svg` 和 `pink-dress-original-scan-SVG-VS-PDF.pdf` 是当前样本的
  reference/oracle，用于理解红色生产线如何从扫描黑线抽象出来；不要把它们描述成自动输出已达标。
- `candidate.svg`、`centerline.svg`、`cleaned.svg`、`semantic.svg`、`refined.pdf` 和 overlay/report
  仍都是内部证据。
- 当前 `pink-dress-simple-reference.svg` 的工作区改动已由用户确认保留；不要擅自回滚。

## 最近验证

- `.\.venv\Scripts\python.exe -m pytest -q` -> 最近已知 `91 passed`
- `.\.venv\Scripts\python.exe -m ruff check .` -> passed
- `npm run spec:validate` -> 3 changes passed

如果 Windows Temp 权限异常：

```powershell
New-Item -ItemType Directory -Force .pytest-tmp | Out-Null
$env:TEMP = (Resolve-Path .pytest-tmp).Path
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

## 下一步

执行 `CURRENT_SLICE.md` 指向的新方向文档/实现切片。旧 delivery closure task packets 已完成但
验收口径过窄，不能继续作为生产级完成标准。

## 上下文控制

- 用 `.\.venv\Scripts\python.exe scripts\context_snapshot.py` 查看短摘要。
- 不要默认全仓库 broad search。
- 不要默认全文读取 `src/pattern_refine/pipeline.py`、`src/pattern_refine/evaluate.py`、
  `src/pattern_refine/semantic.py`；先读 `docs/code-map.md`，再查目标函数局部窗口。
- 生成物不要进入 Git。
