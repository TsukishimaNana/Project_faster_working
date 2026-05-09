# PatternRefine 开发使用的 Skills

## 已引用的本地 Skills

- `pdf`：用于 PDF 检查、渲染、抽取和 OCR 规划。
- `doc-coauthoring`：作为 spec 和 task 文档工作流参考。
- `find-skills`：用于搜索 PDF/OCR 和规划相关 skills。
- `skill-installer`：用于安装额外 skills。

## 候选 PDF/OCR Skills

skill 搜索识别出以下相关候选：

- `yejinlei/pdf-ocr-skill@pdf-ocr-skill` - installed to
  `~/.agents/skills/pdf-ocr-skill`
- `claude-office-skills/skills@pdf-ocr-extraction`

这些是开发期 skills，不替代 runtime dependencies，例如 PyMuPDF、OpenCV、potrace/vtracer 或 Tesseract。

安装新 skill 后，需要重启 Codex 才能在 available skills list 中看到并触发使用。
