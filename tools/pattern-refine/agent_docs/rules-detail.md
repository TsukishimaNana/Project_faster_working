# PatternRefine Detailed Agent Rules

本文件保存 PatternRefine 的长版规则、背景和踩坑记录。新会话默认先读根目录
`agents.md`、`Handoff.md` 和 `CURRENT_SLICE.md`；只有遇到规则细节、子代理调度、
中文编码、单位换算或历史踩坑问题时，再读本文。

## 项目目标

PatternRefine 用于将扫描型 BJD 纸样 PDF 重建为 reference 级生产几何。当前第一版
MVP 只针对 `pink-dress-original-scan.pdf` 单样本推进，当前路线是
reference-guided production reconstruction：扫描 PDF 用于方向、比例、布局和 overlay
诊断，`pink-dress-simple-reference.svg` 作为只读生产几何模板生成最终 SVG。

当前 MVP 的客户主交付物是最终 SVG。PDF、debug SVG 和各种 report 是内部验证产物，
不是客户主交付物。

## 项目目录结构

```text
tools\pattern-refine\
  Handoff.md
  CURRENT_SLICE.md
  agents.md
  README.md
  pyproject.toml
  package.json
  src\pattern_refine\
  tests\
  openspec\
  docs\
  agent_docs\
  assets\fonts\
  examples\input\
  examples\output\
  knowledge_base\PDF-SVG\Original_PinkShirts\
```

## 输出和生成物规则

