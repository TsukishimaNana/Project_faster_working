from pathlib import Path

import pytest

from pattern_refine.evaluate import (
    collect_svg_structure_metrics,
    evaluate_svg_piece_acceptance,
    evaluate_svg_shape,
    evaluate_svg_structure,
    write_svg_evaluation_report,
    write_svg_piece_acceptance_report,
    write_svg_shape_evaluation_report,
)


def test_collect_svg_structure_metrics_counts_object_types(tmp_path: Path) -> None:
    svg = tmp_path / "sample.svg"
    svg.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
  <path d="M 1 1 L 10 1 L 10 10 Z" />
  <path d="M 12 1 C 13 2 14 2 15 1" />
  <path d="M 5 5 c 2 0 3 1 4 3" />
  <line x1="0" y1="0" x2="0" y2="5" />
  <rect x="2" y="2" width="1" height="1" />
</svg>
""",
        encoding="utf-8",
    )

    metrics = collect_svg_structure_metrics(svg)

    assert metrics.object_count == 5
    assert metrics.path_count == 3
    assert metrics.closed_path_count == 1
    assert metrics.curved_path_count == 2
    assert metrics.line_count == 1
    assert metrics.rect_count == 1
    assert metrics.small_object_count == 1
    assert metrics.bbox == pytest.approx((0.0, 0.0, 15.0, 10.0))


def test_evaluate_svg_structure_reports_candidate_reference_delta(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M 0 0 L 10 0 L 10 10 Z" />
  <path d="M 20 0 L 30 0 L 30 10 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M 0 0 C 5 2 8 4 10 10 Z" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_svg_structure(candidate, reference)
    report_path = tmp_path / "report.json"
    write_svg_evaluation_report(report, report_path)

    assert report.candidate.object_count == 2
    assert report.reference.object_count == 1
    assert report.object_count_delta == 1
    assert report.path_count_delta == 1
    assert report.object_type_deltas["path"] == 1
    assert report.candidate_to_reference_object_ratio == pytest.approx(2.0)
    assert not report.mvp_ready
    assert report.mvp_blockers
    assert report.verdict == "debug-pass"
    assert '"object_count_delta": 1' in report_path.read_text(encoding="utf-8")


def test_evaluate_svg_structure_requires_similar_object_types_for_mvp(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M 0 0 L 10 0 L 10 10 Z" />
  <path d="M 20 0 L 30 0 L 30 10 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
  <line x1="0" y1="0" x2="10" y2="0" />
  <line x1="0" y1="10" x2="10" y2="10" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_svg_structure(candidate, reference)

    assert report.candidate_to_reference_object_ratio == pytest.approx(1.0)
    assert not report.mvp_ready
    assert "reference has line objects but candidate has none" in report.mvp_blockers
    assert report.verdict == "debug-pass"


def test_evaluate_svg_structure_marks_reference_like_candidate_mvp_ready(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    reference_text = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M 0 0 C 5 2 8 4 10 10 Z" />
  <line x1="0" y1="0" x2="10" y2="0" />
  <rect x="0" y="0" width="2" height="2" />
</svg>
"""
    candidate.write_text(reference_text, encoding="utf-8")
    reference.write_text(reference_text, encoding="utf-8")

    report = evaluate_svg_structure(candidate, reference)

    assert report.mvp_ready
    assert report.mvp_blockers == []
    assert report.verdict == "mvp-pass"


