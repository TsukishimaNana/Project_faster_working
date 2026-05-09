# PatternRefine Agent Instructions

本文件是 PatternRefine 项目专用规则。也需要遵守个人全局配置：

```text
..\..\.codex\AGENTS.md
```

如果规则冲突，本文件优先约束 PatternRefine 的项目安全和 source-of-truth；个人配置优先约束沟通偏好。

## 项目目标

PatternRefine 用于将扫描型 BJD 纸样 PDF 处理成更干净的矢量输出。第一版 MVP 聚焦线稿清理、关键特征保护圆顺和矢量 PDF 导出。
SVG 是内部/调试格式，不是最终产品边界。

## 当前技术栈

- Python package：`src\pattern_refine`
- OpenSpec：`openspec\`
- 本地 Node 20：通过 npm `node` dev dependency
- 本地 Python virtual environment：`.venv`

## 项目目录结构

```text
tools\pattern-refine\
  Handoff.md                 # 新会话接手摘要
  agents.md                  # 本项目 agent 规则
  README.md                  # 项目说明和常用命令
  pyproject.toml             # Python 包和依赖声明
  package.json               # OpenSpec/Node tooling
  src\pattern_refine\        # Python 源码
  tests\                     # 自动化测试
  openspec\                  # OpenSpec 项目、changes、requirements
  docs\                      # 补充说明和技能记录
  assets\fonts\              # 可选字体资产；需要中文 PDF 文字时使用
  examples\input\            # 可放非原始、可复现的输入示例
  examples\output\           # 生成物、调试图、临时对比输出
  knowledge_base\PDF-SVG\
    Original_PinkShirts\     # 用户原始/参考文件，只读
