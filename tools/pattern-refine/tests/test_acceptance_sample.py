import json
from pathlib import Path

import fitz
import pytest

from pattern_refine.compare import write_failed_piece_comparison, write_piece_comparison
from pattern_refine.evaluate import (
    evaluate_svg_piece_acceptance,
    evaluate_svg_shape,
    evaluate_svg_structure,
    write_svg_piece_acceptance_report,
)
from pattern_refine.pipeline import refine_pdf


SAMPLE_PDF = Path(
    "knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-original-scan.pdf"
)
REFERENCE_SVG = Path(
    "knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-simple-reference.svg"
)


@pytest.mark.skipif(
    not SAMPLE_PDF.exists() or not REFERENCE_SVG.exists(),
    reason="Pink dress sample fixture is not available.",
)
def test_pink_dress_sample_acceptance_preserves_features_and_exports_vector_pdf(
    tmp_path: Path,
) -> None:
    result = refine_pdf(SAMPLE_PDF, tmp_path, dpi=300)

    structure = evaluate_svg_structure(result.final_svg_path, REFERENCE_SVG)
    shape = evaluate_svg_shape(result.final_svg_path, REFERENCE_SVG)
    piece_acceptance = evaluate_svg_piece_acceptance(
        result.final_svg_path,
        REFERENCE_SVG,
        page_size_mm=(result.page_width_mm, result.page_height_mm),
    )
    piece_report_path = tmp_path / "pink-dress-original-scan.piece-acceptance-report.json"
    piece_overlay_path = tmp_path / "pink-dress-original-scan.pieces-comparison.svg"
    failed_piece_overlay_path = tmp_path / "pink-dress-original-scan.failed-pieces-comparison.svg"
    write_svg_piece_acceptance_report(piece_acceptance, piece_report_path)
    write_piece_comparison(result.final_svg_path, REFERENCE_SVG, piece_overlay_path)
    if not piece_acceptance.accepted:
        write_failed_piece_comparison(
            result.final_svg_path,
            REFERENCE_SVG,
            failed_piece_overlay_path,
            page_size_mm=(result.page_width_mm, result.page_height_mm),
        )

    assert result.refined_pdf_path.exists()
    with fitz.open(result.refined_pdf_path) as refined_pdf:
        assert refined_pdf.page_count == 1
        assert refined_pdf.load_page(0).get_images() == []

    assert result.deviation_report.accepted is True
    assert result.deviation_report.max_deviation_mm is not None
    assert result.deviation_report.max_deviation_mm <= result.deviation_report.tolerance_mm
    assert result.semantic_report.path_count >= 7
    assert result.semantic_report.centerline_piece_candidate_count >= 9
    assert result.semantic_report.centerline_missing_reference_count == 0
    assert any(
        diagnostic.source == "large-piece-reference-near"
        for diagnostic in result.semantic_report.centerline_piece_diagnostics
    )
    assert any(
        diagnostic.source == "slender-reference-near-fill"
        for diagnostic in result.semantic_report.centerline_piece_diagnostics
    )
    assert any(
        diagnostic.source == "compact-reference-near-fill"
        for diagnostic in result.semantic_report.centerline_piece_diagnostics
    )
    assert result.reference_template_path == REFERENCE_SVG
    assert result.final_status_report.final_geometry_source == "reference-guided"
    assert result.final_status_report.delivery_ready is False
    assert result.semantic_report.rect_count >= 1
    assert result.semantic_report.line_count >= 5
    assert structure.candidate.object_count == structure.reference.object_count
    assert structure.candidate.path_count == structure.reference.path_count
    assert structure.candidate.line_count == structure.reference.line_count
    assert structure.candidate.rect_count == structure.reference.rect_count
    assert shape.verdict == "shape-pass"
    assert shape.matched_path_count == shape.reference_path_count
    assert piece_report_path.exists()
    assert piece_overlay_path.exists()
    assert not failed_piece_overlay_path.exists()
    assert piece_acceptance.tolerance_mm == pytest.approx(0.2)
    assert piece_acceptance.reference_piece_count == 10
    assert piece_acceptance.result_state == "deliverable-mvp"
    assert piece_acceptance.accepted is True
    assert not piece_acceptance.blockers
    assert piece_acceptance.max_deviation_mm is not None
    assert piece_acceptance.max_deviation_mm <= piece_acceptance.tolerance_mm
    assert piece_acceptance.matched_piece_count == piece_acceptance.reference_piece_count
    assert not piece_acceptance.unmatched_reference_piece_indices
    assert not piece_acceptance.failed_reference_piece_indices
    assert not piece_acceptance.failed_piece_details

    feature_counts = result.feature_report.feature_counts
    assert feature_counts.get("notch_candidate", 0) >= 1
    assert feature_counts.get("right_angle_candidate", 0) >= 1
    assert feature_counts.get("straight_edge_candidate", 0) >= 1
    assert feature_counts.get("short_alignment_mark_candidate", 0) >= 1
    assert result.smoothing_report.protected_point_count >= feature_counts["notch_candidate"]
    assert any(path.protected_path for path in result.smoothing_report.path_results)

    feature_report = json.loads(result.feature_report_path.read_text(encoding="utf-8"))
    smoothing_report = json.loads(result.smoothing_report_path.read_text(encoding="utf-8"))
    assert feature_report["feature_counts"]["notch_candidate"] >= 1
    assert smoothing_report["protected_point_count"] == result.smoothing_report.protected_point_count
