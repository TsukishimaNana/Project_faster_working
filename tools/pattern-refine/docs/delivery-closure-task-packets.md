# Delivery Closure Task Packets

用途：把当前 MVP 收口拆成可直接下发给主线程或窄范围实现任务的 packets。每个任务都必须以
`docs/acceptance-contract.md` 的结果格式收尾。

> 状态说明：本文件记录的是旧 delivery closure 批次。该批次已补齐 verify-delivery、
> scan-vs-reference-guided report 和 overlay diagnostic report，但用户已确认旧口径不能代表
> 生产级 SVG。后续不得把逐裁片 `0.2mm`、`delivery_ready=true` 或 reference-guided 几何接近
> 单独当作生产级 PASS；必须转向 scan evidence + feature recognition + rule-based production
> tracing，并增加 production cleanliness/topology gate。

## Task 1: Verify Delivery Command

ROUTE: 历史任务。旧单样本 MVP = reference-guided production reconstruction。该命令仍可作为
几何接近检查入口，但不足以证明生产级交付。

TASK: 增加一个交付检查入口，读取 final SVG、final status report 和 piece acceptance report，
输出机器可判定的 PASS/FAIL。

WRITE_SCOPE:

- `src/pattern_refine/cli.py`
- 如需拆分，可新增 `src/pattern_refine/delivery.py`
- `tests/test_cli.py` 或新增对应测试文件
- 必要时更新 `README.md`

READ_SCOPE:

- `docs/acceptance-contract.md`
- `src/pattern_refine/report.py`
- `src/pattern_refine/evaluate.py`
- `tests/test_pipeline.py`

COMMAND:

```powershell
pattern-refine verify-delivery <final.svg> --status <final-status-report.json> --piece-report <piece-acceptance-report.json>
```

VALIDATION:

- final SVG 存在。
- final status report 中 `geometry_source == reference-guided`。
- final status report 中 `delivery_ready == true`。
- piece acceptance report 中 `accepted == true`。
- piece acceptance report 中 `max_deviation_mm <= 0.2`。
- `failed_reference_piece_indices` 为空。
- 任一条件失败时命令返回非 0，并输出失败原因。

RETURN:

```text
STATUS: PASS | FAIL | BLOCKED
FINAL_SVG:
GEOMETRY_SOURCE:
DELIVERY_READY:
PIECE_ACCEPTANCE_REPORT:
MAX_DEVIATION_MM:
FAILED_PIECES:
COMMANDS_RUN:
FILES_CHANGED:
RISKS:
NEXT:
```

OPEN_SPEC_TASKS:

- 支撑可重复几何接近验收入口；生产级 PASS 还需要 cleanliness/topology gate。

## Task 2: Scan vs Reference-Guided Difference Report

ROUTE: 历史任务。scan-only centerline 是诊断层；reference-guided final SVG 只代表旧几何接近
对比层，不再单独代表生产级交付主线。

TASK: 生成 `*.scan-vs-reference-guided-report.json`，明确 scan-only 与 reference-guided 的
验收差异，防止后续把诊断层误当交付层。

WRITE_SCOPE:

- `src/pattern_refine/pipeline.py`
- 可新增 `src/pattern_refine/difference_report.py`
- 对应测试文件
- 必要时更新 `README.md` / OpenSpec tasks

READ_SCOPE:

- `src/pattern_refine/evaluate.py`
- `src/pattern_refine/report.py`
- `docs/acceptance-contract.md`
- `openspec/changes/pdf-to-refined-vector-pdf-mvp/tasks.md`

EXPECTED_OUTPUT:

```json
{
  "scan_only_layer": "semantic.svg or centerline.svg",
  "final_layer": "final.svg",
  "final_geometry_source": "reference-guided",
  "scan_only_delivery_ready": false,
  "reference_guided_delivery_ready": true,
  "scan_only_max_deviation_mm": 2.05,
  "reference_guided_max_deviation_mm": 0.122,
  "decision": "scan-only remains diagnostic"
}
```

VALIDATION:

- report 写入输出目录，不写入 `Original_PinkShirts`。
- report 明确 `scan_only_delivery_ready=false`。
- report 明确 `reference_guided_delivery_ready` 来自 final status / piece acceptance。
- report 不把 `debug-pass`、结构接近或 centerline 匹配数当作交付通过。

RETURN:

```text
STATUS: PASS | FAIL | BLOCKED
FINAL_SVG:
SCAN_ONLY_LAYER:
REFERENCE_GUIDED_REPORT:
SCAN_ONLY_MAX_DEVIATION_MM:
REFERENCE_GUIDED_MAX_DEVIATION_MM:
DECISION:
COMMANDS_RUN:
FILES_CHANGED:
RISKS:
NEXT:
```

OPEN_SPEC_TASKS:

- 明确 scan-only centerline 与 reference-guided final SVG 的差异报告。
- 保留 scan-only centerline reconstruction 作为诊断层。

## Task 3: Overlay And Orientation Diagnostic Report

ROUTE: final SVG 即使逐裁片通过，也必须确认没有页面方向、比例、镜像、布局或明显 overlay 问题。

TASK: 生成 `*.delivery-overlay-report.json`，汇总 scan render、scale marker、page orientation、
viewBox/page size 和 overlay 人工复核入口。

WRITE_SCOPE:

- `src/pattern_refine/pipeline.py`
- 可新增 `src/pattern_refine/delivery_overlay.py`
- 对应测试文件
- 必要时更新 docs

READ_SCOPE:

- `src/pattern_refine/orientation.py`
- `src/pattern_refine/scale.py`
- `src/pattern_refine/visualize.py`
- `docs/pink-dress-overlay-acceptance-method.md`

EXPECTED_OUTPUT:

```json
{
  "page_rotation": 270,
  "orientation_normalized": true,
  "scale_report_path": "...scale-report.json",
  "final_svg_viewbox_matches_page_mm": true,
  "overlay_svg_path": "...overlay.svg",
  "manual_overlay_review_required": true,
  "known_visual_risks": [],
  "decision": "overlay diagnostics retained"
}
```

VALIDATION:

- report 写入输出目录，不写入 `Original_PinkShirts`。
- report 明确 page rotation / orientation 状态。
- report 链接 scale report 和 overlay SVG。
- 如果 overlay 仍需人工确认，必须明确 `manual_overlay_review_required=true`，不得自动宣称视觉 PASS。

RETURN:

```text
STATUS: PASS | FAIL | BLOCKED
FINAL_SVG:
OVERLAY_REPORT:
ORIENTATION_NORMALIZED:
SCALE_REPORT:
OVERLAY_SVG:
MANUAL_REVIEW_REQUIRED:
COMMANDS_RUN:
FILES_CHANGED:
RISKS:
NEXT:
```

OPEN_SPEC_TASKS:

- 对 scan render、scale marker、page orientation 和 overlay 继续运行诊断。
- 复核最终 SVG overlay 关系，确认没有明显双边线、重线、断线和 outline tracing 痕迹。
- 保证 reference-guided 裁片轮廓连续且不出现扫描双边线或 outline tracing 痕迹。

## Recommended Order

1. Task 1: Verify Delivery Command
2. Task 2: Scan vs Reference-Guided Difference Report
3. Task 3: Overlay And Orientation Diagnostic Report

不要并行修改同一批 pipeline/report 文件。若需要并行，先做 Task 1，确认接口稳定后再拆 Task 2/3。
