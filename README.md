# Project_faster_working

`Project_faster_working` 是个人工作流加速工具集合。每个工具应作为独立小项目放在 `tools/<tool-name>` 下，避免把不同用途的脚本、样例和配置混在根目录。

## 当前内容

```text
tools/
  pattern-refine/          # BJD 纸样 PDF 清理、圆顺和矢量 PDF 导出工具
.codex/
  AGENTS.md                # 个人全局偏好和文档语言策略
  skill-backups/
    tool-project-bootstrap/ # 新工具项目搭建 skill 的 Git 备份源
```

## 工具项目约定

- 新工具优先放在 `tools/<tool-name>`。
- 每个工具项目应有自己的 `README.md`、`Handoff.md`、`agents.md`、`docs/` 和 `openspec/`。
- 面向人读的文档使用“中文主体 + English identifiers”。
- 原始资料目录必须只读；生成物必须写入 `examples/output/` 或明确的 derived 目录。
- 不移动工作区 `.codex`；工具项目只引用个人配置和 skills。

## Skill 备份和同步

全局可用 skill 位于：

```text
C:\Users\Administrator\.codex\skills\tool-project-bootstrap
```

本仓库备份源位于：

```text
.codex\skill-backups\tool-project-bootstrap
```

建议以后先修改仓库内备份源，验证后再同步到全局 skills 目录。新安装或同步后的 skill 通常需要重启 Codex 才会出现在可用列表中。

注意：`.codex\skills\` 是本机安装的外部 skills 集合，包含嵌入 Git 和第三方资源，不纳入本仓库；本仓库只备份 `.codex\skill-backups\tool-project-bootstrap`。

## Git 上传规范

上传前检查：

1. 确认是否已经 `git init` 并设置远端仓库。
2. 检查 `git status --short`，区分本次改动和历史/无关改动。
3. 不提交虚拟环境、依赖目录、缓存、生成输出或临时文件。
4. 不提交 `.env`、密钥、token、账号配置。
5. 对每个工具项目运行它自己的验证命令。
6. 对 OpenSpec 项目运行 `npm run spec:validate`。
7. 只在用户明确要求“上传 Git 仓库 / push”时执行 `git push`。

推荐 commit message 使用英文：

```text
type(scope): description
```

示例：

```text
docs(workspace): add project bootstrap skill backup
feat(pattern-refine): scaffold pdf refinement mvp
```

## 当前验证入口

PatternRefine：

```powershell
cd tools\pattern-refine
npm run spec:validate
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```
