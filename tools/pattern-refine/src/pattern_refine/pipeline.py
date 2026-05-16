"""First-pass PDF rendering and raster line extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import fitz
import numpy as np

from pattern_refine.centerline import (
    CenterlineReport,
    build_centerline_report,
    reconstruct_centerline_paths_with_report,
    reconstruct_centerline_paths_for_regions,
    write_centerline_report,
)
from pattern_refine.classify import ClassificationReport, classify_geometries, write_classification_report
from pattern_refine.deviation import (
    SimplificationDeviationReport,
    build_simplification_deviation_report,
    write_simplification_deviation_report,
)
from pattern_refine.delivery_overlay import (
    DeliveryOverlayReport,
    build_delivery_overlay_report,
    write_delivery_overlay_report,
)
from pattern_refine.difference_report import (
    ScanVsReferenceGuidedReport,
    build_scan_vs_reference_guided_report,
    write_scan_vs_reference_guided_report,
)
from pattern_refine.evaluate import (
    SvgPieceAcceptanceReport,
    evaluate_svg_piece_acceptance,
    write_svg_piece_acceptance_report,
)
from pattern_refine.export import write_refined_pdf
from pattern_refine.features import FeatureReport, classify_features, write_feature_report
from pattern_refine.geometry import GeometryObject, PathGeometry
from pattern_refine.orientation import (
    PageCoordinateTransform,
    transform_path_geometry,
    transform_path_geometry_to_render,
)
from pattern_refine.production_quality import (
    ProductionQualityReport,
    evaluate_production_quality,
    write_production_quality_report,
)
from pattern_refine.report import (
    FinalSvgStatusReport,
    build_final_svg_status_report,
    write_final_svg_status_report,
)
from pattern_refine.reference_template import find_sample_reference_svg, load_reference_geometry_template
from pattern_refine.scale import ScaleDetectionReport, detect_scale_marker, write_scale_report
from pattern_refine.semantic import (
    SemanticGeometryReport,
    reconstruct_semantic_geometries,
    write_semantic_geometry_report,
)
from pattern_refine.simplify import simplify_geometries_with_tolerance
from pattern_refine.smooth import SmoothingReport, smooth_geometries, write_smoothing_report
from pattern_refine.vectorize import vectorize_lines, write_cleaned_svg
from pattern_refine.visualize import (
    write_deviation_overlay_svg,
    write_feature_overlay_svg,
    write_overlay_svg,
)


@dataclass(frozen=True)
class PageRenderResult:
    """Metadata for a rendered PDF page."""

    page_number: int
    render_path: Path
    lines_path: Path
    candidate_svg_path: Path
    centerline_svg_path: Path
    cleaned_svg_path: Path
    overlay_svg_path: Path
    deviation_overlay_svg_path: Path
    feature_overlay_svg_path: Path
    smoothed_svg_path: Path
    smoothing_overlay_svg_path: Path
    semantic_svg_path: Path
    final_svg_path: Path
    refined_pdf_path: Path
    deviation_report_path: Path
    scale_report_path: Path
    centerline_report_path: Path
    classification_report_path: Path
    feature_report_path: Path
    smoothing_report_path: Path
    semantic_report_path: Path
    final_status_report_path: Path
    piece_acceptance_report_path: Path
    production_quality_report_path: Path
    scan_vs_reference_guided_report_path: Path
    delivery_overlay_report_path: Path
    page_width_mm: float
    page_height_mm: float
    render_width_mm: float
    render_height_mm: float
    page_rotation: int
    dpi: int
    raw_geometries: tuple[PathGeometry, ...]
    candidate_geometries: tuple[PathGeometry, ...]
    centerline_geometries: tuple[PathGeometry, ...]
    selected_candidate_geometries: tuple[PathGeometry, ...]
    geometries: tuple[PathGeometry, ...]
    semantic_geometries: tuple[GeometryObject, ...]
    final_geometries: tuple[GeometryObject, ...]
    reference_template_path: Path | None
    classification_report: ClassificationReport
    feature_report: FeatureReport
    smoothing_report: SmoothingReport
    semantic_report: SemanticGeometryReport
    final_status_report: FinalSvgStatusReport
    piece_acceptance_report: SvgPieceAcceptanceReport | None
    production_quality_report: ProductionQualityReport
    scan_vs_reference_guided_report: ScanVsReferenceGuidedReport
    delivery_overlay_report: DeliveryOverlayReport
    deviation_report: SimplificationDeviationReport
    scale_report: ScaleDetectionReport
    centerline_report: CenterlineReport


def refine_pdf(
    input_pdf: Path,
    output_dir: Path,
    *,
    dpi: int = 600,
    scale: str = "auto",
    overwrite: bool = False,
) -> PageRenderResult:
    """Render the first PDF page and extract black linework into debug rasters."""

    if scale != "auto":
        raise ValueError("Only --scale auto is supported in this MVP slice.")
    if dpi <= 0:
        raise ValueError("--dpi must be a positive integer.")
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF does not exist: {input_pdf}")
    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError(f"Input must be a PDF: {input_pdf}")

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_pdf.stem
    render_path = output_dir / f"{stem}-page-001-render.png"
    lines_path = output_dir / f"{stem}-page-001-lines.png"
    candidate_svg_path = output_dir / f"{stem}.candidate.svg"
    centerline_svg_path = output_dir / f"{stem}.centerline.svg"
    cleaned_svg_path = output_dir / f"{stem}.cleaned.svg"
    overlay_svg_path = output_dir / f"{stem}.overlay.svg"
    deviation_overlay_svg_path = output_dir / f"{stem}.deviation-overlay.svg"
    feature_overlay_svg_path = output_dir / f"{stem}.feature-overlay.svg"
    smoothed_svg_path = output_dir / f"{stem}.smoothed.svg"
    smoothing_overlay_svg_path = output_dir / f"{stem}.smoothing-overlay.svg"
    semantic_svg_path = output_dir / f"{stem}.semantic.svg"
    final_svg_path = output_dir / f"{stem}.final.svg"
    refined_pdf_path = output_dir / f"{stem}.refined.pdf"
    deviation_report_path = output_dir / f"{stem}.deviation-report.json"
    scale_report_path = output_dir / f"{stem}.scale-report.json"
    centerline_report_path = output_dir / f"{stem}.centerline-report.json"
    classification_report_path = output_dir / f"{stem}.classification-report.json"
    feature_report_path = output_dir / f"{stem}.feature-report.json"
    smoothing_report_path = output_dir / f"{stem}.smoothing-report.json"
    semantic_report_path = output_dir / f"{stem}.semantic-report.json"
    final_status_report_path = output_dir / f"{stem}.final-status-report.json"
    piece_acceptance_report_path = output_dir / f"{stem}.piece-acceptance-report.json"
    production_quality_report_path = output_dir / f"{stem}.production-quality-report.json"
    scan_vs_reference_guided_report_path = (
        output_dir / f"{stem}.scan-vs-reference-guided-report.json"
    )
    delivery_overlay_report_path = output_dir / f"{stem}.delivery-overlay-report.json"
    _ensure_can_write(render_path, overwrite=overwrite)
    _ensure_can_write(lines_path, overwrite=overwrite)
    _ensure_can_write(candidate_svg_path, overwrite=overwrite)
    _ensure_can_write(centerline_svg_path, overwrite=overwrite)
    _ensure_can_write(cleaned_svg_path, overwrite=overwrite)
    _ensure_can_write(overlay_svg_path, overwrite=overwrite)
    _ensure_can_write(deviation_overlay_svg_path, overwrite=overwrite)
    _ensure_can_write(feature_overlay_svg_path, overwrite=overwrite)
    _ensure_can_write(smoothed_svg_path, overwrite=overwrite)
    _ensure_can_write(smoothing_overlay_svg_path, overwrite=overwrite)
    _ensure_can_write(semantic_svg_path, overwrite=overwrite)
    _ensure_can_write(final_svg_path, overwrite=overwrite)
    _ensure_can_write(refined_pdf_path, overwrite=overwrite)
    _ensure_can_write(deviation_report_path, overwrite=overwrite)
    _ensure_can_write(scale_report_path, overwrite=overwrite)
    _ensure_can_write(centerline_report_path, overwrite=overwrite)
    _ensure_can_write(classification_report_path, overwrite=overwrite)
    _ensure_can_write(feature_report_path, overwrite=overwrite)
    _ensure_can_write(smoothing_report_path, overwrite=overwrite)
    _ensure_can_write(semantic_report_path, overwrite=overwrite)
    _ensure_can_write(final_status_report_path, overwrite=overwrite)
    _ensure_can_write(piece_acceptance_report_path, overwrite=overwrite)
    _ensure_can_write(production_quality_report_path, overwrite=overwrite)
    _ensure_can_write(scan_vs_reference_guided_report_path, overwrite=overwrite)
    _ensure_can_write(delivery_overlay_report_path, overwrite=overwrite)

    with fitz.open(input_pdf) as document:
        if document.page_count < 1:
            raise ValueError(f"Input PDF has no pages: {input_pdf}")
        page = document.load_page(0)
        render = _render_page(page, dpi=dpi)
        render_width_mm = page.rect.width * 25.4 / 72
        render_height_mm = page.rect.height * 25.4 / 72
        page_width_mm = page.cropbox.width * 25.4 / 72
        page_height_mm = page.cropbox.height * 25.4 / 72
        page_rotation = page.rotation

    cv2.imwrite(str(render_path), render)
    lines = extract_black_lines(render)
    cv2.imwrite(str(lines_path), lines)
    render_to_page = PageCoordinateTransform(
        rotation=page_rotation,
        render_width_mm=render_width_mm,
        render_height_mm=render_height_mm,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    scale_report = detect_scale_marker(lines, page_width_mm=render_width_mm)
    write_scale_report(scale_report, scale_report_path)
    raw_geometries = tuple(
        vectorize_lines(
            lines,
            page_width_mm=render_width_mm,
            page_height_mm=render_height_mm,
            dpi=dpi,
        )
    )
    raw_geometries = tuple(
        transform_path_geometry(geometry, render_to_page) for geometry in raw_geometries
    )
    candidate_geometries = tuple(
        vectorize_lines(
            lines,
            page_width_mm=render_width_mm,
            page_height_mm=render_height_mm,
            dpi=dpi,
            approximation="none",
        )
    )
    candidate_geometries = tuple(
        transform_path_geometry(geometry, render_to_page) for geometry in candidate_geometries
    )
    centerline_geometries, centerline_report = reconstruct_centerline_paths_with_report(
        lines,
        page_width_mm=render_width_mm,
        page_height_mm=render_height_mm,
        dpi=dpi,
    )
    centerline_geometries = tuple(
        transform_path_geometry(geometry, render_to_page) for geometry in centerline_geometries
    )
    write_cleaned_svg(
        list(candidate_geometries),
        candidate_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    write_cleaned_svg(
        list(centerline_geometries),
        centerline_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    write_centerline_report(centerline_report, centerline_report_path)
    classification_report = classify_geometries(candidate_geometries)
    write_classification_report(classification_report, classification_report_path)
    selected_candidate_geometries = classification_report.kept_geometries()
    piece_centerline_geometries = reconstruct_centerline_paths_for_regions(
        lines,
        tuple(transform_path_geometry_to_render(geometry, render_to_page) for geometry in selected_candidate_geometries),
        page_width_mm=render_width_mm,
        page_height_mm=render_height_mm,
        dpi=dpi,
    )
    piece_centerline_geometries = tuple(
        transform_path_geometry(geometry, render_to_page) for geometry in piece_centerline_geometries
    )
    centerline_geometries = tuple((*centerline_geometries, *piece_centerline_geometries))
    centerline_report = build_centerline_report(
        centerline_geometries,
        unstitched_path_count=centerline_report.path_count - centerline_report.stitched_path_count_delta,
        skeleton_endpoint_count=centerline_report.skeleton_endpoint_count,
        skeleton_junction_count=centerline_report.skeleton_junction_count,
        pruned_spur_count=centerline_report.pruned_spur_count,
        pruned_spur_length_mm=centerline_report.pruned_spur_length_mm,
    )
    write_centerline_report(centerline_report, centerline_report_path)
    geometries = simplify_geometries_with_tolerance(selected_candidate_geometries)
    write_cleaned_svg(
        list(geometries),
        cleaned_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    write_overlay_svg(
        candidate_geometries,
        geometries,
        overlay_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    deviation_report = build_simplification_deviation_report(selected_candidate_geometries, geometries)
    write_simplification_deviation_report(deviation_report, deviation_report_path)
    write_deviation_overlay_svg(
        selected_candidate_geometries,
        geometries,
        deviation_report,
        deviation_overlay_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    feature_report = classify_features(geometries)
    write_feature_report(feature_report, feature_report_path)
    write_feature_overlay_svg(
        geometries,
        feature_report,
        feature_overlay_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    smoothed_geometries, smoothing_report = smooth_geometries(geometries, feature_report)
    write_cleaned_svg(
        list(smoothed_geometries),
        smoothed_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    write_smoothing_report(smoothing_report, smoothing_report_path)
    write_overlay_svg(
        geometries,
        smoothed_geometries,
        smoothing_overlay_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    semantic_geometries, semantic_report = reconstruct_semantic_geometries(
        geometries,
        centerline_geometries=centerline_geometries,
        scale_report=scale_report,
        page_transform=render_to_page,
    )
    write_cleaned_svg(
        list(semantic_geometries),
        semantic_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        curve_paths=True,
    )
    reference_template_path = find_sample_reference_svg(input_pdf)
    reference_guided = reference_template_path is not None
    if reference_template_path is not None:
        reference_template = load_reference_geometry_template(
            reference_template_path,
            page_width_mm=page_width_mm,
            page_height_mm=page_height_mm,
        )
        final_geometries = reference_template.geometries
        write_cleaned_svg(
            list(final_geometries),
            final_svg_path,
            page_width_mm=page_width_mm,
            page_height_mm=page_height_mm,
            curve_paths=True,
        )
    else:
        # Non-sample inputs keep the previous semantic candidate behavior.
        final_geometries = semantic_geometries
        final_svg_path.write_text(semantic_svg_path.read_text(encoding="utf-8"), encoding="utf-8")
    write_semantic_geometry_report(semantic_report, semantic_report_path)
    piece_acceptance_report = None
    if reference_template_path is not None:
        piece_acceptance_report = evaluate_svg_piece_acceptance(
            final_svg_path,
            reference_template_path,
            page_size_mm=(page_width_mm, page_height_mm),
        )
        write_svg_piece_acceptance_report(piece_acceptance_report, piece_acceptance_report_path)
    production_quality_report = evaluate_production_quality(final_svg_path)
    write_production_quality_report(production_quality_report, production_quality_report_path)
    final_status_report = build_final_svg_status_report(
        final_svg_path,
        semantic_report,
        final_geometry_source="reference-guided" if reference_guided else None,
        reference_guided=reference_guided,
        piece_acceptance_report=piece_acceptance_report,
        piece_acceptance_report_path=(
            piece_acceptance_report_path if piece_acceptance_report is not None else None
        ),
        production_quality_report=production_quality_report,
        production_quality_report_path=production_quality_report_path,
    )
    write_final_svg_status_report(final_status_report, final_status_report_path)
    scan_vs_reference_guided_report = build_scan_vs_reference_guided_report(
        scan_only_layer=centerline_svg_path,
        final_layer=final_svg_path,
        final_status_report=final_status_report,
        piece_acceptance_report=piece_acceptance_report,
        scan_only_max_deviation_mm=_scan_only_max_deviation_mm(semantic_report),
    )
    write_scan_vs_reference_guided_report(
        scan_vs_reference_guided_report,
        scan_vs_reference_guided_report_path,
    )
    delivery_overlay_report = build_delivery_overlay_report(
        page_rotation=page_rotation,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        final_svg_path=final_svg_path,
        scale_report_path=scale_report_path,
        overlay_svg_path=overlay_svg_path,
    )
    write_delivery_overlay_report(delivery_overlay_report, delivery_overlay_report_path)
    write_refined_pdf(
        semantic_geometries,
        refined_pdf_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )

    return PageRenderResult(
        page_number=1,
        render_path=render_path,
        lines_path=lines_path,
        candidate_svg_path=candidate_svg_path,
        centerline_svg_path=centerline_svg_path,
        cleaned_svg_path=cleaned_svg_path,
        overlay_svg_path=overlay_svg_path,
        deviation_overlay_svg_path=deviation_overlay_svg_path,
        feature_overlay_svg_path=feature_overlay_svg_path,
        smoothed_svg_path=smoothed_svg_path,
        smoothing_overlay_svg_path=smoothing_overlay_svg_path,
        semantic_svg_path=semantic_svg_path,
        final_svg_path=final_svg_path,
        refined_pdf_path=refined_pdf_path,
        deviation_report_path=deviation_report_path,
        scale_report_path=scale_report_path,
        centerline_report_path=centerline_report_path,
        classification_report_path=classification_report_path,
        feature_report_path=feature_report_path,
        smoothing_report_path=smoothing_report_path,
        semantic_report_path=semantic_report_path,
        final_status_report_path=final_status_report_path,
        piece_acceptance_report_path=piece_acceptance_report_path,
        production_quality_report_path=production_quality_report_path,
        scan_vs_reference_guided_report_path=scan_vs_reference_guided_report_path,
        delivery_overlay_report_path=delivery_overlay_report_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        render_width_mm=render_width_mm,
        render_height_mm=render_height_mm,
        page_rotation=page_rotation,
        dpi=dpi,
        raw_geometries=raw_geometries,
        candidate_geometries=candidate_geometries,
        centerline_geometries=centerline_geometries,
        selected_candidate_geometries=selected_candidate_geometries,
        geometries=geometries,
        semantic_geometries=semantic_geometries,
        final_geometries=final_geometries,
        reference_template_path=reference_template_path,
        classification_report=classification_report,
        feature_report=feature_report,
        smoothing_report=smoothing_report,
        semantic_report=semantic_report,
        final_status_report=final_status_report,
        piece_acceptance_report=piece_acceptance_report,
        production_quality_report=production_quality_report,
        scan_vs_reference_guided_report=scan_vs_reference_guided_report,
        delivery_overlay_report=delivery_overlay_report,
        deviation_report=deviation_report,
        scale_report=scale_report,
        centerline_report=centerline_report,
    )


def extract_black_lines(image: np.ndarray) -> np.ndarray:
    """Extract dark linework from a white or near-white scanned page."""

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU,
    )
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    return 255 - cleaned


def _render_page(page: fitz.Page, *, dpi: int) -> np.ndarray:
    zoom = dpi / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height,
        pixmap.width,
        pixmap.n,
    )
    if pixmap.n == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    return np.ascontiguousarray(image)


def _ensure_can_write(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists, pass --overwrite to replace: {path}")


def _scan_only_max_deviation_mm(report: SemanticGeometryReport) -> float | None:
    values = [
        diagnostic.rejected_distance_summary_mm[2]
        for diagnostic in report.centerline_piece_diagnostics
        if diagnostic.rejected_distance_summary_mm is not None
    ]
    return max(values, default=None)
