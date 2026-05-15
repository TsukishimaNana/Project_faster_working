# Current Slice

Purpose: compact context for the next implementation batch. Prefer this file over rereading full
Handoff/OpenSpec when assigning a narrow subtask.

## Route

- Current MVP route: reference-guided production reconstruction.
- Customer deliverable: `*.final.svg`.
- Scan-only centerline remains diagnostic/future-generalization only.
- Source/reference directory is read-only: `knowledge_base/PDF-SVG/Original_PinkShirts`.

## Current Status

- `pink-dress-simple-reference.svg` is loaded read-only as the production geometry template.
- `refine_pdf()` writes reference-guided `final.svg` for `pink-dress-original-scan.pdf`.
- Final status report includes `geometry_source=reference-guided`.
- Full validation last known: `pytest -q` 88 passed, `ruff check .` passed, `npm run spec:validate` passed.

## Active Batch

1. Wire final SVG piece acceptance into pipeline final-status/report.
2. Keep scan render, scale marker, orientation, and overlay diagnostics alive.
3. Add scan-only vs reference-guided difference reporting.

## Dispatch Rule

Do not fork full conversation context for subagents. Send a 30-60 line compressed dispatch packet
with route, task, write scope, read scope, allowed commands, validation, and return format.
