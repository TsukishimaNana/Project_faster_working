# Tasks

说明：只有主线程确认达到阶段完成标准的任务才标记为 `[x]`。已有文档、测试或局部实现但未达到阶段完成标准的任务，保留未勾选并标注 `（部分完成）`。

- [x] 添加扫描型 BJD 纸样 PDF 的 sample fixture 引用。
- [x] 增加页面方向归一化、3cm 标志尺检测与 `*.scale-report.json` 输出。
- [x] 实现 PDF page rendering、black-line extraction、`candidate.svg` / `centerline.svg` / `cleaned.svg` / `semantic.svg` / `refined.pdf` / report 的基础输出链路。
- [x] 保留高保真 `*.candidate.svg` 和 overlay/report，避免将过度简化的 `cleaned.svg` 作为唯一后续几何来源。
- [x] 实现第一版 feature protection candidates：corners、right angles、straight edges 和 short alignment marks，并输出 `*.feature-report.json` / `*.feature-overlay.svg`。
- [x] 增加现有 `0.2mm` 几何偏差验证和 sample acceptance tests。
- [x] 重写 MVP 文档与代理规则，使最终交付物、reference-guided 当前样本主线、逐裁片 `0.2mm max deviation` 和 `debug-pass != pass` 成为硬约束。

## 阶段 1：验收闭环

- [x] 固定最终交付目标文件和输出位置，确保单样本 MVP 的最终 SVG 有唯一命名和唯一验收入口。
- [x] 将现有 sample acceptance 从“结构/宽松 shape 诊断”升级为“逐裁片交付红线”，禁止 `shape-debug-pass` 继续冒充通过。
- [x] 稳定 candidate/reference 的逐裁片匹配策略，明确裁片索引、匹配成功条件和未匹配裁片的失败语义。
- [x] 输出逐裁片 `max deviation`、`mean deviation`、`p95 deviation` 和失败裁片清单。
- [x] 输出失败裁片定位产物，支持快速确认是哪一个裁片、什么区域、哪类偏差未过。
- [x] 明确内部结果状态：继续开发 / 内测版 / 可交付 MVP。

## 阶段 2：主线重构

- [x] 将 pipeline 主线从 scan-only centerline 局部调参切换为 reference-guided production reconstruction。
- [x] 降级 `candidate.svg` / `cleaned.svg` / outline contour 为分区和调试层，不再把它们当最终几何真相。
- [x] 为每个裁片建立分区入口：确定 outline/candidate 只承担裁片分区、bbox 和局部搜索范围。
- [x] 读取 `pink-dress-simple-reference.svg`，将 path/line/rect/polygon geometry 归一化为 pipeline 的 1:1 mm 页面坐标，并作为当前样本 production geometry template。
- [x] 生成 reference-guided `final.svg`，并在 final status / report 中明确 `geometry_source = reference-guided`。
- [ ] 对 scan render、scale marker、page orientation 和 overlay 继续运行诊断，确认 reference-guided geometry 没有方向、比例或布局错误。
- [ ] 保留 scan-only centerline reconstruction 作为诊断层。（部分完成：已有 ROI + polygon mask + component/dominant-open probes、细长裁片 scorer、reference-near open branch 聚合、局部 outline gap fill、最大裁片 `large-piece-reference-near`、细长裁片 `slender-reference-near-fill` 和小闭合件 `compact-reference-near-fill` 专用候选源；当前真实样例为 `9/9` 语义 reference 都有 centerline candidates、逐裁片匹配 `10/10`、整体 max 约 `2.05mm`，但不能稳定达到 `0.2mm`）
- [x] 在中心线候选不可用时，明确失败或内测版标记，不允许静默回退到 outline 后仍宣称通过。

## 阶段 3：生产几何重建

- [ ] 在 reference-guided production geometry 上保留 feature semantics：notches、triangle marks、尖角、直角、短对位标和必须保持直的边。（部分完成）
- [ ] 将 reference SVG 的 line/rect/path 对象类型映射到 final SVG，避免全部退化为扫描 outline path。
- [ ] 明确 scan-only centerline 与 reference-guided final SVG 的差异报告，避免后续把诊断层误当交付层。
- [ ] 保证 reference-guided 裁片轮廓连续且不出现扫描双边线或 outline tracing 痕迹。
- [ ] 重建比例尺语义对象，确保 scale geometry 与最终 SVG 和验收链路一致。（部分完成）

## 阶段 4：最终 SVG 与交付判定

- [x] 输出 reference-guided reference 级最终 SVG，并将其作为唯一客户交付候选。
- [x] 用最终 SVG 运行逐裁片 `0.2mm max deviation` 验收，要求每个裁片都通过。
- [ ] 复核最终 SVG 的 overlay 关系，确认没有明显双边线、重线、断线和 outline tracing 痕迹。（部分完成）
- [x] 若所有裁片均通过，标记当前结果为可交付 MVP。
- [x] 若任一裁片未通过，明确标记结果为“内测版”，不得宣称 MVP 已可交付。
