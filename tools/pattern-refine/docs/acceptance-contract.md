# Acceptance Contract

用途：固定 PatternRefine 每轮开发后的验收口径。用户主要验收结果和证据，不需要阅读代码过程。

## 唯一交付目标

当前单样本 MVP 的客户主交付候选只有：

```text
*.final.svg
```

以下产物只能作为内部验证或诊断证据：

- `*.refined.pdf`
- `*.candidate.svg`
- `*.centerline.svg`
- `*.cleaned.svg`
- `*.semantic.svg`
- `*.overlay.svg`
- `*.deviation-report.json`
- `*.scale-report.json`
- `*.feature-report.json`
- `*.final-status-report.json`
- `*.piece-acceptance-report.json`
- `*.production-quality-report.json`

## PASS 条件

只有同时满足以下条件，才能报告 `STATUS: PASS`：

- final SVG 已生成，并且是唯一客户交付候选。
- final status report 标明明确可信的 `geometry_source`，且不是 scan-only/debug/outline tracing。
- final status report 的 `delivery_ready=true`。
- piece acceptance report 存在。
- piece acceptance report 的 `accepted=true`。
- production-quality report 存在。
- production-quality report 的 `accepted=true`。
- 每个 reference 裁片都匹配成功。
- 每个裁片 `max_deviation_mm <= 0.2`。
- `failed_reference_piece_indices` 为空。
- production cleanliness/topology evidence 存在并通过：无重合线、无双边线、无明显断线、无 outline tracing、
  裁片 path 连续闭合、对象语义清晰、点数/曲线表达适合后续编辑生产。
- 没有把 debug SVG、PDF、结构指标或 scan-only centerline 当作交付通过依据。

## FAIL 条件

出现任一情况，报告 `STATUS: FAIL` 或 `STATUS: BLOCKED`：

- final SVG 未生成。
- `geometry_source` 未标明，或仍是 scan-only/debug/outline tracing。
- `delivery_ready=false`。
- 任一裁片未匹配。
- 任一裁片 `max_deviation_mm > 0.2`。
- piece acceptance report 缺失。
- production cleanliness/topology evidence 缺失。
- production-quality report 缺失或 `accepted=false`。
- 结果仍表现为 outline tracing、双边线、重线、断线或明显方向/比例/镜像错误。
- 原始/参考目录被写入派生产物或被未确认修改。

## 固定回复格式

每轮完成后，最终回复优先使用：

```text
STATUS: PASS | FAIL | BLOCKED
FINAL_SVG:
GEOMETRY_SOURCE:
DELIVERY_READY:
PIECE_ACCEPTANCE_REPORT:
MAX_DEVIATION_MM:
FAILED_PIECES:
OUTPUT_DIR:
COMMANDS_RUN:
FILES_CHANGED:
RISKS:
NEXT:
```

## 过程输出限制

- 不要用长代码 diff、长测试日志或 OpenSpec 任务数替代验收证据。
- 如果测试通过但 `delivery_ready=false`，必须报告 `FAIL` 或 `BLOCKED`。
- 如果结构、shape 或 debug 指标通过，但 piece acceptance 未通过，必须报告 `FAIL`。
- 如果 piece acceptance 通过但 production cleanliness/topology gate 未实现或未通过，必须报告
  `BLOCKED` 或 `FAIL`，不能报告生产级 `PASS`。
- 如果只是完成文档、重构或诊断，不涉及最终交付验收，报告 `STATUS: BLOCKED` 或说明“未运行交付验收”。

## 用户验收视角

用户只需要优先看：

1. `STATUS`
2. `FINAL_SVG`
3. `DELIVERY_READY`
4. `MAX_DEVIATION_MM`
5. `FAILED_PIECES`
6. `RISKS`

代码改动说明保持简短，只说明与 final SVG / piece acceptance / delivery readiness 的关系。
