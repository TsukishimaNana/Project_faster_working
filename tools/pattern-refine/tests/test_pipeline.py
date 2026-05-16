from pathlib import Path
import json

import cv2
import fitz
import numpy as np
import pytest

from pattern_refine.pipeline import extract_black_lines, refine_pdf


def test_extract_black_lines_keeps_dark_linework_on_white_background() -> None:
    image = np.full((48, 48, 3), 255, dtype=np.uint8)
    image[24, 8:40] = 0

    lines = extract_black_lines(image)

    assert lines[24, 24] == 0
    assert lines[4, 4] == 255


def test_refine_pdf_renders_first_page_and_refuses_overwrite(tmp_path: Path) -> None:
    input_pdf = tmp_path / "sample.pdf"
    output_dir = tmp_path / "output"
    document = fitz.open()
    page = document.new_page(width=72, height=72)
    page.draw_rect((10, 10, 62, 62), color=(0, 0, 0), width=1)
    document.save(input_pdf)
    document.close()

    result = refine_pdf(input_pdf, output_dir, dpi=72)

    assert result.render_path.exists()
    assert result.lines_path.exists()
    assert result.candidate_svg_path.exists()
    assert result.centerline_svg_path.exists()
    assert result.cleaned_svg_path.exists()
    assert result.overlay_svg_path.exists()
    assert result.deviation_overlay_svg_path.exists()
    assert result.feature_overlay_svg_path.exists()
    assert result.smoothed_svg_path.exists()
    assert result.smoothing_overlay_svg_path.exists()
    assert result.semantic_svg_path.exists()
    assert result.final_svg_path.exists()
    assert result.refined_pdf_path.exists()
    assert result.deviation_report_path.exists()
    assert result.scale_report_path.exists()
    assert result.centerline_report_path.exists()
    assert result.classification_report_path.exists()
    assert result.feature_report_path.exists()
    assert result.smoothing_report_path.exists()
    assert result.semantic_report_path.exists()
    assert result.final_status_report_path.exists()
    assert not result.piece_acceptance_report_path.exists()
    assert result.production_quality_report_path.exists()
    assert result.scan_vs_reference_guided_report_path.exists()
    assert result.delivery_overlay_report_path.exists()
    assert result.piece_acceptance_report is None
    assert result.page_width_mm == pytest.approx(25.4)
    assert result.page_height_mm == pytest.approx(25.4)
    assert len(result.geometries) > 0
    assert len(result.candidate_geometries) >= len(result.raw_geometries)
    assert isinstance(result.centerline_geometries, tuple)
    assert len(result.selected_candidate_geometries) == len(result.geometries)
    assert sum(len(geometry.points) for geometry in result.candidate_geometries) >= sum(
        len(geometry.points) for geometry in result.raw_geometries
    )
    assert result.classification_report.kept_count == len(result.selected_candidate_geometries)
    assert isinstance(result.feature_report.feature_counts, dict)
    assert result.smoothing_report.tolerance_mm == pytest.approx(0.2)
    assert result.semantic_report.object_count == len(result.semantic_geometries)
    assert result.final_geometries == result.semantic_geometries
    assert result.reference_template_path is None
    assert result.final_status_report.delivery_ready is False
    assert result.final_status_report.final_svg_is_unique_delivery_candidate is True
    assert result.deviation_report.max_deviation_mm is not None
    assert result.scale_report.detected is False
    assert result.centerline_report.path_count == len(result.centerline_geometries)
    render = cv2.imread(str(result.render_path))
    lines = cv2.imread(str(result.lines_path), cv2.IMREAD_GRAYSCALE)
    assert render is not None
    assert lines is not None
    assert render.shape[:2] == (72, 72)
    assert int(lines.min()) < 255
    assert result.refined_pdf_path.read_bytes().startswith(b"%PDF")
    with fitz.open(result.refined_pdf_path) as refined_pdf:
        assert refined_pdf.page_count == 1
        assert refined_pdf.load_page(0).get_images() == []
    report = json.loads(result.deviation_report_path.read_text(encoding="utf-8"))
    assert report["tolerance_mm"] == pytest.approx(0.2)
    assert report["simplified_path_count"] == len(result.geometries)
    scale_report = json.loads(result.scale_report_path.read_text(encoding="utf-8"))
    assert scale_report["detected"] is False
    centerline_report = json.loads(result.centerline_report_path.read_text(encoding="utf-8"))
    assert centerline_report["path_count"] == len(result.centerline_geometries)
    classification_report = json.loads(
        result.classification_report_path.read_text(encoding="utf-8")
    )
    assert classification_report["kept_count"] == len(result.geometries)
    feature_report = json.loads(result.feature_report_path.read_text(encoding="utf-8"))
    assert "feature_counts" in feature_report
    smoothing_report = json.loads(result.smoothing_report_path.read_text(encoding="utf-8"))
    assert "accepted_path_count" in smoothing_report
    semantic_report = json.loads(result.semantic_report_path.read_text(encoding="utf-8"))
    assert semantic_report["object_count"] == len(result.semantic_geometries)
    assert "centerline_piece_candidate_count" in semantic_report
    final_status_report = json.loads(
        result.final_status_report_path.read_text(encoding="utf-8")
    )
    assert final_status_report["final_svg_is_unique_delivery_candidate"] is True
    assert final_status_report["delivery_ready"] is False
    assert final_status_report["geometry_source"] == "semantic-outline-fallback"
    assert final_status_report["result_state"] == result.final_status_report.result_state
    assert final_status_report["final_geometry_source"] == "semantic-outline-fallback"
    assert final_status_report["production_quality"]["accepted"] is False
    assert final_status_report["production_quality"]["report_path"] == str(
        result.production_quality_report_path
    )
    production_quality_report = json.loads(
        result.production_quality_report_path.read_text(encoding="utf-8")
    )
    assert production_quality_report["accepted"] is False
    assert "manual_production_review_required" in production_quality_report["blockers"]
    difference_report = json.loads(
        result.scan_vs_reference_guided_report_path.read_text(encoding="utf-8")
    )
    assert difference_report["scan_only_delivery_ready"] is False
    assert difference_report["reference_guided_delivery_ready"] is False
    assert difference_report["decision"] == "scan-only remains diagnostic"
    overlay_report = json.loads(
        result.delivery_overlay_report_path.read_text(encoding="utf-8")
    )
    assert overlay_report["page_rotation"] == 0
    assert overlay_report["orientation_normalized"] is True
    assert overlay_report["manual_overlay_review_required"] is True
    assert overlay_report["final_svg_viewbox_matches_page_mm"] is True
    assert result.final_svg_path.read_text(encoding="utf-8") == result.semantic_svg_path.read_text(
        encoding="utf-8"
    )

    with pytest.raises(FileExistsError):
        refine_pdf(input_pdf, output_dir, dpi=72)


