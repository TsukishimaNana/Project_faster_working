# Handoff

Purpose: let a new PatternRefine session take over quickly. Keep this file short. Longer context
lives in `docs/handoff-details.md`; current batch context lives in `CURRENT_SLICE.md`.

## Startup Prompt

```text
Work in `D:\my_project\Project_faster_working\tools\pattern-refine`.
Read `Handoff.md`, `CURRENT_SLICE.md`, `agents.md`, and the active OpenSpec tasks before changing files.
Report route level, current OpenSpec phase, smallest task batch, risks, and whether the work stays on the reference-guided route.
Use compressed dispatch packets for subagents; do not fork full conversation context.
```

## Minimal Read Set

1. `CURRENT_SLICE.md`
2. `agents.md`
3. `openspec\changes\pdf-to-refined-vector-pdf-mvp\tasks.md`
4. `openspec\changes\pdf-to-refined-vector-pdf-mvp\design.md`

Use `docs\handoff-details.md` only if this short handoff is insufficient.

## Current State

- Current sample MVP route: reference-guided production reconstruction.
- Customer deliverable: `*.final.svg`; PDF/debug SVG/report files are internal evidence.
- `pink-dress-simple-reference.svg` is loaded read-only as the production geometry template.
- `refine_pdf()` now writes reference-guided `final.svg` for `pink-dress-original-scan.pdf`.
- Final status report includes `geometry_source=reference-guided`.
- Scan-only centerline remains diagnostic; latest known scan-only max deviation was about `2.05mm`.
- Reference-guided final SVG piece acceptance passes in tests with max deviation about `0.122mm`.
- Pipeline `delivery_ready` still needs to consume piece acceptance directly before declaring MVP deliverable.

## Recent Validation

- `.\.venv\Scripts\python.exe -m pytest -q` -> `88 passed`
- `.\.venv\Scripts\python.exe -m ruff check .` -> passed
- `npm run spec:validate` -> 3 changes passed

For Windows Temp permission issues:

```powershell
New-Item -ItemType Directory -Force .pytest-tmp | Out-Null
$env:TEMP = (Resolve-Path .pytest-tmp).Path
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

## Next Steps

1. Wire final SVG piece acceptance into pipeline final-status/report.
2. Keep scan render, scale marker, orientation, and overlay diagnostics alive.
3. Add scan-only vs reference-guided difference reporting.
4. Only mark deliverable MVP when final-status/report and per-piece `0.2mm` evidence agree.

## Context Control

- Run `.\.venv\Scripts\python.exe scripts\context_snapshot.py` for compact status.
- Do not broad-search the whole repo unless necessary.
- Keep generated outputs out of Git.
