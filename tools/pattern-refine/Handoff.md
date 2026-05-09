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
- Python 包骨架已存在，包含占位 CLI 和 pytest 覆盖。
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

## 最近验证命令

从 `tools\pattern-refine` 运行：

```powershell
npm run spec:validate
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

最近已知结果：项目骨架和 OpenSpec 搭建后全部通过。

## 下一步 MVP

开始实现第一条纵向切片：

1. 只读加载 `pink-dress-original-scan.pdf`。
2. 将第一页渲染到生成输出目录中的高分辨率图片。
3. 从白底中提取黑色线稿。
4. 生成第一个用于对比的调试产物。

生成产物必须放在 `Original_PinkShirts` 外，例如 `examples\output\` 或未来的 derived knowledge-base 目录。

## 风险

- 样例 PDF 是 image-backed PDF，不是干净的矢量 PDF。
- 线条圆顺是核心难点；不要过度圆顺尖角、剪口、直角、三角标或短对位标。
- 默认圆顺偏差阈值为 `0.2mm`。
- 即使文件有效，中文终端输出也可能显示乱码；先确认文件 bytes/encoding，再判断是否损坏。
- 如果编码或字体处理不正确，SVG 中文文字层可能乱码。

## 更新规则

- 保持精简。
- 每个重要里程碑后更新当前状态、最近验证、风险和下一步。
- 不贴长命令输出。
