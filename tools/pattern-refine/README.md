# PatternRefine

PatternRefine 是一个用于加速 BJD 纸样处理的小工具项目：读取扫描型纸样
PDF，先建立页面归一化和扫描证据层，再识别制版特征，用规则化勾线生成干净的
生产级 SVG。

项目放在 `tools/pattern-refine` 下，方便 `Project_faster_working` 以后继续容纳多个工作加速小工具。

## MVP 目标

当前 MVP 聚焦 `pink-dress-original-scan.pdf` 单样本，但路线已从“扫描轮廓矢量化后直接交付”
调整为“扫描证据 + 特征识别 + 规则勾线”：

1. 将 PDF 页面渲染为高分辨率图片。
2. 归一化页面方向、尺寸、viewBox 和单位，建立稳定扫描证据坐标系。
3. 从白底中提取黑色纸样线稿，输出 scan evidence/debug 层。
4. 识别裁片、直边、曲边、尖角、剪口、短对位标、比例尺和非生产噪声。
5. 按制版规则重建少点数、无重合线、可编辑的生产 SVG。
6. 用人工 reference 和合格叠图作为规则样本与验收对照，而不是把扫描轮廓本身当 final。

`pink-dress-simple-reference.svg` 和 `pink-dress-original-scan-SVG-VS-PDF.pdf` 是当前样本的
reference/oracle：它们说明“红色生产线如何从扫描黑线中抽象出来”。扫描提取层只能作为证据，
不能直接升级为生产级 final SVG。

## 输出

- `*.final.svg`：生产级 SVG 候选；必须通过 topology/cleanliness gate 后才能称为可交付。
- `*.piece-acceptance-report.json`：逐裁片几何偏差报告，只能证明接近 reference，不能单独证明生产级。
- `*.final-status-report.json`：最终交付状态，必须同时消费几何验收和生产级 cleanliness/topology 证据。
- `*.candidate.svg` / `*.centerline.svg` / `*.cleaned.svg` / `*.semantic.svg`：扫描证据或诊断层，不能当客户交付物。
- `*.scan-evidence.svg` / `*.feature-report.json`：后续用于表达黑线证据和识别出的制版特征。
- `*.refined.pdf`：内部 vector export 链路检查产物。
- 后续输出：用于激光流程的 DXF 和 PLT。
- 不进入 MVP：Adobe Illustrator `.ai` 导出。

## 工具链

### Python

Python 负责 PDF 渲染、页面归一化、扫描证据提取、特征识别、规则化 SVG 重建和内部 PDF
导出。包入口为：

```powershell
pattern-refine
```

### OpenSpec

OpenSpec 用于管理项目 change 和任务拆解。它要求 Node `20.19.0+`；本项目在 `.nvmrc`、`.node-version`
和 `package.json` 中记录该要求。

使用项目本地 Node 20 runtime，不全局升级系统 Node：

```powershell
npm run node:version
npm run spec:list
npm run spec:validate
```

npm scripts 会显式通过本地 `node` dev dependency 运行 OpenSpec。

### Agent Skills

不要把工作区 `.codex` 目录移动到本项目中。当前开发流程引用父工作区中的这些 skills：

- `pdf`：PDF 检查、抽取、渲染相关指导。
- `doc-coauthoring`：结构化 spec 和 task 文档工作流。

如果 OCR 阶段进入当前里程碑，可以再安装可选 OCR skills。

当前 skill 使用和安装记录见 `docs/skills.md`。

## 开发说明

第一个实现里程碑故意收窄范围：证明当前粉裙扫描 PDF 可以稳定生成页面归一化扫描证据层，
并从中识别足够的制版特征，生成接近 `pink-dress-simple-reference.svg` 风格的干净勾线草稿。
逐裁片 `0.2mm` 几何偏差只能作为辅助指标；生产交付必须增加无重合线、无双边线、拓扑连续、
对象语义清晰和少点数可编辑性验收。
OCR、DXF/PLT 导出和 Illustrator 自动化都是后续扩展。

基础验证命令：

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
npm run spec:validate
```
