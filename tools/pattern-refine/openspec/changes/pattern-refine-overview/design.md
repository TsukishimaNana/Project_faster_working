# Design Notes

PatternRefine 作为一个小工具项目组织，Python 和 OpenSpec 各自负责不同关注点。

Python 负责 processing 和 export code。OpenSpec 负责 project intent、change history、acceptance criteria 和 implementation task breakdowns。

父级 `.codex` 目录保持为 workspace-level configuration。Skills 只在文档中引用，不复制进本项目。
