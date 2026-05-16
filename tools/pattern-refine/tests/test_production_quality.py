import json
from pathlib import Path

from pattern_refine.production_quality import (
    evaluate_production_quality,
    write_production_quality_report,
)


def test_production_quality_flags_jagged_open_and_overlapping_lines(tmp_path: Path) -> None:
    svg_path = tmp_path / "jagged.final.svg"
    noisy_points = " ".join(
        f"L {10 + index * 0.1:.3f} {10 + (index % 2) * 0.1:.3f}"
        for index in range(140)
    )
    svg_path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path id="path-0001" d="M 10 10 {noisy_points}" />
  <line id="line-0001" x1="5" y1="5" x2="20" y2="5" />
  <line id="line-0002" x1="5.05" y1="5.04" x2="20.05" y2="5.04" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_production_quality(svg_path)

    assert report.accepted is False
    assert report.manual_review_required is True
    assert "jagged_polyline_detected" in report.blockers
    assert "open_or_broken_contour_detected" in report.blockers
    assert "overlapping_lines_detected" in report.blockers
    assert report.max_path_command_count > 120
    assert report.overlapping_segment_pair_count >= 1


def test_write_production_quality_report_writes_machine_readable_json(tmp_path: Path) -> None:
    svg_path = tmp_path / "cleanish.final.svg"
    report_path = tmp_path / "cleanish.production-quality-report.json"
    svg_path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path id="path-0001" d="M 5 5 L 20 5 L 20 20 L 5 20 Z" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_production_quality(svg_path)
    write_production_quality_report(report, report_path)

    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["accepted"] is False
    assert data["manual_review_required"] is True
    assert data["blockers"] == ["manual_production_review_required"]
    assert data["path_count"] == 1
