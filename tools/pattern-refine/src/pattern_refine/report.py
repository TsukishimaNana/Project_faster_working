"""Quality reports for PatternRefine pipeline outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pattern_refine.evaluate import SvgPieceAcceptanceReport
from pattern_refine.geometry import PathGeometry
from pattern_refine.production_quality import ProductionQualityReport
from pattern_refine.semantic import SemanticGeometryReport


@dataclass(frozen=True)
class DeviationReport:
    tolerance_mm: float
    max_deviation_mm: float
    smoothing_applied: bool
    accepted: bool
    path_count: int
    closed_path_count: int
    total_area_mm2: float
    total_perimeter_mm: float

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "tolerance_mm": self.tolerance_mm,
            "max_deviation_mm": self.max_deviation_mm,
            "smoothing_applied": self.smoothing_applied,
            "accepted": self.accepted,
            "path_count": self.path_count,
            "closed_path_count": self.closed_path_count,
            "total_area_mm2": self.total_area_mm2,
            "total_perimeter_mm": self.total_perimeter_mm,
        }


def build_identity_deviation_report(
    geometries: tuple[PathGeometry, ...],
    *,
    tolerance_mm: float = 0.2,
) -> DeviationReport:
    """Report current geometry quality before smoothing is enabled."""

    max_deviation_mm = 0.0
    return DeviationReport(
        tolerance_mm=tolerance_mm,
        max_deviation_mm=max_deviation_mm,
        smoothing_applied=False,
        accepted=max_deviation_mm <= tolerance_mm,
        path_count=len(geometries),
        closed_path_count=sum(1 for geometry in geometries if geometry.closed),
        total_area_mm2=sum(geometry.area_mm2 for geometry in geometries),
        total_perimeter_mm=sum(geometry.perimeter_mm for geometry in geometries),
    )


def write_deviation_report(report: DeviationReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


@dataclass(frozen=True)
class FinalSvgStatusReport:
    final_svg_path: str
    result_state: str
    delivery_ready: bool
    final_svg_is_unique_delivery_candidate: bool
    final_geometry_source: str
    centerline_replacement_applied: bool
    centerline_reference_path_count: int
    centerline_piece_candidate_count: int
    centerline_missing_reference_count: int
    blockers: tuple[str, ...]
    piece_acceptance_accepted: bool | None
    piece_acceptance_report_path: str | None
    piece_acceptance_max_deviation_mm: float | None
    piece_acceptance_tolerance_mm: float | None
    production_quality_accepted: bool | None
    production_quality_report_path: str | None
    production_quality_blockers: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "final_svg_path": self.final_svg_path,
            "result_state": self.result_state,
            "delivery_ready": self.delivery_ready,
            "final_svg_is_unique_delivery_candidate": self.final_svg_is_unique_delivery_candidate,
            "geometry_source": self.final_geometry_source,
            "final_geometry_source": self.final_geometry_source,
            "centerline_replacement_applied": self.centerline_replacement_applied,
            "centerline_reference_path_count": self.centerline_reference_path_count,
            "centerline_piece_candidate_count": self.centerline_piece_candidate_count,
            "centerline_missing_reference_count": self.centerline_missing_reference_count,
            "blockers": list(self.blockers),
            "piece_acceptance": {
                "accepted": self.piece_acceptance_accepted,
                "report_path": self.piece_acceptance_report_path,
                "max_deviation_mm": self.piece_acceptance_max_deviation_mm,
                "tolerance_mm": self.piece_acceptance_tolerance_mm,
            },
            "production_quality": {
                "accepted": self.production_quality_accepted,
                "report_path": self.production_quality_report_path,
                "blockers": list(self.production_quality_blockers),
            },
        }


def build_final_svg_status_report(
    final_svg_path: Path,
    semantic_report: SemanticGeometryReport,
    *,
    final_geometry_source: str | None = None,
    reference_guided: bool = False,
    piece_acceptance_report: SvgPieceAcceptanceReport | None = None,
    piece_acceptance_report_path: Path | None = None,
    production_quality_report: ProductionQualityReport | None = None,
    production_quality_report_path: Path | None = None,
) -> FinalSvgStatusReport:
    """Classify the final SVG without treating debug geometry as customer-ready."""

    blockers: list[str] = []
    if not reference_guided and not semantic_report.centerline_replacement_applied:
        blockers.append("centerline replacement was not applied; final SVG still uses outline fallback")
    if not reference_guided and semantic_report.centerline_missing_reference_count > 0:
        blockers.append("some piece-level centerline candidates are missing")
    if (
        not reference_guided
        and semantic_report.centerline_piece_candidate_count < semantic_report.centerline_reference_path_count
    ):
        blockers.append("not every deferred pattern path has a centerline candidate")
    if piece_acceptance_report is None:
        blockers.append("reference piece acceptance has not passed in this pipeline step")
    elif not piece_acceptance_report.accepted:
        blockers.extend(piece_acceptance_report.blockers)
    if production_quality_report is None:
        blockers.append("production cleanliness/topology gate has not run")
    elif not production_quality_report.accepted:
        blockers.extend(production_quality_report.blockers)
    delivery_ready = not blockers
    return FinalSvgStatusReport(
        final_svg_path=str(final_svg_path),
        result_state="deliverable-mvp" if delivery_ready else "internal-test",
        delivery_ready=delivery_ready,
        final_svg_is_unique_delivery_candidate=True,
        final_geometry_source=final_geometry_source or (
            "semantic-centerline"
            if semantic_report.centerline_replacement_applied
            else "semantic-outline-fallback"
        ),
        centerline_replacement_applied=semantic_report.centerline_replacement_applied,
        centerline_reference_path_count=semantic_report.centerline_reference_path_count,
        centerline_piece_candidate_count=semantic_report.centerline_piece_candidate_count,
        centerline_missing_reference_count=semantic_report.centerline_missing_reference_count,
        blockers=tuple(blockers),
        piece_acceptance_accepted=(
            piece_acceptance_report.accepted if piece_acceptance_report is not None else None
        ),
        piece_acceptance_report_path=(
            str(piece_acceptance_report_path) if piece_acceptance_report_path is not None else None
        ),
        piece_acceptance_max_deviation_mm=(
            piece_acceptance_report.max_deviation_mm
            if piece_acceptance_report is not None
            else None
        ),
        piece_acceptance_tolerance_mm=(
            piece_acceptance_report.tolerance_mm if piece_acceptance_report is not None else None
        ),
        production_quality_accepted=(
            production_quality_report.accepted if production_quality_report is not None else None
        ),
        production_quality_report_path=(
            str(production_quality_report_path) if production_quality_report_path is not None else None
        ),
        production_quality_blockers=(
            production_quality_report.blockers if production_quality_report is not None else ()
        ),
    )


def write_final_svg_status_report(report: FinalSvgStatusReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