def test_refine_pdf_normalizes_rotated_page_to_unrotated_page_size(tmp_path: Path) -> None:
    input_pdf = tmp_path / "rotated.pdf"
    output_dir = tmp_path / "output"
    document = fitz.open()
    page = document.new_page(width=72, height=144)
    page.draw_rect((18, 36, 54, 108), color=(0, 0, 0), width=1)
    page.set_rotation(270)
    document.save(input_pdf)
    document.close()

    result = refine_pdf(input_pdf, output_dir, dpi=72)

    assert result.page_rotation == 270
    assert result.render_width_mm == pytest.approx(50.8)
    assert result.render_height_mm == pytest.approx(25.4)
    assert result.page_width_mm == pytest.approx(25.4)
    assert result.page_height_mm == pytest.approx(50.8)
    assert 'viewBox="0 0 25.400000 50.800000"' in result.semantic_svg_path.read_text(
        encoding="utf-8"
    )
    with fitz.open(result.refined_pdf_path) as refined_pdf:
        page = refined_pdf.load_page(0)
        assert page.rect.width == pytest.approx(72.0)
        assert page.rect.height == pytest.approx(144.0)


def test_refine_pdf_uses_sample_reference_guided_final_svg(tmp_path: Path) -> None:
    source_dir = tmp_path / "Original_PinkShirts"
    source_dir.mkdir()
    input_pdf = source_dir / "pink-dress-original-scan.pdf"
    reference_svg = source_dir / "pink-dress-simple-reference.svg"
    output_dir = tmp_path / "output"
    document = fitz.open()
    page = document.new_page(width=72, height=72)
    page.draw_rect((10, 10, 62, 62), color=(0, 0, 0), width=1)
    document.save(input_pdf)
    document.close()
    reference_svg.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72">
  <path d="M 10 10 C 20 10 30 20 40 40 L 50 50 Z"/>
  <line x1="5" y1="5" x2="25" y2="5"/>
  <rect x="20" y="20" width="10" height="15"/>
