# PatternRefine

PatternRefine 是一个用于加速 BJD 纸样处理的小工具项目：清理扫描型纸样
PDF、圆顺线条、保护关键纸样特征，并导出供应商可用的矢量 PDF。

项目放在 `tools/pattern-refine` 下，方便 `Project_faster_working` 以后继续容纳多个工作加速小工具。

## MVP 目标

第一版 MVP 聚焦扫描型 BJD 纸样 PDF：

1. 将 PDF 页面渲染为高分辨率图片。
2. 从白底中提取黑色纸样线稿。
3. 将清理后的线稿矢量化为内部 SVG。
4. 在保留尖角、剪口、直角、三角标等关键特征的前提下圆顺和简化路径。
5. 导出矢量 PDF 作为主要交付物。

SVG 是中间格式和调试格式，不是最终产品边界。

## 输出

- `*.cleaned.svg`：内部/调试用矢量表示。
- `*.refined.pdf`：MVP 主要输出，用于供应商查看和交付。
- 后续输出：用于激光流程的 DXF 和 PLT。
- 不进入 MVP：Adobe Illustrator `.ai` 导出。

## 工具链

### Python

Python 负责 PDF 渲染、图像清理、矢量处理和 PDF 导出。包入口为：

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

第一个实现里程碑故意收窄范围：证明一个扫描型 PDF 可以变成更圆顺的矢量 PDF，且不会破坏关键纸样特征。
OCR、DXF/PLT 导出和 Illustrator 自动化都是后续扩展。

基础验证命令：

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
npm run spec:validate
```
