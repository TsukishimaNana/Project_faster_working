# Production Reconstruction Direction

用途：固定方案 B 的执行方向，避免后续会话继续按旧 delivery closure 或 scan tracing 思路推进。

## 结论

当前目标不是把扫描黑线直接矢量化成 final SVG，而是：

1. 从 `pink-dress-original-scan.pdf` 建立页面归一化扫描证据层。
2. 从黑线证据中识别制版特征。
3. 用规则化 primitive graph 重新勾线。
4. 生成类似 `pink-dress-simple-reference.svg` 风格的干净生产 SVG 草稿。
5. 用 production cleanliness/topology gate 阻止非生产级 SVG 被误报为 PASS。

旧的 `verify-delivery`、piece acceptance 和 `delivery_ready=true` 只能证明几何接近 reference，
不能证明 SVG 生产可用。

## 当前不合格问题

用户按生产经验指出，当前 final 最明显的问题是：

- 重线：局部有多条近似重合线，不是单条生产线。
- 线条磕巴：轮廓有很多触点、抖动、小折点，像沿扫描墨迹或像素边缘跑线。
- 断点：局部轮廓不连续，有断裂、缺口或碎段。

这些问题说明当前输出仍像扫描线稿矢量化结果，而不是制版几何重绘结果。即使 `max_deviation`
小于 `0.2mm`，也不能视为生产级。

## Reference / Oracle 角色

`pink-dress-simple-reference.svg` 在方案 B 中只作为 oracle/reference：

- 展示干净生产 SVG 应该是什么结构和线条质量。
- 帮助判断哪些扫描黑线应保留、哪些噪声应忽略。
- 帮助定义 notch、直线边、曲线边、短对位标和比例尺的表达方式。
- 用于验收系统输出是否接近人工制版意图。

不要把它当 fallback template 直接复制成 final，也不要把 reference-guided 输出描述为 scan-only
自动重建。若未来临时使用 reference preserved 输出，必须明确标记来源，不能作为方案 B 自动重建证据。

`pink-dress-original-scan-SVG-VS-PDF.pdf` 是 overlay oracle：它展示红色生产线与扫描黑线的关系。
第一阶段先作为人工验收说明，不自动解析它，避免扩大范围。

## Production Quality Report / Gate

production-quality report 是机器可读的生产质量检查报告。

production-quality gate 是交付门槛：如果 gate 未实现或未通过，不能报告生产级 PASS。

示例输出：

```json
{
  "accepted": false,
  "manual_review_required": true,
  "blockers": [
    "overlapping_lines_detected",
    "jagged_polyline_detected",
    "open_or_broken_contour_detected"
  ]
}
```

它的作用不是生成新 SVG，而是先让系统能明确判定“非生产级 SVG 不合格”，避免再用
piece acceptance 误报 PASS。

## 第一阶段任务包

ROUTE: 方案 B 第一阶段，先建立 production cleanliness/topology gate，不先改 tracing 算法。

TASK: 生成 `*.production-quality-report.json`，用于判定当前 final/reference/debug SVG 是否达到生产级
基础质量。当前 final 如果存在重线、磕巴、断点等问题，报告必须 `accepted=false` 并列出 blocker。

WRITE_SCOPE:

- 可新增 `src/pattern_refine/production_quality.py`
- 可新增 CLI 子命令或先做内部函数测试
- 对应测试文件
- 必要时更新 `docs/acceptance-contract.md`、`CURRENT_SLICE.md`

READ_SCOPE:

- `docs/production-reconstruction-direction.md`
- `docs/code-map.md`
- `docs/acceptance-contract.md`（如果接入交付验收）
- 只按 symbol/window 读取相关代码；不要全文读取 `pipeline.py`、`evaluate.py`、`semantic.py`

INPUT:

- 当前 final SVG，例如 `examples/output/pink-dress-original-scan.final.svg`
- reference oracle：`knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-simple-reference.svg`
- 可选 debug SVG：`candidate.svg`、`centerline.svg`、`semantic.svg`

OUTPUT:

- `*.production-quality-report.json`
- 可选 `*.production-quality-overlay.svg`

FIRST_GATE_CHECKS:

- 重复或近似重合 path/line/segment。
- open path、断裂 contour、未闭合裁片。
- 过密点、过多短 segment、jagged polyline。
- 孤立短碎线或非生产噪声混入 final。
- outline tracing / double-line suspicion。
- 对象语义混乱：裁片 path、比例尺 line、rect/mark 未分离。
- viewBox/page size 是否归一化。
- `manual_review_required=true`，直到人工/规则验收闭环足够明确。

VALIDATION:

- 当前非生产级 final 不得 `accepted=true`。
- report 必须列出 blocker 和可定位的问题摘要。
- piece acceptance 只能作为辅助字段，不能让 production gate 自动 PASS。
- 不写入、不移动、不覆盖 `knowledge_base/PDF-SVG/Original_PinkShirts`。
- 不做 DXF/PLT、OCR、UI 或多样本泛化。

RETURN:

```text
STATUS: PASS | FAIL | BLOCKED
PRODUCTION_QUALITY_REPORT:
ACCEPTED:
MANUAL_REVIEW_REQUIRED:
BLOCKERS:
INPUT_SVG:
REFERENCE_ORACLE:
COMMANDS_RUN:
FILES_CHANGED:
RISKS:
NEXT:
```

## 后续阶段

第二阶段才进入 feature recognition 和 rule-based production tracing：

- scan evidence layer：归一化黑线、component、skeleton、噪声过滤证据。
- feature recognition：裁片、直边、曲边、尖角、剪口、短对位标、比例尺。
- rule-based tracing：用少量 line/Bezier primitive 生成干净 SVG 草稿。
- manual review：保留 uncertain regions，默认需要人工复核。
