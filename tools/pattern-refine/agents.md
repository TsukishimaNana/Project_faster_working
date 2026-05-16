# PatternRefine Agent Rules

本文件是新会话默认入口，只保留永久硬规则。长版背景、单位细节、子代理细则和踩坑记录见
`agent_docs/rules-detail.md`。仍需遵守个人全局配置 `..\..\.codex\AGENTS.md`；如有冲突，
本文件优先约束 PatternRefine 的项目安全和 source-of-truth。

## 必读顺序

开发、调试或 OpenSpec 推进前只读：

1. `CURRENT_SLICE.md`
2. `agents.md`

需要读代码前先读：

3. `docs/code-map.md`

只有当前任务需要任务状态、验收口径或背景细节时，再读 `Handoff.md`、
`docs/acceptance-contract.md`、当前 OpenSpec `tasks.md`、`docs/handoff-details.md`
或 `agent_docs/rules-detail.md`。
不要把完整历史、全量 OpenSpec、完整 rules detail 默认塞进上下文。
不要默认全文读取 `src/pattern_refine/pipeline.py`、`src/pattern_refine/evaluate.py`、
`src/pattern_refine/semantic.py`；使用 `docs/code-map.md` 和局部 symbol 查询。

## 永久硬规则

- 当前 MVP 只针对 `pink-dress-original-scan.pdf` 单样本。
- 当前主线是 scan-evidence + feature recognition + rule-based production tracing。
- 扫描 PDF 是页面归一化和黑线证据 source；不能把扫描轮廓、骨架或 debug centerline 直接升级为生产级 final。
- `pink-dress-simple-reference.svg` 和 `pink-dress-original-scan-SVG-VS-PDF.pdf` 是当前样本 reference/oracle，
  用于理解和验证“扫描黑线 -> 红色生产线”的制版抽象规则；不擅自回滚用户确认的工作区改动。
- 客户主交付物是 `*.final.svg`。
- `*.refined.pdf`、`candidate.svg`、`centerline.svg`、`cleaned.svg`、`semantic.svg`、overlay 和 report 都是内部验证产物。
- `knowledge_base/PDF-SVG/Original_PinkShirts` 是原始/参考目录，不得写入派生产物、覆盖、移动或编辑。
- 默认输出写到 `examples/output/`、测试临时目录或明确的 derived 目录。
- 程序内部几何单位统一为 mm；PDF 绘制必须按 `pt = mm * 72 / 25.4` 换算。
- 最终 SVG 必须有明确 geometry source，并说明是 reference-preserved、rule-reconstructed draft，
  还是 scan-evidence diagnostic。
- 当前样本的逐裁片 `max deviation <= 0.2mm` 只是几何接近 gate，不再等同生产级验收。
- `delivery_ready=true` 必须同时来自 piece acceptance 和 production cleanliness/topology gate；
  若 cleanliness/topology gate 未实现或未通过，不能报告生产级 PASS。
- 不允许用 `debug-pass`、`shape-debug-pass`、`mvp-pass`、object count、结构接近或平均值代替交付验收。
- 不允许把 reference-guided、scan-evidence 或 centerline 输出描述成已经达到生产级，除非通过
  无重合线、无双边线、连续拓扑、对象语义清晰和少点数可编辑性验收。
- scan-only centerline 只保留为诊断和特征识别输入，不是当前 final geometry 主线。
- 发现方向、比例、镜像、viewBox 或坐标轴问题时，先做全局诊断，再调局部几何。



## 工作方式

- 开始开发或调试前，使用 `project-agent-routing` 技能判断 L0-L3，并汇报：路由等级、当前 OpenSpec 阶段、最小任务批次、主要风险。
- L0/L1 由主线程直接处理；只有用户明确要求子代理时才派发子代理。
- 每轮任务只围绕 `CURRENT_SLICE.md` 的 1-3 项推进；不要顺手扩大范围。
- 修改 CLI 参数、交付口径或验收逻辑时，同步更新测试、Handoff、OpenSpec 和 README。
- 不要默认 broad search 全仓库；优先搜索具体函数名、字段名或文件名。
- 不要把生成物、测试临时输出、`.tmp*`、`.pytest-tmp`、`examples/output/*` 当作 source-of-truth。

- 如果我的决定会明显导致范围漂移、验收失效、数据污染、虚假进展或不可维护实现，你必须先指出问题，再执行。不要因为我要求推进，就默认我的方向是对的。如果存在更保守、更可验证的路径，优先提出并说明理由。如果你判断当前要求会让项目更乱，你要先收缩任务，而不是顺着做大。

- 除非遇到阻塞、范围变化或需要我做产品决策，否则不要中途停下等我“继续”。你应在当前任务批次内自主完成实现、验证、审查和结果整理。

## 文档维护频率

- 每轮更新：`CURRENT_SLICE.md` 顶部 `Next Session Snapshot`。只覆盖下一轮接手所需的最小事实，
  不保留流水账。
- 任务正式化时更新：当前 OpenSpec `tasks.md` 或新 task packet。
- 路线、硬规则或接手协议变化时更新：`Handoff.md`、`agents.md`。
- 验收规则变化时更新：`docs/acceptance-contract.md`。
- 代码结构、长文件入口或推荐读取窗口变化时更新：`docs/code-map.md`。
- 背景说明变化时更新：`docs/handoff-details.md` 或其他专题文档。
- 不要每轮更新 `Handoff.md`；只有“新会话不知道就会走错方向”的长期事实变化时才更新。

## 文档语言策略

- 项目文档以中文为主，保留必要英文术语、命令、文件名、字段名和状态码。
- 面向新会话的入口文档要短、直接、可执行；避免长背景叙述和历史流水账。
- 技术术语第一次出现时可用中文解释，后续使用稳定短语，例如 scan evidence、feature recognition、
  rule-based production tracing、production cleanliness/topology gate。
- 验收和风险说明必须明确区分“几何接近”“诊断证据”和“生产级交付”。

## 验收报告

最终回复优先按 `docs/acceptance-contract.md` 报告结果。用户主要验收，验收内容以中文为主：

- `FINAL_SVG`
- `GEOMETRY_SOURCE`
- `DELIVERY_READY`
- `PIECE_ACCEPTANCE_REPORT`
- `MAX_DEVIATION_MM`
- `FAILED_PIECES`
- `COMMANDS_RUN`
- `RISKS`

代码过程只在必要时简述，不要用长 diff 或长日志替代可验收证据。

## 常用验证命令

从 `tools\pattern-refine` 运行：

```powershell
$env:TEMP = (Resolve-Path .pytest-tmp).Path
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m ruff check .
npm run spec:validate
```
