# Handoff

用途：让新会话在 30 秒内接手 PatternRefine。保持精简；详细决策放在 OpenSpec。

## 接手 Prompt

```text
请在 `D:\my_project\Project_faster_working\tools\pattern-refine` 中工作。
先阅读 `Handoff.md`、`agents.md` 和当前 active OpenSpec changes，再做修改。
先汇报当前状态和风险，然后继续推进 MVP。
```

## 当前工作区

- 路径：`D:\my_project\Project_faster_working\tools\pattern-refine`
- 项目：PatternRefine
- 目标：为扫描型 BJD 纸样 PDF 清理、关键特征保护圆顺、矢量 PDF 导出的 MVP 开发做准备。
- MVP 主要交付物：`*.refined.pdf`
- 调试/中间输出：`*.cleaned.svg`
- 不进入 MVP：桌面 UI、AI 导出、DXF/PLT 导出、完整 OCR 文字提示层重建。

## 当前状态

- 项目骨架已创建在 `tools/pattern-refine`。
- Python 包已包含 `refine` CLI 初版、PDF page render、black-line extraction、初始主轮廓候选 SVG adapter 和 path geometry parser。
- 本地 Python `.venv` 已创建，并安装 PDF/image/vector 相关依赖。
- OpenSpec scripts 使用本地 Node 20.19.0 dev dependency。
- OpenSpec 当前有三个可验证 changes：
  - `pattern-refine-development-roadmap`
  - `pattern-refine-overview`
  - `pdf-to-refined-vector-pdf-mvp`
- `pdf-ocr-skill` 已安装到 `~\.agents\skills\pdf-ocr-skill`；重启 Codex 后再依赖它出现在可用 skill 列表中。
- 粉色连衣裙参考文件以只读方式存放在 `knowledge_base\PDF-SVG\Original_PinkShirts`。

## 必读文件

- `agents.md`
- `README.md`
- `docs\development-notes.md`
- `docs\skills.md`
- `openspec\project.md`
- `openspec\changes\pattern-refine-development-roadmap\*`
- `openspec\changes\pdf-to-refined-vector-pdf-mvp\*`

## 粉色连衣裙原始参考文件

不要修改此目录中的文件内容：

```text
knowledge_base\PDF-SVG\Original_PinkShirts\
```

当前英文可读文件名：

- `pink-dress-original-scan.pdf`
- `pink-dress-simple-reference.svg`
- `pink-dress-annotated-layout-reference.svg`
- `pink-dress-dxf-reference.dxf`
- `pink-dress-illustrator-reference.ai`

当前验收参考：`pink-dress-simple-reference.svg`。目标是接近其少量对象级 path/line/rect 表达，而不是像素级 tracing。

## 最近验证命令

从 `tools\pattern-refine` 运行：

```powershell
npm run spec:validate
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

最近已知结果：MVP 主轮廓候选切片后全部通过。若系统 Temp 权限异常，pytest 可临时使用项目内 `.tmp`：

```powershell
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = (Resolve-Path .tmp).Path
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest
```

## 下一步 MVP

已完成：

- 只读加载 `pink-dress-original-scan.pdf`。
- 将第一页以 600 DPI 渲染到 `examples\output\pink-dress-original-scan-page-001-render.png`。
- 从白底中提取黑色线稿到 `examples\output\pink-dress-original-scan-page-001-lines.png`。
- 从线稿生成主轮廓候选 `examples\output\pink-dress-original-scan.cleaned.svg`。
- 当前 cleaned SVG 解析得到 86 个 path geometry，已从不可读的 1063 个骨架碎片恢复到可查看候选层，但仍多于 `pink-dress-simple-reference.svg` 的对象级表达。
- 当前 PDF 页面尺寸换算约为 `419.99mm x 297.05mm`。

下一步继续做文字/噪声过滤、主裁片合并和对象级轮廓重建，使 `cleaned.svg` 接近 `pink-dress-simple-reference.svg`；之后再实现 feature classification：corners、notches、right angles、triangle marks、short alignment marks 和 straight edges。文字后续走 OCR 识别候选 + 人工确认映射表，再重建文字层，不作为当前 geometry MVP 阻塞项。

## 当前关键结论

- `pink-dress-simple-reference.svg` 是当前简单验收成果参考，不是 `3cm.svg`；用户已删除 `3cm.svg`。
- `cleaned.svg` 不能是像素级 tracing 结果，应该是对象级纸样 SVG：少量 path/line/rect，能被后续算法继续处理。
- 当前 OpenCV 主轮廓候选版本输出 86 个 path；比 1063 个骨架碎片可读，但仍远多于参考 SVG 的约 `9 path + 10 line + 1 rect`。
- 中心线/骨架化分支已被判断为不适合作为主路线：它让结果变成大量短碎 path，基本看不清。
- `potrace` 或 `vtracer` 可以作为初始 raster-to-vector adapter 评估，但其原始输出不应直接视为最终 `cleaned.svg`。真正核心是后续 object-level geometry reconstruction。
- 推荐流程：OpenCV 预处理 → potrace/vtracer 或 OpenCV tracing 生成候选矢量 → PatternRefine 自己的 geometry post-processing → 对象级 `cleaned.svg` → refined PDF。

## 建议评估方案

下一步优先做 evaluator，而不是继续凭肉眼调参数。建议命令形态：

```powershell
pattern-refine evaluate examples\output\pink-dress-original-scan.cleaned.svg --reference knowledge_base\PDF-SVG\Original_PinkShirts\pink-dress-simple-reference.svg --out examples\output
```

评估维度：

- 结构指标：candidate/reference 的 path、line、rect、closed path、small path 数量。
- 对象匹配：candidate 主轮廓 bbox 是否能匹配 reference 裁片 bbox；记录 matched/unmatched/extra objects。
- 几何偏差：采样 path 后计算 mean/p95/max nearest-neighbor 或 Hausdorff distance，单位 mm。
- 比例尺：检测扫描中的 3cm 尺或 reference 中比例尺，校准 pixel-to-mm。
- 可处理性：是否仍有大量微小 path、文字碎片、孤立点；主轮廓是否闭合。

建议三档结论：

- Fail：看不清、碎 path 太多、主裁片匹配不上。
- Debug Pass：能看出主要裁片，path 数量可控，适合继续做后处理。
- MVP Pass：接近 `pink-dress-simple-reference.svg`，主要裁片匹配，比例尺正确，关键特征保留，可导出 vector PDF。

当前 86-path 版本应视为接近 Debug Pass，但未达 MVP Pass。

## 风险

- 样例 PDF 是 image-backed PDF，不是干净的矢量 PDF。
- 线条圆顺是核心难点；不要过度圆顺尖角、剪口、直角、三角标或短对位标。
- 默认圆顺偏差阈值为 `0.2mm`。
- 即使文件有效，中文终端输出也可能显示乱码；先确认文件 bytes/encoding，再判断是否损坏。
- 如果编码或字体处理不正确，SVG 中文文字层可能乱码。
- 文字层不能从扫描笔画路径直接“提取”作为最终文本；应先 OCR 识别，再由用户确认映射。

## 更新规则

- 保持精简。
- 每个重要里程碑后更新当前状态、最近验证、风险和下一步。
- 不贴长命令输出。
