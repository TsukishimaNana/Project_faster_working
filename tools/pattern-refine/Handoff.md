# Handoff

用途：让新会话快速接手 PatternRefine。本文保持短版；较长背景放在
`docs/handoff-details.md`，当前批次上下文放在 `CURRENT_SLICE.md`。

## 接手 Prompt

```text
请在 `D:\my_project\Project_faster_working\tools\pattern-refine` 中工作。
修改文件前先读 `Handoff.md`、`CURRENT_SLICE.md`、`agents.md` 和当前 active OpenSpec tasks。
先汇报路由等级、当前 OpenSpec 阶段、最小任务批次、主要风险，以及是否仍在 reference-guided 路线上。
子代理只使用压缩派工单，不 fork 完整对话上下文。
```

## 最小阅读集

1. `CURRENT_SLICE.md`
2. `agents.md`
3. `openspec\changes\pdf-to-refined-vector-pdf-mvp\tasks.md`
4. `openspec\changes\pdf-to-refined-vector-pdf-mvp\design.md`

只有短版信息不够时，再读 `docs\handoff-details.md`。

## 当前状态

- 当前样本 MVP 路线：reference-guided production reconstruction。
- 客户交付物是 `*.final.svg`；PDF、debug SVG 和 report 都是内部证据。
- `pink-dress-simple-reference.svg` 只读加载为 production geometry template。
- `refine_pdf()` 已为 `pink-dress-original-scan.pdf` 输出 reference-guided `final.svg`。
- final status report 已包含 `geometry_source=reference-guided`。
- scan-only centerline 只保留为诊断层；最新已知 scan-only max deviation 约 `2.05mm`。
- reference-guided final SVG 在测试中的逐裁片验收已通过，max deviation 约 `0.122mm`。
- pipeline 的 `delivery_ready` 仍需直接消费 piece acceptance 证据后，才能声明 MVP 可交付。

## 最近验证

- `.\.venv\Scripts\python.exe -m pytest -q` -> `88 passed`
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

1. 将 final SVG piece acceptance 接入 pipeline final-status/report。
2. 保持 scan render、scale marker、orientation 和 overlay diagnostics 不断链。
3. 增加 scan-only 与 reference-guided 的差异报告。
4. 只有 final-status/report 与逐裁片 `0.2mm` 证据一致时，才标记可交付 MVP。

## 上下文控制

- 用 `.\.venv\Scripts\python.exe scripts\context_snapshot.py` 查看短摘要。
- 不要默认全仓库 broad search。
- 生成物不要进入 Git。