</svg>
""",
        encoding="utf-8",
    )

    result = refine_pdf(input_pdf, output_dir, dpi=72)

    assert result.reference_template_path == reference_svg
    assert len(result.final_geometries) == 3
    assert result.final_geometries != result.semantic_geometries
    assert result.final_status_report.final_geometry_source == "reference-guided"
    assert result.piece_acceptance_report is not None
    assert result.final_status_report.delivery_ready is False
    assert result.production_quality_report.accepted is False
    assert result.scan_vs_reference_guided_report.reference_guided_delivery_ready is (
        result.piece_acceptance_report.accepted
    )
    assert result.scan_vs_reference_guided_report.scan_only_delivery_ready is False
    assert result.scan_vs_reference_guided_report.final_geometry_source == "reference-guided"
    assert result.delivery_overlay_report.manual_overlay_review_required is True
    assert result.final_status_report.result_state == (
        "deliverable-mvp" if result.piece_acceptance_report.accepted else "internal-test"
    )
    final_status_report = json.loads(
        result.final_status_report_path.read_text(encoding="utf-8")
    )
    assert final_status_report["geometry_source"] == "reference-guided"
    assert final_status_report["final_geometry_source"] == "reference-guided"
    assert final_status_report["piece_acceptance"]["accepted"] is result.piece_acceptance_report.accepted
    assert final_status_report["piece_acceptance"]["report_path"] == str(
        result.piece_acceptance_report_path
    )
    assert final_status_report["production_quality"]["accepted"] is False
    assert final_status_report["production_quality"]["report_path"] == str(
        result.production_quality_report_path
    )
    difference_report = json.loads(
        result.scan_vs_reference_guided_report_path.read_text(encoding="utf-8")
    )
    assert difference_report["final_geometry_source"] == "reference-guided"
    assert difference_report["scan_only_delivery_ready"] is False
    assert difference_report["reference_guided_delivery_ready"] is result.piece_acceptance_report.accepted
    assert (
        difference_report["reference_guided_max_deviation_mm"]
        == result.piece_acceptance_report.max_deviation_mm
    )
    overlay_report = json.loads(
        result.delivery_overlay_report_path.read_text(encoding="utf-8")
    )
    assert overlay_report["overlay_svg_path"] == str(result.overlay_svg_path)
    assert overlay_report["scale_report_path"] == str(result.scale_report_path)
    assert overlay_report["manual_overlay_review_required"] is True
    assert "centerline replacement was not applied" not in "\n".join(
        final_status_report["blockers"]
    )
    final_svg_text = result.final_svg_path.read_text(encoding="utf-8")
    assert '<path id="path-0001"' in final_svg_text
    assert '<line id="line-0001"' in final_svg_text
    assert '<rect id="rect-0001"' in final_svg_text
    assert result.final_svg_path.read_text(encoding="utf-8") != result.semantic_svg_path.read_text(
        encoding="utf-8"
    )
