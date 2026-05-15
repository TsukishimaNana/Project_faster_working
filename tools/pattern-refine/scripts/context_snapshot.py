"""Print a compact PatternRefine context snapshot for agents."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "openspec" / "changes" / "pdf-to-refined-vector-pdf-mvp" / "tasks.md"
CURRENT_SLICE = ROOT / "CURRENT_SLICE.md"
HANDOFF = ROOT / "Handoff.md"


def main() -> int:
    print("# PatternRefine Context Snapshot")
    print()
    print(f"workdir: {ROOT}")
    print(f"branch: {_git(['branch', '--show-current']) or 'unknown'}")
    print()
    _print_current_slice()
    _print_tasks()
    _print_dirty_summary()
    _print_recent_validation()
    return 0


def _print_current_slice() -> None:
    if not CURRENT_SLICE.exists():
        return
    print("## Current Slice")
    lines = CURRENT_SLICE.read_text(encoding="utf-8").splitlines()
    for line in lines[:80]:
        if line.startswith("# "):
            continue
        print(line)
    print()


def _print_tasks() -> None:
    if not TASKS.exists():
        return
    print("## Active OpenSpec Tasks")
    pending: list[str] = []
    completed = 0
    total = 0
    for line in TASKS.read_text(encoding="utf-8").splitlines():
        if line.startswith("- ["):
            total += 1
            if line.startswith("- [x]"):
                completed += 1
            elif len(pending) < 8:
                pending.append(line)
    print(f"progress: {completed}/{total}")
    for line in pending:
        print(line)
    print()


def _print_dirty_summary() -> None:
    print("## Git Dirty Summary")
    status = _git(["status", "--short", "--", "."])
    if not status:
        print("clean")
        print()
        return
    lines = status.splitlines()
    print(f"dirty_entries_in_pattern_refine: {len(lines)}")
    for line in lines[:30]:
        print(line)
    if len(lines) > 30:
        print(f"... {len(lines) - 30} more")
    print()


def _print_recent_validation() -> None:
    if not HANDOFF.exists():
        return
    print("## Recent Validation")
    text = HANDOFF.read_text(encoding="utf-8")
    match = re.search(r"## 最近验证\n(?P<body>.*?)(?:\n## |\Z)", text, re.S)
    if not match:
        return
    for line in match.group("body").strip().splitlines()[:20]:
        print(line)


def _git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return ""
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
