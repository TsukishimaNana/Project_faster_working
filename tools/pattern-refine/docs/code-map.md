# Code Map

用途：让新会话在不全文读取长 Python 文件的情况下定位代码。默认先读本文件，再按目标函数读取
80-150 行窗口。

## 禁止默认全文读取

以下文件较长，除非已经有明确目标函数和理由，不要全文 `Get-Content -Raw`：

- `src/pattern_refine/pipeline.py`
- `src/pattern_refine/evaluate.py`
- `src/pattern_refine/semantic.py`

推荐读取方式：

```powershell
Select-String -Path src/pattern_refine/pipeline.py -Pattern "final_status_report_path" -Context 6,20
Select-String -Path src/pattern_refine/evaluate.py -Pattern "^def evaluate_svg_piece_acceptance" -Context 0,90
Select-String -Path src/pattern_refine/semantic.py -Pattern "^class SemanticGeometryReport|^def reconstruct_semantic_geometries" -Context 0,80
```

如果需要更多上下文，先说明缺口，再扩大到相邻函数窗口；不要从“理解全文件”开始。

## pipeline.py

职责：编排 PDF 渲染、黑线提取、诊断 SVG/report 写出、final/status/report 写出。

主要入口：

- `PageRenderResult`：pipeline 返回契约；新增输出路径或 report 字段时先查这里。
- `refine_pdf()`：主编排函数；输出路径注册、overwrite guard、各阶段调用都在这里。
- `extract_black_lines()`：黑线二值提取。
- `_render_page()`：PyMuPDF 页面渲染。
- `_ensure_can_write()`：输出覆盖保护。
- `_scan_only_max_deviation_mm()`：scan-only 差异报告辅助汇总。

常见定位：

- 新增输出文件：查 `PageRenderResult`、`*_path = output_dir / ...`、`_ensure_can_write`、return block。
- 修改交付状态：查 `final_status_report`、`write_final_svg_status_report`。
- 修改 overlay/scale/report 写出：查对应 `write_*_report` 或 `*_report_path`。

## evaluate.py

职责：SVG/reference 几何对比、piece acceptance、shape/structure report。

主要入口：

- `SvgPieceAcceptanceReport`：逐裁片验收 report schema。
- `evaluate_svg_piece_acceptance()`：final SVG vs reference SVG 的当前几何接近 gate。
- `evaluate_svg_piece_deviation()`：物理坐标下的 piece deviation report。
- `evaluate_svg_shape()`：归一化 shape 比较。
- `collect_svg_structure_metrics()`：SVG object count/type 结构指标。
- `write_svg_piece_acceptance_report()` 等 `write_*`：JSON 写出。

内部解析/匹配热点：

- `_collect_piece_shapes()`：从 SVG 收集可验收裁片对象。
- `_scale_piece_shapes_to_mm()`：把 SVG 坐标换算到 mm。
- `_match_piece_shapes()`：candidate/reference piece 匹配。
- `_bidirectional_piece_distances()`：双向 contour 距离。
- `_svg_units_to_mm()` / `_svg_viewbox_bbox()`：SVG 坐标和单位处理。

注意：这里的 `max_deviation <= 0.2mm` 只能证明几何接近 reference，不等于生产级 cleanliness/topology。

## semantic.py

职责：从扫描诊断几何中推断语义层、centerline diagnostics、比例尺线语义。当前它是诊断和特征识别输入，
不是生产级 final geometry。

主要入口：

- `CenterlinePieceDiagnostic`：scan-only centerline 对 reference 的诊断记录。
- `SemanticGeometryReport`：语义层 report schema。
- `reconstruct_semantic_geometries()`：语义层主入口。
- `write_semantic_geometry_report()`：JSON 写出。

特征/centerline 相关热点：

- `_major_centerline_paths_with_diagnostics()`：centerline candidate 与 reference diagnostic。
- `_piecewise_scored_centerline_candidates()`：按裁片区域生成/评分候选。
- `_centerline_piece_score()` 和 `_centerline_piece_rejection_reason()`：centerline 评分/拒绝原因。
- `_path_distance_summary()`：centerline/reference 距离汇总。
- `_promote_linear_contour()` / `_promote_rect_contour()`：线/矩形语义提升。
- `_scale_marker_lines()`、`_promoted_scale_marker_ticks()`：比例尺语义。

注意：如果任务是方案 B 的新特征识别，可以先新增独立模块承载 scan evidence / feature graph，不要继续把
`semantic.py` 扩成生产级勾线器。

## 推荐新模块边界

方案 B 后续实现优先拆出新模块，而不是继续扩大长文件：

- `scan_evidence.py`：页面归一化后的黑线证据、component/skeleton/ignored noise report。
- `feature_recognition.py`：piece/edge/corner/notch/alignment mark/scale candidates。
- `production_tracing.py`：规则化 primitive graph 到 clean production SVG draft。
- `production_quality.py`：重合线、双边线、断线、闭合、点数、对象语义 gate。
