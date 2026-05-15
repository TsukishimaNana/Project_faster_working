import json
from pathlib import Path
import sys

from pattern_refine.cli import build_parser, main


def test_cli_parser_accepts_version_flag() -> None:
    parser = build_parser()

    args = parser.parse_args(["--version"])

    assert args.version is True


def test_cli_parser_accepts_refine_command() -> None:
    parser = build_parser()

    args = parser.parse_args(["refine", "input.pdf", "--out", "out"])

    assert args.command == "refine"
    assert args.dpi == 600
    assert args.scale == "auto"
    assert args.overwrite is False


def test_cli_parser_accepts_evaluate_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "evaluate",
            "candidate.svg",
            "--reference",
            "reference.svg",
            "--out",
            "out",
        ]
    )

    assert args.command == "evaluate"
    assert args.candidate_svg.name == "candidate.svg"
    assert args.reference.name == "reference.svg"
    assert args.out.name == "out"
    assert args.overwrite is False


def test_cli_evaluate_writes_piece_acceptance_report(tmp_path: Path, monkeypatch) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    out_dir = tmp_path / "out"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path d="M 5 5 L 20 5 L 20 20 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 113.385827 113.385827">
  <path d="M 14.173228 14.173228 L 56.692913 14.173228 L 56.692913 56.692913 Z" />
  <path d="M 85.039370 85.039370 L 99.212598 85.039370 L 99.212598 99.212598 Z" />
</svg>
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pattern-refine",
            "evaluate",
            str(candidate),
            "--reference",
            str(reference),
            "--out",
            str(out_dir),
        ],
    )

    assert main() == 0
    report_path = out_dir / "candidate.piece-acceptance-report.json"
    failed_overlay_path = out_dir / "candidate.failed-pieces-comparison.svg"
    assert report_path.exists()
    assert failed_overlay_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["matched_piece_count"] == 1
    assert report["accepted"] is False
    assert report["failed_piece_details"][0]["failure_type"] == "unmatched-reference"
