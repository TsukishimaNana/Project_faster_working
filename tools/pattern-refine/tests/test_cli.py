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


def test_cli_parser_accepts_verify_delivery_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "verify-delivery",
            "sample.final.svg",
            "--status",
            "sample.final-status-report.json",
            "--piece-report",
            "sample.piece-acceptance-report.json",
            "--production-quality-report",
            "sample.production-quality-report.json",
        ]
    )

    assert args.command == "verify-delivery"
    assert args.final_svg.name == "sample.final.svg"
    assert args.status.name == "sample.final-status-report.json"
    assert args.piece_report.name == "sample.piece-acceptance-report.json"
    assert args.production_quality_report.name == "sample.production-quality-report.json"


def test_cli_parser_accepts_production_quality_command() -> None:
    parser = build_parser()

    args = parser.parse_args(["production-quality", "sample.final.svg", "--out", "out"])

    assert args.command == "production-quality"
    assert args.input_svg.name == "sample.final.svg"
    assert args.out.name == "out"
    assert args.overwrite is False


def test_cli_verify_delivery_passes_ready_reference_guided_reports(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    final_svg = tmp_path / "sample.final.svg"
    status_report = tmp_path / "sample.final-status-report.json"
    piece_report = tmp_path / "sample.piece-acceptance-report.json"
    production_quality_report = tmp_path / "sample.production-quality-report.json"
    final_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" />', encoding="utf-8")
    status_report.write_text(
        json.dumps({"geometry_source": "reference-guided", "delivery_ready": True}),
        encoding="utf-8",
    )
    piece_report.write_text(
        json.dumps(
            {
                "accepted": True,
                "max_deviation_mm": 0.122,
                "failed_reference_piece_indices": [],
                "unmatched_reference_piece_indices": [],
            }
        ),
        encoding="utf-8",
    )
    production_quality_report.write_text(
        json.dumps({"accepted": True, "blockers": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pattern-refine",
            "verify-delivery",
            str(final_svg),
            "--status",
            str(status_report),
            "--piece-report",
            str(piece_report),
            "--production-quality-report",
            str(production_quality_report),
        ],
    )

    assert main() == 0
    output = capsys.readouterr().out
    assert "STATUS: PASS" in output
    assert "GEOMETRY_SOURCE: reference-guided" in output
    assert "PRODUCTION_QUALITY_ACCEPTED: True" in output
    assert "MAX_DEVIATION_MM: 0.122" in output


def test_cli_verify_delivery_fails_when_piece_report_exceeds_tolerance(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    final_svg = tmp_path / "sample.final.svg"
    status_report = tmp_path / "sample.final-status-report.json"
    piece_report = tmp_path / "sample.piece-acceptance-report.json"
    production_quality_report = tmp_path / "sample.production-quality-report.json"
    final_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" />', encoding="utf-8")
    status_report.write_text(
        json.dumps({"geometry_source": "reference-guided", "delivery_ready": True}),
        encoding="utf-8",
    )
    piece_report.write_text(
        json.dumps(
            {
                "accepted": False,
                "max_deviation_mm": 0.25,
                "failed_reference_piece_indices": [3],
                "unmatched_reference_piece_indices": [],
            }
        ),
        encoding="utf-8",
    )
    production_quality_report.write_text(
        json.dumps({"accepted": True, "blockers": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pattern-refine",
            "verify-delivery",
            str(final_svg),
            "--status",
            str(status_report),
            "--piece-report",
            str(piece_report),
            "--production-quality-report",
            str(production_quality_report),
        ],
    )

    assert main() == 1
    output = capsys.readouterr().out
    assert "STATUS: FAIL" in output
    assert "piece acceptance max_deviation_mm" in output
    assert "FAILED_PIECES: [3]" in output


def test_cli_verify_delivery_fails_when_production_quality_blocks(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    final_svg = tmp_path / "sample.final.svg"
    status_report = tmp_path / "sample.final-status-report.json"
    piece_report = tmp_path / "sample.piece-acceptance-report.json"
    production_quality_report = tmp_path / "sample.production-quality-report.json"
    final_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" />', encoding="utf-8")
    status_report.write_text(
        json.dumps({"geometry_source": "reference-guided", "delivery_ready": True}),
        encoding="utf-8",
    )
    piece_report.write_text(
        json.dumps(
            {
                "accepted": True,
                "max_deviation_mm": 0.122,
                "failed_reference_piece_indices": [],
                "unmatched_reference_piece_indices": [],
            }
        ),
        encoding="utf-8",
    )
    production_quality_report.write_text(
        json.dumps({"accepted": False, "blockers": ["jagged_polyline_detected"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pattern-refine",
            "verify-delivery",
            str(final_svg),
            "--status",
            str(status_report),
            "--piece-report",
            str(piece_report),
            "--production-quality-report",
            str(production_quality_report),
        ],
    )

    assert main() == 1
    output = capsys.readouterr().out
    assert "STATUS: FAIL" in output
    assert "PRODUCTION_QUALITY_ACCEPTED: False" in output
    assert "production quality blockers are not empty" in output


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
