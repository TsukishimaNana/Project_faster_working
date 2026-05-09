# Language Policy

Use “中文主体 + English identifiers”.

## Rules

- Human-facing project docs should be mostly Chinese.
- Keep technical identifiers in English:
  - paths
  - package names
  - commands
  - CLI flags
  - function/class/module names
  - OpenSpec change ids
  - Requirement and Scenario labels
  - output suffixes
- OpenSpec prose may be mixed Chinese/English.
- OpenSpec requirement bodies must keep `SHALL` or `MUST`.
- High-risk rules must be written clearly in Chinese:
  - original files are read-only
  - source-of-truth rules
  - encoding/terminal mojibake rules
  - output directory rules
  - unit conversion rules
  - non-goals and implementation red lines

## Default Tone

Keep docs practical and short. Avoid generic filler. Write enough for a future
agent to execute safely without asking the user to repeat known preferences.
