---
name: tool-project-bootstrap
description: Bootstrap personal workflow tool projects inside an existing workspace. Use when the user wants to create a new small tool project, scaffold a tools/name project, set up OpenSpec roadmap/overview/MVP changes, generate Handoff.md and agents.md, establish read-only source material rules, define output directories, document CLI contracts, or reuse the PatternRefine-style project setup workflow.
---

# Tool Project Bootstrap

Use this skill to create or plan a new personal workflow tool project. Optimize
for projects that live under a larger workspace, commonly as `tools/<tool-name>`,
and need strong handoff, source-of-truth, and OpenSpec discipline.

## Core Workflow

1. Confirm or infer the project boundary:
   - display name
   - directory name
   - parent workspace
   - MVP goal
   - primary output
   - debug/intermediate outputs
   - non-goals
   - read-only source/reference directories
2. Use “中文主体 + English identifiers” for documentation.
3. Prefer `tools/<tool-name>` unless the user asks for another structure.
4. Do not move or copy workspace `.codex`; only reference global/personal rules.
5. Create the standard project structure from `references/standard-structure.md`.
6. Generate `Handoff.md` from `references/handoff-template.md`.
7. Generate project `agents.md` from `references/agents-template.md`.
8. Create OpenSpec content using `references/openspec-change-pattern.md`.
9. Record validation commands and environment/version facts.
10. Run available validation and update Handoff with the result.

## Required Project Documents

Every bootstrapped tool project should include:

- `README.md`: concise project purpose, MVP goal, commands.
- `Handoff.md`: short resume state for the next session.
- `agents.md`: project-specific agent rules and red lines.
- `docs/`: supplemental notes such as skills, dependencies, and decisions.
- `openspec/`: roadmap, overview, and first MVP change.

Read the relevant templates before writing these files:

- `references/agents-template.md`
- `references/handoff-template.md`
- `references/openspec-change-pattern.md`
- `references/standard-structure.md`
- `references/language-policy.md`

## OpenSpec Pattern

Create three changes unless there is a clear reason not to:

- `<tool-name>-development-roadmap`: long-term direction.
- `<tool-name>-overview`: project boundary and setup.
- `<first-mvp-change>`: first concrete implementation milestone.

OpenSpec requirement bodies must include `SHALL` or `MUST`, even when the rest
of the sentence is Chinese.

## Safety Rules

- Keep original/reference material read-only.
- Never generate derived files into original source directories.
- Put generated outputs in `examples/output/` or a clearly named derived folder.
- Write high-risk rules in Chinese.
- Keep machine identifiers, paths, commands, package names, change ids, and file
  extensions in English.
- If adding fonts, binaries, or copied assets, record source and usage policy.

## Validation

After bootstrapping, run what applies:

- OpenSpec validation, for example `npm run spec:validate`.
- Project tests, for example `pytest`.
- Formatter/linter checks, for example `ruff`.
- File existence checks for required docs and read-only source directories.

Summarize results in the final response and update `Handoff.md` if files were
created or changed.