```

## 输出和生成物规则

- `Original_PinkShirts` 只读；任何派生图片、SVG、PDF、报告都不能写进去。
- MVP 默认输出目录优先使用 `examples\output\`。
- 后续如生成较多分析材料，可新增 `knowledge_base\derived\...`，但必须与 `Original_*` 原始目录分离。
- 推荐输出命名：
  - `pink-dress-page-001-render.png`
  - `pink-dress-page-001-lines.png`
  - `pink-dress.cleaned.svg`
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
- 扫描 PDF 转图片后必须建立 pixel-to-mm 校准；优先参考 PDF 上的厘米尺/英寸尺，其次参考已知 1:1 SVG/DXF。
- 当前参考 SVG/DXF 按用户判断视为 1:1，可用于校准和对比，但不要写回原始目录。
- 当前参考 SVG 样式不复杂；MVP 优先从 refined geometry 直接绘制 PDF，SVG 转 PDF 只作为对照或 fallback。
- 如需中文文字输出，使用 `assets\fonts\NotoSansSC-VF.ttf`，并在 PDF 中显式嵌入字体；不要依赖系统字体路径。

## 几何和验证规则

- 纸样路径必须能解释为真实 mm 几何；禁止混用 mm、px、pt 而不记录换算。
- 闭合裁片路径必须显式验证闭合；开路径、辅助线、比例尺、文字箭头不要混进主轮廓。
- 几何不合法时应失败并给出原因，不要静默输出空文件或残缺纸样。
- 比例尺和 1:1 输出不能只靠肉眼判断；必须能用已知厘米尺/英寸尺、SVG/DXF 参考或报告验证。
- 调试叠图、辅助线、OCR 文字层和最终导出层必须分离，避免把调试表达混入供应商交付物。
- 对称或重复裁片后续应通过数量/标注表达，不要为了视觉排版重复生成不可区分的几何副本。

## 文本文件规范

- 仓库内项目文本文件统一 UTF-8（无 BOM）+ LF。
- 新建或重写中文文档、JSON、SVG、脚本文件时，先确认写入编码。
- 中文相关问题的修复结论应有证据：真实文件编码、读取方式、终端显示方式和修改后验证结果。

## MVP 工作前必读

- `Handoff.md`
- `README.md`
- `docs\development-notes.md`
- `docs\skills.md`
- `openspec\project.md`
- `openspec\changes\pattern-refine-development-roadmap\proposal.md`
- `openspec\changes\pdf-to-refined-vector-pdf-mvp\proposal.md`
- `openspec\changes\pdf-to-refined-vector-pdf-mvp\design.md`
- `openspec\changes\pdf-to-refined-vector-pdf-mvp\tasks.md`

## 原始知识库只读

以下目录包含用户提供的原始/参考文件：

```text
knowledge_base\PDF-SVG\Original_PinkShirts
```

规则：

- 不要编辑此目录内的文件内容。
- 不要覆盖此目录内的文件。
- 不要把文件移出此目录。
- 不要把派生产物生成到此目录。
- 如果需要处理参考文件，只读读取它，并将生成产物写入 `examples\output\` 或命名清晰的 derived 目录。

当前文件：

- `pink-dress-original-scan.pdf`
- `pink-dress-simple-reference.svg`
- `pink-dress-annotated-layout-reference.svg`
- `pink-dress-dxf-reference.dxf`
- `pink-dress-illustrator-reference.ai`

## 中文编码和终端安全

本项目包含中文来源文件名、SVG 文字层和参考文档。编码问题是已知重复错误来源。

规则：

- 除非有反证，所有文本文件按 UTF-8 处理。
- 不要把终端 mojibake 直接判定为文件损坏。
- 重写疑似乱码文件前，先验证源文件 bytes，或用显式 UTF-8 方式读取。
- PowerShell 处理中文路径时，优先使用 `-LiteralPath`、`Get-ChildItem` 返回的对象路径，以及明确支持 UTF-8 的工具。
- 不要手敲乱码中文路径后继续覆盖写入。
- 不要把终端渲染出来的中文文本当成唯一 source-of-truth。
- SVG 输出包含中文文字层时，必须明确保留 UTF-8 XML encoding，并使用支持中文 glyphs 的字体。
- 如果未来 PDF 输出包含中文文本，必须嵌入支持中文的字体，不依赖查看器默认字体。

## 重复错误预防

避免这些错误：

- 混淆 SVG 中间文件和最终交付物。
- 把 OCR 当作第一版 geometry MVP 的阻塞项。
- 把生成产物写入原始知识库目录。
- 过度圆顺尖角、剪口、直角、三角标、短对位标或必须保持直线的生产边。
- 忽略 `0.2mm` 默认偏差阈值。
- 把 Illustrator image trace 作为 MVP 的隐藏运行时依赖。
- 假设样例 PDF 包含矢量路径或可抽取文字；当前粉色连衣裙 PDF 是 image-backed。
- 对中文路径/编码问题靠试错修补，而不是先验证 source-of-truth 文件和编码。

## 开发命令

从 `tools\pattern-refine` 运行：

```powershell
npm run spec:list
npm run spec:validate
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

## MVP CLI 契约

第一版命令形态：

```powershell
pattern-refine refine <input.pdf> --out <dir> --dpi 600 --scale auto
```

- 默认不覆盖已有输出；覆盖必须显式传 `--overwrite`。
- 默认输出 render PNG、line PNG、`*.cleaned.svg`、`*.refined.pdf`、`*.deviation-report.json`。
- `--scale auto` 优先使用 PDF 中厘米尺/英寸尺校准；自动失败时应报告原因，并允许后续加入手动校准参数。
- CLI 参数变更会影响测试、Handoff、OpenSpec 和用户使用文档，必须同步更新。

## MVP 依赖版本记录

当前 MVP 环境基线：

- PyMuPDF `1.27.2.3`
- opencv-python `4.13.0`
- numpy `2.4.4`
- Pillow `12.2.0`
- lxml `6.1.0`
- reportlab `4.5.0`
- svgwrite `1.4.3`

## 实现边界

- MVP 工作必须对齐 OpenSpec tasks。
- 范围发生实质变化时，新增或更新 OpenSpec。
- 优先使用确定性的几何和图像处理步骤。
- 生成输出不要写进 source/reference folders。
- 不要把 `.ai` export 加入 MVP。
- 在 refined geometry 质量被接受前，不要加入 DXF/PLT export。
