# Current Slice

用途：每轮可覆盖的最小接手面。新会话默认只读本文件和 `agents.md`；历史状态不足时再读
`Handoff.md`；需要读代码时先读 `docs/code-map.md`。

## Next Session Snapshot

ROUTE:
scan evidence + feature recognition + rule-based production tracing

CURRENT_PHASE:
方案 B 第一阶段 production cleanliness/topology gate 已接入；下一步进入 gate 规则细化或
feature recognition / rule-based production tracing 的最小实现任务。

DONE_THIS_ROUND:
- 已新增 `src/pattern_refine/production_quality.py`，写出
  `*.production-quality-report.json`。
- `refine_pdf()` 已写出 production-quality report，并把 production gate blocker 合入
  final status 的 `delivery_ready`。
- `verify-delivery` 已要求 `--production-quality-report`；piece acceptance 通过但 production gate
  未过时仍 FAIL。
- 当前 `examples/output/pink-dress-original-scan.final.svg` 的 production-quality CLI 结果为
  `accepted=false`，blockers 包含 `jagged_polyline_detected` 和
  `manual_production_review_required`。

NEXT_TASK:
在不改交付口径的前提下，选择一个小任务继续推进：要么细化 production gate 的重线/断点定位摘要，
要么开始 feature recognition / rule-based production tracing 的最小 primitive graph 任务。不要把
当前 reference-guided final 描述成生产级交付。

READ_FIRST:
- `CURRENT_SLICE.md`
- `agents.md`

READ_ONLY_IF_NEEDED:
- `Handoff.md`：历史状态或最近验证不足时。
- `docs/acceptance-contract.md`：交付验收或验收逻辑变更时。
- `docs/code-map.md`：读取 Python 代码前。
- `docs/production-reconstruction-direction.md`：开始下一任务前读取。
- 当前 OpenSpec tasks：需要正式任务状态时。

DO_NOT_READ_FULL:
- `src/pattern_refine/pipeline.py`
- `src/pattern_refine/evaluate.py`
- `src/pattern_refine/semantic.py`

DO_NOT_REPEAT:
- 不要把 piece acceptance、`delivery_ready=true` 或 `max_deviation <= 0.2mm` 当作生产级 PASS。
- 不要继续把旧 delivery closure 当成已经解决生产级 SVG 质量。
- 不要把 `pink-dress-simple-reference.svg` 当 fallback final template；它在方案 B 中是 oracle/reference。
- 不要写入、移动或覆盖 `knowledge_base/PDF-SVG/Original_PinkShirts`。

## 执行边界

- 只围绕方案 B 方向修正和生产级 SVG 验收口径推进。
- 不做 DXF/PLT、OCR、UI 或多样本泛化。
- 不写入、不移动、不覆盖 `knowledge_base/PDF-SVG/Original_PinkShirts`。
- 不回滚用户确认保留的 `pink-dress-simple-reference.svg` 工作区改动。
- 不把 `candidate.svg`、`centerline.svg`、`cleaned.svg`、`semantic.svg` 或 `refined.pdf`
  当作客户交付物。
- 不把 piece acceptance、`delivery_ready=true` 或 `max_deviation <= 0.2mm` 单独当作生产级 PASS。
- 最终回复按 `docs/acceptance-contract.md` 输出 PASS/FAIL/BLOCKED 证据；文档-only 任务报告 BLOCKED
  或“未运行交付验收”。

## 必读范围

每个任务默认只读：

1. `CURRENT_SLICE.md`
2. `agents.md`
3. 本轮相关短文档或任务包

按需读取：

- `Handoff.md`：只有当前状态、最近验证或历史决策不足时读取。
- `docs/acceptance-contract.md`：只有要汇报交付验收或修改验收逻辑时读取。
- `docs/code-map.md`：需要读取 Python 代码前先读。

需要 OpenSpec 状态时再读：

```text
openspec/changes/pdf-to-refined-vector-pdf-mvp/tasks.md
```

## 代码读取边界

默认不要全文读取这些长文件：

- `src/pattern_refine/pipeline.py`
- `src/pattern_refine/evaluate.py`
- `src/pattern_refine/semantic.py`

读取代码时先用 `docs/code-map.md` 定位，再用 `Select-String` 查目标 symbol 和 80-150 行上下文。
如果局部窗口不足，先说明缺口再扩大读取范围。

## 每轮维护

每轮结束时只更新本文件顶部 `Next Session Snapshot`，覆盖旧内容，不追加流水账。只记录下一轮
避免重复工作所需的最小事实：本轮完成、下一步、读取范围、禁止重复事项、阻塞和关键验证摘要。

不要把详细日志、长命令输出、生成物清单或历史讨论塞进本文件。

## 派工规则

- 不要让子代理 fork 完整对话上下文。
- 只发送 30-60 行压缩派工单。
- 派工单必须包含 route、task、write scope、read scope、allowed commands、validation 和 return format。
- 不要把 `agent_docs/rules-detail.md` 整段复制进派工单；只摘当前任务需要的规则。
- 派工单必须包含“不要全文读取 `pipeline.py` / `evaluate.py` / `semantic.py`，先用
  `docs/code-map.md` 定位”的上下文限制。
