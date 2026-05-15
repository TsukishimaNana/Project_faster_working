from pathlib import Path
from xml.etree import ElementTree

from pattern_refine.compare import (
    write_failed_piece_comparison,
    write_matched_piece_comparison_from_diagnostics,
    write_piece_comparison,
    write_svg_comparison,
)
from pattern_refine.geometry import PathGeometry, Point
from pattern_refine.semantic import CenterlinePieceDiagnostic


def test_write_svg_comparison_outputs_review_panels(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
  <path d="M 1 1 L 10 1 L 10 10 Z" />
  <line x1="1" y1="12" x2="10" y2="12" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path class="st0" d="M 2 2 L 20 2 L 20 20 Z" />
  <rect x="2" y="24" width="18" height="4" />
</svg>
""",
        encoding="utf-8",
    )
    output = tmp_path / "comparison.svg"

    write_svg_comparison(candidate, reference, output)

    root = ElementTree.parse(output).getroot()
    assert root.attrib["viewBox"] == "0 0 1200 520"
    assert "Candidate" in output.read_text(encoding="utf-8")
    assert "Reference" in output.read_text(encoding="utf-8")
    assert "Overlay" in output.read_text(encoding="utf-8")
    assert len(root.findall(".//{http://www.w3.org/2000/svg}path")) == 4


def test_write_piece_comparison_outputs_matched_piece_overlays(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10 10 L 40 10 L 40 40 L 10 40 Z" />
  <path d="M 60 10 L 80 10 L 80 40 L 60 40 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <path d="M 20 20 L 80 20 L 80 80 L 20 80 Z" />
  <path d="M 120 20 L 160 20 L 160 80 L 120 80 Z" />
</svg>
""",
        encoding="utf-8",
    )
    output = tmp_path / "pieces.svg"

    write_piece_comparison(candidate, reference, output)

    text = output.read_text(encoding="utf-8")
    assert "Per-Piece Overlay" in text
    assert "matches=2" in text
    assert "C1 vs R1" in text


def test_write_piece_comparison_marks_failed_piece_metrics(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10.3 10 L 40.3 10 L 40.3 40 L 10.3 40 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10 10 L 40 10 L 40 40 L 10 40 Z" />
</svg>
""",
        encoding="utf-8",
    )
    output = tmp_path / "pieces.svg"

    write_piece_comparison(candidate, reference, output)

    text = output.read_text(encoding="utf-8")
    assert "status=FAIL" in text
    assert "max 0.300mm" in text


def test_write_failed_piece_comparison_outputs_only_failed_and_unmatched_panels(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10.3 10 L 40.3 10 L 40.3 40 L 10.3 40 Z" />
  <path d="M 70 70 L 80 70 L 80 80 L 70 80 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10 10 L 40 10 L 40 40 L 10 40 Z" />
  <path d="M 5 70 L 15 70 L 15 80 L 5 80 Z" />
</svg>
""",
        encoding="utf-8",
    )
    output = tmp_path / "failed-pieces.svg"

    write_failed_piece_comparison(candidate, reference, output, tolerance_mm=0.2)

    text = output.read_text(encoding="utf-8")
    assert "Failed Piece Overlay" in text
    assert "failed panels=3" in text
    assert "over-tolerance C1 vs R1 max 0.300mm" in text
    assert "unmatched-candidate C2" in text
    assert "unmatched-reference R2" in text


def test_write_matched_piece_comparison_from_diagnostics_outputs_only_matched_panels(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" />', encoding="utf-8")
    reference.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" />', encoding="utf-8")
    diagnostics = (
        CenterlinePieceDiagnostic(
            reference_index=1,
            reference_area_mm2=900.0,
            reference_perimeter_mm=120.0,
            matched=True,
            source="component-hull",
            score=1.02,
            candidate_area_mm2=910.0,
            candidate_perimeter_mm=118.0,
            candidate_bounds_mm=(10.0, 10.0, 40.0, 40.0),
            reference_bounds_mm=(12.0, 12.0, 42.0, 42.0),
            candidate_geometry=PathGeometry(
                points=(
                    Point(10.0, 10.0),
                    Point(40.0, 10.0),
                    Point(40.0, 40.0),
                    Point(10.0, 40.0),
                ),
                closed=True,
            ),
            reference_geometry=PathGeometry(
                points=(
                    Point(12.0, 12.0),
                    Point(42.0, 12.0),
                    Point(42.0, 42.0),
                    Point(12.0, 42.0),
                ),
                closed=True,
            ),
        ),
        CenterlinePieceDiagnostic(
            reference_index=2,
            reference_area_mm2=500.0,
            reference_perimeter_mm=100.0,
            matched=False,
            source=None,
            score=None,
            candidate_area_mm2=None,
            candidate_perimeter_mm=None,
            candidate_bounds_mm=None,
            reference_bounds_mm=(50.0, 50.0, 70.0, 70.0),
            candidate_geometry=None,
            reference_geometry=PathGeometry(
                points=(
                    Point(50.0, 50.0),
                    Point(70.0, 50.0),
                    Point(70.0, 70.0),
                    Point(50.0, 70.0),
                ),
                closed=True,
            ),
        ),
    )
    output = tmp_path / "matched.svg"

    write_matched_piece_comparison_from_diagnostics(candidate, reference, diagnostics, output)

    text = output.read_text(encoding="utf-8")
    assert "Matched Piece Overlay" in text
    assert "matched diagnostics=1" in text
    assert "R1 source=component-hull score=1.020" in text
    assert "R2" not in text
