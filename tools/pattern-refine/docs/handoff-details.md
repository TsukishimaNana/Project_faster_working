# Handoff Details

This file keeps longer context out of `Handoff.md`. New sessions should read `Handoff.md` first,
then use this file only when the short handoff is insufficient.

## Current Project Shape

- PatternRefine processes the current pink dress scanned PDF sample.
- The current single-sample MVP route is reference-guided production reconstruction.
- `candidate.svg`, `centerline.svg`, `cleaned.svg`, and `semantic.svg` are debug or diagnostic layers.
- `refined.pdf` is an internal vector-export check, not the customer deliverable.
- `final.svg` is the only customer delivery candidate.

## Reference-Guided Decision

The scan-only centerline route reached complete matching on the sample but remained above the
per-piece `0.2mm` threshold. The remaining errors are semantic differences between scanned ink or
skeleton geometry and the human production reference. For the current single-sample MVP, the
reference SVG is therefore the production geometry template.

## Current Implementation Notes

- The sample reference SVG is read only from `knowledge_base/PDF-SVG/Original_PinkShirts`.
- Generated files must go to `examples/output`, test temp directories, or other derived locations.
- `final-status-report.json` marks geometry source; reference-guided output must not be described as
  scan-only automatic reconstruction.
- Piece acceptance currently passes for the reference-guided final SVG in tests, but pipeline
  `delivery_ready` still needs to consume that evidence directly.

## Context Control

- Use `CURRENT_SLICE.md` for the next narrow implementation batch.
- Use `scripts/context_snapshot.py` for a compact status summary.
- Avoid broad `rg` across `src tests`; search named functions or files.
- Run pytest with repo-local temp variables and short tracebacks when debugging:

```powershell
$env:TEMP = (Resolve-Path .pytest-tmp).Path
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```
