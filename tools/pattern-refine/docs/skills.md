# PatternRefine 开发使用的 Skills

## 已引用的本地 Skills

- `pdf`：用于 PDF 检查、渲染、抽取和 OCR 规划。
- `doc-coauthoring`：作为 spec 和 task 文档工作流参考。
- `find-skills`：用于搜索 PDF/OCR 和规划相关 skills。
- `skill-installer`：用于安装额外 skills。

## 父工作区 OpenSpec Skills

以下 OpenSpec skills 位于父工作区 `D:\my_project\Project_faster_working\.codex\skills\`，PatternRefine 只引用，不复制到本项目：

- `openspec-explore`：用于只读探索 OpenSpec 上下文和现有 change。
- `openspec-propose`：用于创建或补全 OpenSpec proposal/design/specs/tasks。
- `openspec-apply-change`：用于按 OpenSpec tasks 推进实现。
- `openspec-archive-change`：用于完成后归档 OpenSpec change。

## 候选 PDF/OCR Skills

skill 搜索识别出以下相关候选：

- `yejinlei/pdf-ocr-skill@pdf-ocr-skill` - installed to
  `~/.agents/skills/pdf-ocr-skill`
- `claude-office-skills/skills@pdf-ocr-extraction`

这些是开发期 skills，不替代 runtime dependencies，例如 PyMuPDF、OpenCV、potrace/vtracer 或 Tesseract。

安装新 skill 后，需要重启 Codex 才能在 available skills list 中看到并触发使用。

## 后续 OCR Runtime 候选

文字识别属于 Annotation Assist，不进入当前 geometry MVP runtime。后续应实测以下候选：

- Tesseract OCR + `chi_sim`/`chi_tra` traineddata：本地、开源、集成简单；对清晰印刷体较稳，对手写中文和旋转小字可能弱。
- PaddleOCR：中文 OCR 能力强，包含检测和识别 pipeline；依赖更重，但更适合复杂中文场景。
- RapidOCR：偏轻量的 ONNXRuntime OCR 方案，部署可能比完整 PaddleOCR 简单。
- EasyOCR：上手简单，支持中文；需要对当前纸样手写标注做实际准确率验证。

推荐后续流程不是把文字矢量路径直接提取为最终文字，而是：

1. OCR 输出候选文本、置信度、位置、方向和关联裁片候选。
2. 用户在确认表单中修正候选，并建立标准化映射。
3. 最终 PDF/SVG 文字层从确认后的映射重建，使用项目内中文字体。
