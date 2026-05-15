# Current Slice

用途：保存下一批实现任务的压缩上下文。窄任务派发时优先读本文件，不要反复重读完整
`Handoff.md` 或 OpenSpec 全量上下文。

## 路线

- 当前 MVP 路线：reference-guided production reconstruction。
- 客户交付物：`*.final.svg`。
- scan-only centerline 只作为诊断层和后续泛化路线。
- source/reference 目录只读：`knowledge_base/PDF-SVG/Original_PinkShirts`。

## 当前状态

- `pink-dress-simple-reference.svg` 已只读加载为 production geometry template。
- `refine_pdf()` 已为 `pink-dress-original-scan.pdf` 写出 reference-guided `final.svg`。
- final status report 已包含 `geometry_source=reference-guided`。
- 最近完整验证：`pytest -q` 88 passed，`ruff check .` passed，`npm run spec:validate` passed。

## 当前批次

1. 将 final SVG piece acceptance 接入 pipeline final-status/report。
2. 保持 scan render、scale marker、orientation 和 overlay diagnostics 不断链。
3. 增加 scan-only 与 reference-guided 的差异报告。

## 派工规则

不要让子代理 fork 完整对话上下文。只发送 30-60 行压缩派工单，包含 route、task、
write scope、read scope、allowed commands、validation 和 return format。