def test_evaluate_svg_structure_allows_one_missing_scale_marker_group(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M 0 0 C 5 2 8 4 10 10 Z" />
  <line x1="0" y1="0" x2="10" y2="0" />
  <line x1="0" y1="1" x2="1" y2="1" />
  <line x1="0" y1="2" x2="1" y2="2" />
  <line x1="0" y1="3" x2="1" y2="3" />
  <line x1="0" y1="4" x2="10" y2="4" />
  <line x1="0" y1="5" x2="1" y2="5" />
  <line x1="0" y1="6" x2="1" y2="6" />
  <rect x="0" y="0" width="2" height="2" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M 0 0 C 5 2 8 4 10 10 Z" />
  <line x1="0" y1="0" x2="10" y2="0" />
  <line x1="0" y1="1" x2="1" y2="1" />
  <line x1="0" y1="2" x2="1" y2="2" />
  <line x1="0" y1="3" x2="1" y2="3" />
  <line x1="0" y1="4" x2="10" y2="4" />
  <line x1="0" y1="5" x2="1" y2="5" />
  <line x1="0" y1="6" x2="1" y2="6" />
  <line x1="0" y1="7" x2="1" y2="7" />
  <line x1="0" y1="8" x2="10" y2="8" />
  <line x1="0" y1="9" x2="1" y2="9" />
  <rect x="0" y="0" width="2" height="2" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_svg_structure(candidate, reference)

    assert report.mvp_ready
    assert report.verdict == "mvp-pass"


def test_evaluate_svg_shape_matches_scaled_translated_closed_paths(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path d="M 10 10 L 30 10 L 30 30 L 10 30 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <path d="M 100 100 L 300 100 L 300 300 L 100 300 Z" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_svg_shape(candidate, reference)
    report_path = tmp_path / "shape-report.json"
    write_svg_shape_evaluation_report(report, report_path)

    assert report.candidate_path_count == 1
    assert report.reference_path_count == 1
    assert report.matched_path_count == 1
    assert report.unmatched_candidate_indices == ()
    assert report.unmatched_reference_indices == ()
    assert report.max_deviation_normalized == pytest.approx(0.0)
    assert report.verdict == "shape-pass"
    assert '"matched_path_count": 1' in report_path.read_text(encoding="utf-8")


def test_evaluate_svg_shape_reports_unmatched_reference_path(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path d="M 0 0 L 10 0 L 10 10 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path d="M 0 0 L 10 0 L 10 10 Z" />
  <path d="M 20 20 L 30 20 L 30 30 Z" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_svg_shape(candidate, reference)

    assert report.matched_path_count == 1
    assert len(report.unmatched_reference_indices) == 1
    assert "reference has unmatched paths" in report.shape_blockers
    assert report.verdict == "shape-debug-pass"


def test_evaluate_svg_piece_acceptance_measures_paths_and_rects_in_mm(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    pt_per_mm = 72 / 25.4
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 297 420">
  <path d="M 10 10 L 40 10 L 40 40 L 10 40 Z" />
  <rect x="60" y="20" width="20" height="30" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {297 * pt_per_mm:.6f} {420 * pt_per_mm:.6f}">
  <path d="M {10 * pt_per_mm:.6f} {10 * pt_per_mm:.6f} L {40 * pt_per_mm:.6f} {10 * pt_per_mm:.6f} L {40 * pt_per_mm:.6f} {40 * pt_per_mm:.6f} L {10 * pt_per_mm:.6f} {40 * pt_per_mm:.6f} Z" />
  <rect x="{60 * pt_per_mm:.6f}" y="{20 * pt_per_mm:.6f}" width="{20 * pt_per_mm:.6f}" height="{30 * pt_per_mm:.6f}" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_svg_piece_acceptance(candidate, reference)
    report_path = tmp_path / "piece-acceptance.json"
    write_svg_piece_acceptance_report(report, report_path)

    assert report.accepted
    assert report.result_state == "deliverable-mvp"
    assert report.candidate_piece_count == 2
    assert report.reference_piece_count == 2
    assert report.matched_piece_count == 2
    assert report.failed_reference_piece_indices == ()
    assert report.max_deviation_mm == pytest.approx(0.0, abs=1e-5)
    assert '"result_state": "deliverable-mvp"' in report_path.read_text(encoding="utf-8")


def test_evaluate_svg_piece_acceptance_fails_unmatched_reference_piece(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.svg"
    reference = tmp_path / "reference.svg"
    candidate.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 0 0 L 10 0 L 10 10 Z" />
</svg>
""",
        encoding="utf-8",
    )
    reference.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 0 0 L 10 0 L 10 10 Z" />
  <path d="M 60 60 L 80 60 L 80 80 Z" />
</svg>
""",
        encoding="utf-8",
    )

    report = evaluate_svg_piece_acceptance(candidate, reference)

    assert not report.accepted
    assert report.result_state == "continue-development"
    assert report.unmatched_reference_piece_indices == (2,)
    assert report.failed_reference_piece_indices == (2,)
    assert report.failed_piece_details[0].failure_type == "unmatched-reference"
    assert report.failed_piece_details[0].reference_piece_index == 2
    assert report.failed_piece_details[0].candidate_piece_index is None
    assert "reference has unmatched pieces" in report.blockers


def test_evaluate_svg_piece_acceptance_rejects_single_piece_over_tolerance(
    tmp_path: Path,
) -> None:
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

    report = evaluate_svg_piece_acceptance(candidate, reference, tolerance_mm=0.2)

    assert not report.accepted
    assert report.result_state == "internal-test"
    assert report.failed_reference_piece_indices == (1,)
    assert report.failed_piece_details[0].failure_type == "over-tolerance"
    assert report.failed_piece_details[0].reference_piece_index == 1
    assert report.failed_piece_details[0].candidate_piece_index == 1
    assert report.failed_piece_details[0].max_deviation_mm == pytest.approx(0.3)
    assert report.piece_matches[0].max_deviation_mm == pytest.approx(0.3)
    assert "at least one matched piece exceeds tolerance" in report.blockers