- `Original_PinkShirts` 只读；任何派生图片、SVG、PDF、报告都不能写进去。
- MVP 默认输出目录优先使用 `examples\output\`。
- 后续如生成较多分析材料，可新增 `knowledge_base\derived\...`，但必须与
  `Original_*` 原始目录分离。
- 推荐输出命名：
  - `pink-dress-page-001-render.png`
  - `pink-dress-page-001-lines.png`
  - `pink-dress.candidate.svg`
  - `pink-dress.centerline.svg`
  - `pink-dress.cleaned.svg`
  - `pink-dress.semantic.svg`
  - `pink-dress.final.svg`
  - `pink-dress.refined.pdf`
  - `pink-dress.deviation-report.json`
- 默认不覆盖旧输出；需要覆盖时必须由 CLI 参数或明确任务说明触发。

## 单位和格式约定

- 程序内部几何单位统一为 mm。
- 矢量 PDF 必须为 1:1，页面和路径单位换算后应保持毫米真实尺寸。
- PDF 绘制单位通常是 pt，换算为 `pt = mm * 72 / 25.4`，不要把 mm 直接当 pt 写入。
- PLT 绘图仪单位为 1016。
- DXF 格式按 `1 unit = 1 mm` 输出。
- DXF/CAD 坐标通常 Y 轴向上；从 SVG/PDF 坐标导出 DXF 时必须明确处理 Y 轴方向。
- 扫描 PDF 转图片后必须建立 pixel-to-mm 校准；优先参考 PDF 上的厘米尺/英寸尺，
  其次参考已知 1:1 SVG/DXF。
- 当前参考 SVG/DXF 按用户判断视为 1:1，可用于校准和对比，但不要写回原始目录。
- 如需中文文字输出，使用 `assets\fonts\NotoSansSC-VF.ttf`，并在 PDF 中显式嵌入字体；
  不要依赖系统字体路径。

## 几何和验证规则

- 纸样路径必须能解释为真实 mm 几何；禁止混用 mm、px、pt 而不记录换算。
- 闭合裁片路径必须显式验证闭合；开路径、辅助线、比例尺、文字箭头不要混进主轮廓。
- 几何不合法时应失败并给出原因，不要静默输出空文件或残缺纸样。
- 比例尺和 1:1 输出不能只靠肉眼判断；必须能用已知厘米尺/英寸尺、SVG/DXF 参考或报告验证。
- 调试叠图、辅助线、OCR 文字层和最终导出层必须分离，避免把调试表达混入最终交付 SVG。
- 对称或重复裁片后续应通过数量/标注表达，不要为了视觉排版重复生成不可区分的几何副本。
- 当前单样本 MVP 的最终几何目标是 reference-guided production geometry；scan-only
  centerline 只保留为诊断和后续泛化路线，不是墨迹 blob 的 outline tracing。
- 当前样本主验收是逐裁片 `max deviation <= 0.2mm`；每个裁片都必须过，不允许以
  整体平均值、结构接近或 `debug-pass` 替代。
- `cleaned.svg`、`candidate.svg`、`centerline.svg`、`semantic.svg` 都是中间层；不能把它们误当成最终交付物。

## 中文编码和终端安全

- 除非有反证，所有文本文件按 UTF-8 处理。
- 不要把终端 mojibake 直接判定为文件损坏。
- 重写疑似乱码文件前，先验证源文件 bytes，或用显式 UTF-8 方式读取。
- PowerShell 处理中文路径时，优先使用 `-LiteralPath`、`Get-ChildItem` 返回的对象路径，
  以及明确支持 UTF-8 的工具。
- 不要手敲乱码中文路径后继续覆盖写入。
- 不要把终端渲染出来的中文文本当成唯一 source-of-truth。
- SVG 输出包含中文文字层时，必须明确保留 UTF-8 XML encoding，并使用支持中文 glyphs 的字体。
- 如果未来 PDF 输出包含中文文本，必须嵌入支持中文的字体，不依赖查看器默认字体。

## 重复错误预防

- 混淆 SVG 中间文件和最终交付物。
- 把 `debug-pass`、结构接近、object count 接近或 `mvp-pass` 当成客户可交付通过。
- 忽略原始 PDF `rotation=270` 与 reference 竖版坐标差异，未先完成页面方向归一化就开始调局部几何。
- 比例尺识别取整条黑线，而不是 4 刻度定义的 30mm 可读段。
- 无标记地复制 `pink-dress-simple-reference.svg` 或其他人工参考文件并冒充 scan-only
  算法输出。当前单样本 MVP 允许只读使用该 reference SVG 作为 reference-guided
  production template，但输出必须写入派生目录、完成坐标归一化、在 report 中标明
  `geometry_source=reference-guided`，并通过逐裁片验收。
- 把 OCR 当作第一版 geometry MVP 的阻塞项。
- 把生成产物写入原始知识库目录。
- 过度圆顺尖角、剪口、直角、三角标、短对位标或必须保持直线的生产边。
- 忽略 `0.2mm` 默认偏差阈值。
- 继续把 outline refinement/simplification 或 scan-only centerline 局部调参当成当前
  MVP final geometry 主线。
- 把 Illustrator image trace 作为 MVP 的隐藏运行时依赖。
- 假设样例 PDF 包含矢量路径或可抽取文字；当前粉色连衣裙 PDF 是 image-backed。
- 对中文路径/编码问题靠试错修补，而不是先验证 source-of-truth 文件和编码。

## 子代理和路由细则

开发、调试、OpenSpec 推进和子代理调度任务，必须先使用 `project-agent-routing` 技能判断任务等级。

| 等级 | 适用场景 | 执行方式 |
|---|---|---|
| L0 | 只读状态、解释代码、定位信息、不改文件 | 主线程直接处理 |
| L1 | 1-3 个文件、边界明确、局部测试可覆盖、不改变 OpenSpec 范围 | 主线程按 TDD 小步实现 |
| L2 | 多文件或单个 OpenSpec 小项，需要独立实现和审查 | 主线程派 1 个编程子代理，主线程审查 diff 和最终验证 |
| L3 | 一个 OpenSpec 大项或阶段，需要拆分、协调、阶段验证 | 主线程派 1 个推进子代理 |

子代理角色细则见：

- `agent_docs/subagents/main-thread.md`
- `agent_docs/subagents/progress-agent.md`
- `agent_docs/subagents/implementer-agent.md`
- `agent_docs/subagents/status-packet-template.md`

## MVP CLI 契约

```powershell
pattern-refine refine <input.pdf> --out <dir> --dpi 600 --scale auto
```

- 默认不覆盖已有输出；覆盖必须显式传 `--overwrite`。
- 默认输出 render PNG、line PNG、`*.candidate.svg`、`*.centerline.svg`、`*.cleaned.svg`、
  `*.semantic.svg`、`*.final.svg`、`*.refined.pdf`、`*.piece-acceptance-report.json`、
  `*.final-status-report.json` 和相关 debug reports。
- `--scale auto` 优先使用 PDF 中厘米尺/英寸尺校准；自动失败时应报告原因，并允许后续加入手动校准参数。

## 已知陷阱

| 场景 | 错误做法 | 正确做法 |
| --- | --- | --- |
| `comparison.svg` 或 per-piece overlay 出现大面积错位，且很多裁片看起来只差 90 度旋转、横竖页面方向或镜像。 | 继续调 path matching、feature classification、smoothing 或局部几何参数，把显眼的全局方向问题拖到最后才发现。 | 先做全局方向诊断：对 candidate/reference 尝试 0/90/180/270 度旋转和必要的翻转后再比较 bbox、IoU、path 匹配和人工 overlay；如果 90 度旋转能解决大半错位，优先修方向归一化/对照渲染，再进入局部轮廓优化。 |
| 结构指标已经 `mvp-pass`，但整体 overlay 一眼看出布局方向不一致。 | 把 object count、path count、line count 通过当成几何已经接近 reference。 | 结构通过只代表对象数量和类型接近；必须同时检查整体 overlay 和 per-piece overlay，先排除页面方向、坐标轴方向、viewBox 归一化、旋转/镜像问题。 |
