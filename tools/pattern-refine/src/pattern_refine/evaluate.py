"""Evaluation helpers for comparing generated SVGs with reference SVGs."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

SVG_NS = "http://www.w3.org/2000/svg"
_NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
_PATH_TOKEN_RE = re.compile(r"[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


@dataclass(frozen=True)
class SvgStructureMetrics:
    path_count: int
    closed_path_count: int
    curved_path_count: int
    line_count: int
    rect_count: int
    polygon_count: int
    polyline_count: int
    small_object_count: int
    bbox: tuple[float, float, float, float] | None

    @property
    def object_count(self) -> int:
        return (
            self.path_count
            + self.line_count
            + self.rect_count
            + self.polygon_count
            + self.polyline_count
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "object_count": self.object_count,
            "path_count": self.path_count,
            "closed_path_count": self.closed_path_count,
            "curved_path_count": self.curved_path_count,
            "line_count": self.line_count,
            "rect_count": self.rect_count,
            "polygon_count": self.polygon_count,
            "polyline_count": self.polyline_count,
            "small_object_count": self.small_object_count,
            "bbox": list(self.bbox) if self.bbox is not None else None,
        }


@dataclass(frozen=True)
class SvgEvaluationReport:
    candidate: SvgStructureMetrics
    reference: SvgStructureMetrics
    object_count_delta: int
    path_count_delta: int
    object_type_deltas: dict[str, int]
    candidate_to_reference_object_ratio: float | None
    mvp_ready: bool
    mvp_blockers: list[str]
    verdict: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_json_dict(),
            "reference": self.reference.to_json_dict(),
            "object_count_delta": self.object_count_delta,
            "path_count_delta": self.path_count_delta,
            "object_type_deltas": self.object_type_deltas,
            "candidate_to_reference_object_ratio": self.candidate_to_reference_object_ratio,
            "mvp_ready": self.mvp_ready,
            "mvp_blockers": self.mvp_blockers,
            "verdict": self.verdict,
        }


@dataclass(frozen=True)
class PathShapeMatch:
    candidate_index: int
    reference_index: int
    bbox_iou: float
    mean_deviation_normalized: float
    p95_deviation_normalized: float
    max_deviation_normalized: float
    sample_count: int
    candidate_bbox: tuple[float, float, float, float]
    reference_bbox: tuple[float, float, float, float]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "candidate_index": self.candidate_index,
            "reference_index": self.reference_index,
            "bbox_iou": self.bbox_iou,
            "mean_deviation_normalized": self.mean_deviation_normalized,
            "p95_deviation_normalized": self.p95_deviation_normalized,
            "max_deviation_normalized": self.max_deviation_normalized,
            "sample_count": self.sample_count,
            "candidate_bbox": list(self.candidate_bbox),
            "reference_bbox": list(self.reference_bbox),
        }


@dataclass(frozen=True)
class PieceAcceptanceMatch:
    candidate_piece_index: int
    reference_piece_index: int
    accepted: bool
    bbox_iou: float
    mean_deviation_mm: float
    p95_deviation_mm: float
    max_deviation_mm: float
    sample_count: int
    candidate_bbox_mm: tuple[float, float, float, float]
    reference_bbox_mm: tuple[float, float, float, float]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "candidate_piece_index": self.candidate_piece_index,
            "reference_piece_index": self.reference_piece_index,
            "accepted": self.accepted,
            "bbox_iou": self.bbox_iou,
            "mean_deviation_mm": self.mean_deviation_mm,
            "p95_deviation_mm": self.p95_deviation_mm,
            "max_deviation_mm": self.max_deviation_mm,
            "sample_count": self.sample_count,
            "candidate_bbox_mm": list(self.candidate_bbox_mm),
            "reference_bbox_mm": list(self.reference_bbox_mm),
        }


@dataclass(frozen=True)
class FailedPieceDetail:
    failure_type: str
    reference_piece_index: int | None
    candidate_piece_index: int | None
    max_deviation_mm: float | None
    mean_deviation_mm: float | None
    p95_deviation_mm: float | None
    bbox_iou: float | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "reference_piece_index": self.reference_piece_index,
            "candidate_piece_index": self.candidate_piece_index,
            "max_deviation_mm": self.max_deviation_mm,
            "mean_deviation_mm": self.mean_deviation_mm,
            "p95_deviation_mm": self.p95_deviation_mm,
            "bbox_iou": self.bbox_iou,
        }


@dataclass(frozen=True)
class SvgPieceAcceptanceReport:
    tolerance_mm: float
    accepted: bool
    result_state: str
    candidate_piece_count: int
    reference_piece_count: int
    matched_piece_count: int
    unmatched_candidate_piece_indices: tuple[int, ...]
    unmatched_reference_piece_indices: tuple[int, ...]
    failed_reference_piece_indices: tuple[int, ...]
    mean_deviation_mm: float | None
    p95_deviation_mm: float | None
    max_deviation_mm: float | None
    piece_matches: tuple[PieceAcceptanceMatch, ...]
    failed_piece_details: tuple[FailedPieceDetail, ...]
    blockers: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "tolerance_mm": self.tolerance_mm,
            "accepted": self.accepted,
            "result_state": self.result_state,
            "candidate_piece_count": self.candidate_piece_count,
            "reference_piece_count": self.reference_piece_count,
            "matched_piece_count": self.matched_piece_count,
            "unmatched_candidate_piece_indices": list(self.unmatched_candidate_piece_indices),
            "unmatched_reference_piece_indices": list(self.unmatched_reference_piece_indices),
            "failed_reference_piece_indices": list(self.failed_reference_piece_indices),
            "mean_deviation_mm": self.mean_deviation_mm,
            "p95_deviation_mm": self.p95_deviation_mm,
            "max_deviation_mm": self.max_deviation_mm,
            "piece_matches": [match.to_json_dict() for match in self.piece_matches],
            "failed_piece_details": [
                detail.to_json_dict() for detail in self.failed_piece_details
            ],
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class SvgShapeEvaluationReport:
    candidate_path_count: int
    reference_path_count: int
    matched_path_count: int
    unmatched_candidate_indices: tuple[int, ...]
    unmatched_reference_indices: tuple[int, ...]
    candidate_normalization_bbox: tuple[float, float, float, float] | None
    reference_normalization_bbox: tuple[float, float, float, float] | None
    mean_deviation_normalized: float | None
    p95_deviation_normalized: float | None
    max_deviation_normalized: float | None
    path_matches: tuple[PathShapeMatch, ...]
    shape_blockers: tuple[str, ...]
    verdict: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "candidate_path_count": self.candidate_path_count,
            "reference_path_count": self.reference_path_count,
            "matched_path_count": self.matched_path_count,
            "unmatched_candidate_indices": list(self.unmatched_candidate_indices),
            "unmatched_reference_indices": list(self.unmatched_reference_indices),
            "candidate_normalization_bbox": (
                list(self.candidate_normalization_bbox)
                if self.candidate_normalization_bbox is not None
                else None
            ),
            "reference_normalization_bbox": (
                list(self.reference_normalization_bbox)
                if self.reference_normalization_bbox is not None
                else None
            ),
            "mean_deviation_normalized": self.mean_deviation_normalized,
            "p95_deviation_normalized": self.p95_deviation_normalized,
            "max_deviation_normalized": self.max_deviation_normalized,
            "path_matches": [match.to_json_dict() for match in self.path_matches],
            "shape_blockers": list(self.shape_blockers),
            "verdict": self.verdict,
        }


@dataclass(frozen=True)
class PieceDeviationMatch:
    candidate_index: int
    reference_index: int
    bbox_iou: float
    mean_deviation_mm: float
    p95_deviation_mm: float
    max_deviation_mm: float
    sample_count: int
    candidate_bbox_mm: tuple[float, float, float, float]
    reference_bbox_mm: tuple[float, float, float, float]
    accepted: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "candidate_index": self.candidate_index,
            "reference_index": self.reference_index,
            "bbox_iou": self.bbox_iou,
            "mean_deviation_mm": self.mean_deviation_mm,
            "p95_deviation_mm": self.p95_deviation_mm,
            "max_deviation_mm": self.max_deviation_mm,
            "sample_count": self.sample_count,
            "candidate_bbox_mm": list(self.candidate_bbox_mm),
            "reference_bbox_mm": list(self.reference_bbox_mm),
            "accepted": self.accepted,
        }


@dataclass(frozen=True)
class SvgPieceDeviationReport:
    candidate_piece_count: int
    reference_piece_count: int
    matched_piece_count: int
    unmatched_candidate_indices: tuple[int, ...]
    unmatched_reference_indices: tuple[int, ...]
    candidate_page_bbox_mm: tuple[float, float, float, float] | None
    reference_page_bbox_mm: tuple[float, float, float, float] | None
    piece_matches: tuple[PieceDeviationMatch, ...]
    tolerance_mm: float
    max_piece_deviation_mm: float | None
    failed_candidate_indices: tuple[int, ...]
    failed_reference_indices: tuple[int, ...]
    blockers: tuple[str, ...]
    delivery_ready: bool
    result_state: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "candidate_piece_count": self.candidate_piece_count,
            "reference_piece_count": self.reference_piece_count,
            "matched_piece_count": self.matched_piece_count,
            "unmatched_candidate_indices": list(self.unmatched_candidate_indices),
            "unmatched_reference_indices": list(self.unmatched_reference_indices),
            "candidate_page_bbox_mm": (
                list(self.candidate_page_bbox_mm) if self.candidate_page_bbox_mm is not None else None
            ),
            "reference_page_bbox_mm": (
                list(self.reference_page_bbox_mm) if self.reference_page_bbox_mm is not None else None
            ),
            "piece_matches": [match.to_json_dict() for match in self.piece_matches],
            "tolerance_mm": self.tolerance_mm,
            "max_piece_deviation_mm": self.max_piece_deviation_mm,
            "failed_candidate_indices": list(self.failed_candidate_indices),
            "failed_reference_indices": list(self.failed_reference_indices),
            "blockers": list(self.blockers),
            "delivery_ready": self.delivery_ready,
            "result_state": self.result_state,
        }


@dataclass(frozen=True)
class _PathShape:
    index: int
    points: tuple[tuple[float, float], ...]
    closed: bool
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class _PieceShape:
    index: int
    points: tuple[tuple[float, float], ...]
    bbox: tuple[float, float, float, float]
    source_tag: str


def evaluate_svg_structure(
    candidate_svg: Path,
    reference_svg: Path,
    *,
    small_object_threshold: float = 2.0,
) -> SvgEvaluationReport:
    """Compare object-level SVG structure between a candidate and reference."""

    candidate = collect_svg_structure_metrics(
        candidate_svg,
        small_object_threshold=small_object_threshold,
    )
    reference = collect_svg_structure_metrics(
        reference_svg,
        small_object_threshold=small_object_threshold,
    )
    object_count_delta = candidate.object_count - reference.object_count
    path_count_delta = candidate.path_count - reference.path_count
    ratio = None
    if reference.object_count > 0:
        ratio = candidate.object_count / reference.object_count
    object_type_deltas = _object_type_deltas(candidate, reference)
    mvp_blockers = _mvp_blockers(candidate, reference)
    return SvgEvaluationReport(
        candidate=candidate,
        reference=reference,
        object_count_delta=object_count_delta,
        path_count_delta=path_count_delta,
        object_type_deltas=object_type_deltas,
        candidate_to_reference_object_ratio=ratio,
        mvp_ready=not mvp_blockers,
        mvp_blockers=mvp_blockers,
        verdict=_structure_verdict(candidate, reference, mvp_blockers),
    )


def evaluate_svg_piece_acceptance(
    candidate_svg: Path,
    reference_svg: Path,
    *,
    tolerance_mm: float = 0.2,
    page_size_mm: tuple[float, float] | None = None,
    match_score_threshold: float = 0.1,
) -> SvgPieceAcceptanceReport:
    """Evaluate final SVG delivery with strict per-piece millimeter tolerances."""

    candidate_pieces = _collect_piece_shapes(candidate_svg)
    reference_pieces = _collect_piece_shapes(reference_svg)
    candidate_viewbox = _svg_viewbox_bbox(candidate_svg)
    reference_viewbox = _svg_viewbox_bbox(reference_svg)
    candidate_page_size = page_size_mm or _viewbox_size(candidate_viewbox)
    reference_page_size = page_size_mm or candidate_page_size
    candidate_pieces_mm = _scale_piece_shapes_to_mm(
        candidate_pieces,
        candidate_viewbox,
        candidate_page_size,
    )
    reference_pieces_mm = _scale_piece_shapes_to_mm(
        reference_pieces,
        reference_viewbox,
        reference_page_size,
    )
    matches, unmatched_candidate, unmatched_reference = _match_piece_shapes(
        candidate_pieces_mm,
        reference_pieces_mm,
        tolerance_mm=tolerance_mm,
        match_score_threshold=match_score_threshold,
    )
    matched_distances = [
        distance
        for match in matches
        for distance in (
            match.mean_deviation_mm,
            match.p95_deviation_mm,
            match.max_deviation_mm,
        )
    ]
    failed_reference_indices = tuple(
        sorted(
            [
                *(match.reference_piece_index for match in matches if not match.accepted),
                *(piece.index for piece in unmatched_reference),
            ]
        )
    )
    failed_piece_details = _failed_piece_details(matches, unmatched_candidate, unmatched_reference)
    blockers = _piece_acceptance_blockers(
        candidate_pieces_mm,
        reference_pieces_mm,
        matches,
        unmatched_candidate,
        unmatched_reference,
    )
    accepted = not blockers
    return SvgPieceAcceptanceReport(
        tolerance_mm=tolerance_mm,
        accepted=accepted,
        result_state=_piece_acceptance_result_state(accepted, matches, unmatched_reference),
        candidate_piece_count=len(candidate_pieces_mm),
        reference_piece_count=len(reference_pieces_mm),
        matched_piece_count=len(matches),
        unmatched_candidate_piece_indices=tuple(piece.index for piece in unmatched_candidate),
        unmatched_reference_piece_indices=tuple(piece.index for piece in unmatched_reference),
        failed_reference_piece_indices=failed_reference_indices,
        mean_deviation_mm=(
            sum(match.mean_deviation_mm for match in matches) / len(matches)
            if matches
            else None
        ),
        p95_deviation_mm=_percentile(matched_distances, 0.95) if matched_distances else None,
        max_deviation_mm=max((match.max_deviation_mm for match in matches), default=None),
        piece_matches=tuple(matches),
        failed_piece_details=failed_piece_details,
        blockers=tuple(blockers),
    )


def evaluate_svg_shape(
    candidate_svg: Path,
    reference_svg: Path,
    *,
    closed_paths_only: bool = True,
    match_score_threshold: float = 0.2,
) -> SvgShapeEvaluationReport:
    """Compare normalized path shapes between a candidate and reference SVG.

    The current sample has different SVG coordinate systems between the scanned output and
    the Illustrator reference. This evaluator therefore normalizes each SVG's path bbox into
    a unit square before matching paths and measuring sampled contour distance.
    """

    candidate_paths = _collect_path_shapes(candidate_svg, closed_paths_only=closed_paths_only)
    reference_paths = _collect_path_shapes(reference_svg, closed_paths_only=closed_paths_only)
    candidate_bbox = _svg_viewbox_bbox(candidate_svg) or _merge_bboxes(
        [path.bbox for path in candidate_paths]
    )
    reference_bbox = _svg_viewbox_bbox(reference_svg) or _merge_bboxes(
        [path.bbox for path in reference_paths]
    )
    normalized_candidate = _normalize_path_shapes(candidate_paths, candidate_bbox)
    normalized_reference = _normalize_path_shapes(reference_paths, reference_bbox)
    matches, unmatched_candidate, unmatched_reference = _match_path_shapes(
        normalized_candidate,
        normalized_reference,
        match_score_threshold=match_score_threshold,
    )
    all_distances = [
        distance
        for match in matches
        for distance in (
            match.mean_deviation_normalized,
            match.p95_deviation_normalized,
            match.max_deviation_normalized,
        )
    ]
    max_deviation = max((match.max_deviation_normalized for match in matches), default=None)
    mean_deviation = (
        sum(match.mean_deviation_normalized for match in matches) / len(matches)
        if matches
        else None
    )
    p95_deviation = _percentile(all_distances, 0.95) if all_distances else None
    blockers = _shape_blockers(
        candidate_paths,
        reference_paths,
        matches,
        unmatched_candidate,
        unmatched_reference,
    )
    return SvgShapeEvaluationReport(
        candidate_path_count=len(candidate_paths),
        reference_path_count=len(reference_paths),
        matched_path_count=len(matches),
        unmatched_candidate_indices=tuple(path.index for path in unmatched_candidate),
        unmatched_reference_indices=tuple(path.index for path in unmatched_reference),
        candidate_normalization_bbox=candidate_bbox,
        reference_normalization_bbox=reference_bbox,
        mean_deviation_normalized=mean_deviation,
        p95_deviation_normalized=p95_deviation,
        max_deviation_normalized=max_deviation,
        path_matches=tuple(matches),
        shape_blockers=tuple(blockers),
        verdict=_shape_verdict(candidate_paths, reference_paths, matches, blockers),
    )


def evaluate_svg_piece_deviation(
    candidate_svg: Path,
    reference_svg: Path,
    *,
    tolerance_mm: float = 0.2,
    closed_paths_only: bool = True,
    match_score_threshold: float = 0.1,
) -> SvgPieceDeviationReport:
    """Compare candidate/reference closed paths in physical millimeter coordinates."""

    candidate_paths, candidate_page_bbox = _collect_path_shapes_in_mm(
        candidate_svg,
        closed_paths_only=closed_paths_only,
    )
    reference_paths, reference_page_bbox = _collect_path_shapes_in_mm(
        reference_svg,
        closed_paths_only=closed_paths_only,
    )
    matches, unmatched_candidate, unmatched_reference = _match_path_shapes(
        candidate_paths,
        reference_paths,
        match_score_threshold=match_score_threshold,
    )
    piece_matches = tuple(
        PieceDeviationMatch(
            candidate_index=match.candidate_index,
            reference_index=match.reference_index,
            bbox_iou=match.bbox_iou,
            mean_deviation_mm=match.mean_deviation_normalized,
            p95_deviation_mm=match.p95_deviation_normalized,
            max_deviation_mm=match.max_deviation_normalized,
            sample_count=match.sample_count,
            candidate_bbox_mm=match.candidate_bbox,
            reference_bbox_mm=match.reference_bbox,
            accepted=match.max_deviation_normalized <= tolerance_mm,
        )
        for match in matches
    )
    failed_candidate_indices = tuple(
        match.candidate_index for match in piece_matches if not match.accepted
    )
    failed_reference_indices = tuple(
        match.reference_index for match in piece_matches if not match.accepted
    )
    blockers = _piece_blockers(
        candidate_paths,
        reference_paths,
        piece_matches,
        unmatched_candidate,
        unmatched_reference,
        tolerance_mm=tolerance_mm,
    )
    max_piece_deviation = max((match.max_deviation_mm for match in piece_matches), default=None)
    delivery_ready = not blockers
    return SvgPieceDeviationReport(
        candidate_piece_count=len(candidate_paths),
        reference_piece_count=len(reference_paths),
        matched_piece_count=len(piece_matches),
        unmatched_candidate_indices=tuple(path.index for path in unmatched_candidate),
        unmatched_reference_indices=tuple(path.index for path in unmatched_reference),
        candidate_page_bbox_mm=candidate_page_bbox,
        reference_page_bbox_mm=reference_page_bbox,
        piece_matches=piece_matches,
        tolerance_mm=tolerance_mm,
        max_piece_deviation_mm=max_piece_deviation,
        failed_candidate_indices=failed_candidate_indices,
        failed_reference_indices=failed_reference_indices,
        blockers=tuple(blockers),
        delivery_ready=delivery_ready,
        result_state=_piece_result_state(delivery_ready),
    )


def collect_svg_structure_metrics(
    svg_path: Path,
    *,
    small_object_threshold: float = 2.0,
) -> SvgStructureMetrics:
    root = ElementTree.parse(svg_path).getroot()
    boxes: list[tuple[float, float, float, float]] = []
    path_count = 0
    closed_path_count = 0
    curved_path_count = 0
    line_count = 0
    rect_count = 0
    polygon_count = 0
    polyline_count = 0
    small_object_count = 0

    for element in root.iter():
        tag = _strip_namespace(element.tag)
        bbox: tuple[float, float, float, float] | None = None
        if tag == "path":
            path_count += 1
            d = element.attrib.get("d", "")
            closed_path_count += int("Z" in d.upper())
            curved_path_count += int(any(command in d for command in ("C", "c", "Q", "q", "S", "s")))
            bbox = _bbox_from_path_data(d)
        elif tag == "line":
            line_count += 1
            bbox = _bbox_from_line(element.attrib)
        elif tag == "rect":
            rect_count += 1
            bbox = _bbox_from_rect(element.attrib)
        elif tag == "polygon":
            polygon_count += 1
            bbox = _bbox_from_points(element.attrib.get("points", ""))
        elif tag == "polyline":
            polyline_count += 1
            bbox = _bbox_from_points(element.attrib.get("points", ""))

        if bbox is None:
            continue
        boxes.append(bbox)
        if _bbox_width(bbox) < small_object_threshold and _bbox_height(bbox) < small_object_threshold:
            small_object_count += 1

    return SvgStructureMetrics(
        path_count=path_count,
        closed_path_count=closed_path_count,
        curved_path_count=curved_path_count,
        line_count=line_count,
        rect_count=rect_count,
        polygon_count=polygon_count,
        polyline_count=polyline_count,
        small_object_count=small_object_count,
        bbox=_merge_bboxes(boxes),
    )


def write_svg_evaluation_report(report: SvgEvaluationReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_svg_shape_evaluation_report(
    report: SvgShapeEvaluationReport,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_svg_piece_deviation_report(
    report: SvgPieceDeviationReport,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_svg_piece_acceptance_report(
    report: SvgPieceAcceptanceReport,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _structure_verdict(
    candidate: SvgStructureMetrics,
    reference: SvgStructureMetrics,
    mvp_blockers: list[str],
) -> str:
    if candidate.object_count == 0:
        return "fail"
    if reference.object_count == 0:
        return "debug-pass"
    if not mvp_blockers:
        return "mvp-pass"
    ratio = candidate.object_count / reference.object_count
    if (
        ratio <= 6
        and candidate.small_object_count <= reference.small_object_count + 5
    ):
        return "debug-pass"
    return "fail"


def _mvp_blockers(
    candidate: SvgStructureMetrics,
    reference: SvgStructureMetrics,
) -> list[str]:
    blockers: list[str] = []
    if reference.object_count == 0:
        return blockers
    ratio = candidate.object_count / reference.object_count
    if ratio < 0.75 or ratio > 1.25:
        blockers.append(
            "candidate object count is not within 25% of the reference object count"
        )
    path_delta = abs(candidate.path_count - reference.path_count)
    line_delta = abs(candidate.line_count - reference.line_count)
    rect_delta = abs(candidate.rect_count - reference.rect_count)
    curved_delta = abs(candidate.curved_path_count - reference.curved_path_count)
    if path_delta > 2:
        blockers.append("path count is not close to the reference path count")
    if line_delta > 3:
        blockers.append("line count is not close to the reference line count")
    if rect_delta > 0:
        blockers.append("rect count does not match the reference rect count")
    if reference.curved_path_count > 0 and curved_delta > 2:
        blockers.append("curved path representation is not close to the reference")
    if reference.path_count > 0 and candidate.path_count == 0:
        blockers.append("reference has paths but candidate has none")
    if reference.line_count > 0 and candidate.line_count == 0:
        blockers.append("reference has line objects but candidate has none")
    if reference.rect_count > 0 and candidate.rect_count == 0:
        blockers.append("reference has rect objects but candidate has none")
    if reference.polygon_count > 0 and candidate.polygon_count == 0:
        blockers.append("reference has polygons but candidate has none")
    if reference.polyline_count > 0 and candidate.polyline_count == 0:
        blockers.append("reference has polylines but candidate has none")
    if candidate.small_object_count > reference.small_object_count + 5:
        blockers.append("candidate contains too many small objects")
    return blockers


def _shape_blockers(
    candidate_paths: tuple[_PathShape, ...],
    reference_paths: tuple[_PathShape, ...],
    matches: list[PathShapeMatch],
    unmatched_candidate: tuple[_PathShape, ...],
    unmatched_reference: tuple[_PathShape, ...],
) -> list[str]:
    blockers: list[str] = []
    if not candidate_paths:
        blockers.append("candidate has no comparable closed paths")
    if not reference_paths:
        blockers.append("reference has no comparable closed paths")
    if reference_paths and len(matches) / len(reference_paths) < 0.8:
        blockers.append("less than 80% of reference paths have a candidate shape match")
    if unmatched_candidate:
        blockers.append("candidate has extra unmatched paths")
    if unmatched_reference:
        blockers.append("reference has unmatched paths")
    if any(match.max_deviation_normalized > 0.08 for match in matches):
        blockers.append("at least one matched path has high normalized contour deviation")
    return blockers


def _shape_verdict(
    candidate_paths: tuple[_PathShape, ...],
    reference_paths: tuple[_PathShape, ...],
    matches: list[PathShapeMatch],
    blockers: list[str],
) -> str:
    if not candidate_paths or not reference_paths:
        return "fail"
    if not blockers:
        return "shape-pass"
    if matches:
        return "shape-debug-pass"
    return "fail"


def _piece_acceptance_blockers(
    candidate_pieces: tuple[_PieceShape, ...],
    reference_pieces: tuple[_PieceShape, ...],
    matches: list[PieceAcceptanceMatch],
    unmatched_candidate: tuple[_PieceShape, ...],
    unmatched_reference: tuple[_PieceShape, ...],
) -> list[str]:
    blockers: list[str] = []
    if not candidate_pieces:
        blockers.append("candidate has no comparable pieces")
    if not reference_pieces:
        blockers.append("reference has no comparable pieces")
    if unmatched_reference:
        blockers.append("reference has unmatched pieces")
    if unmatched_candidate:
        blockers.append("candidate has extra unmatched pieces")
    if any(not match.accepted for match in matches):
        blockers.append("at least one matched piece exceeds tolerance")
    if reference_pieces and len(matches) != len(reference_pieces):
        blockers.append("not every reference piece has a candidate match")
    return blockers


def _failed_piece_details(
    matches: list[PieceAcceptanceMatch],
    unmatched_candidate: tuple[_PieceShape, ...],
    unmatched_reference: tuple[_PieceShape, ...],
) -> tuple[FailedPieceDetail, ...]:
    details: list[FailedPieceDetail] = []
    for match in matches:
        if match.accepted:
            continue
        details.append(
            FailedPieceDetail(
                failure_type="over-tolerance",
                reference_piece_index=match.reference_piece_index,
                candidate_piece_index=match.candidate_piece_index,
                max_deviation_mm=match.max_deviation_mm,
                mean_deviation_mm=match.mean_deviation_mm,
                p95_deviation_mm=match.p95_deviation_mm,
                bbox_iou=match.bbox_iou,
            )
        )
    for piece in unmatched_reference:
        details.append(
            FailedPieceDetail(
                failure_type="unmatched-reference",
                reference_piece_index=piece.index,
                candidate_piece_index=None,
                max_deviation_mm=None,
                mean_deviation_mm=None,
                p95_deviation_mm=None,
                bbox_iou=None,
            )
        )
    for piece in unmatched_candidate:
        details.append(
            FailedPieceDetail(
                failure_type="unmatched-candidate",
                reference_piece_index=None,
                candidate_piece_index=piece.index,
                max_deviation_mm=None,
                mean_deviation_mm=None,
                p95_deviation_mm=None,
                bbox_iou=None,
            )
        )
    return tuple(details)


def _piece_acceptance_result_state(
    accepted: bool,
    matches: list[PieceAcceptanceMatch],
    unmatched_reference: tuple[_PieceShape, ...],
) -> str:
    if accepted:
        return "deliverable-mvp"
    if not matches or unmatched_reference:
        return "continue-development"
    return "internal-test"


def _piece_blockers(
    candidate_paths: tuple[_PathShape, ...],
    reference_paths: tuple[_PathShape, ...],
    matches: tuple[PieceDeviationMatch, ...],
    unmatched_candidate: tuple[_PathShape, ...],
    unmatched_reference: tuple[_PathShape, ...],
    *,
    tolerance_mm: float,
) -> list[str]:
    blockers: list[str] = []
    if not candidate_paths:
        blockers.append("candidate has no comparable closed pieces")
    if not reference_paths:
        blockers.append("reference has no comparable closed pieces")
    if unmatched_candidate:
        blockers.append("candidate has unmatched pieces")
    if unmatched_reference:
        blockers.append("reference has unmatched pieces")
    if any(not match.accepted for match in matches):
        blockers.append(f"at least one matched piece exceeds {tolerance_mm:.3f}mm max deviation")
    if reference_paths and len(matches) != len(reference_paths):
        blockers.append("not every reference piece has a stable candidate match")
    return blockers


def _piece_result_state(delivery_ready: bool) -> str:
    return "deliverable-mvp" if delivery_ready else "internal-preview"


def _object_type_deltas(
    candidate: SvgStructureMetrics,
    reference: SvgStructureMetrics,
) -> dict[str, int]:
    return {
        "path": candidate.path_count - reference.path_count,
        "closed_path": candidate.closed_path_count - reference.closed_path_count,
        "curved_path": candidate.curved_path_count - reference.curved_path_count,
        "line": candidate.line_count - reference.line_count,
        "rect": candidate.rect_count - reference.rect_count,
        "polygon": candidate.polygon_count - reference.polygon_count,
        "polyline": candidate.polyline_count - reference.polyline_count,
        "small_object": candidate.small_object_count - reference.small_object_count,
    }


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _collect_path_shapes(svg_path: Path, *, closed_paths_only: bool) -> tuple[_PathShape, ...]:
    root = ElementTree.parse(svg_path).getroot()
    shapes: list[_PathShape] = []
    path_index = 0
    for element in root.iter():
        if _strip_namespace(element.tag) != "path":
            continue
        path_index += 1
        d = element.attrib.get("d", "")
        points, closed = _points_from_path_data(d)
        if closed_paths_only and not closed:
            continue
        if len(points) < 2:
            continue
        bbox = _bbox_from_points_tuple(points)
        if bbox is None:
            continue
        shapes.append(_PathShape(index=path_index, points=tuple(points), closed=closed, bbox=bbox))
    return tuple(shapes)


def _collect_piece_shapes(svg_path: Path) -> tuple[_PieceShape, ...]:
    root = ElementTree.parse(svg_path).getroot()
    pieces: list[_PieceShape] = []
    piece_index = 0
    for element in root.iter():
        tag = _strip_namespace(element.tag)
        points: tuple[tuple[float, float], ...] | None = None
        if tag == "path":
            path_points, closed = _points_from_path_data(element.attrib.get("d", ""))
            if not closed or len(path_points) < 3:
                continue
            points = tuple(path_points)
        elif tag == "rect":
            points = _rect_points(element.attrib)
        elif tag == "polygon":
            polygon_points = _point_pairs_from_points_attribute(element.attrib.get("points", ""))
            if len(polygon_points) < 3:
                continue
            points = polygon_points
        else:
            continue
        bbox = _bbox_from_points_tuple(points)
        if bbox is None:
            continue
        piece_index += 1
        pieces.append(_PieceShape(index=piece_index, points=points, bbox=bbox, source_tag=tag))
    return tuple(pieces)


def _scale_piece_shapes_to_mm(
    pieces: tuple[_PieceShape, ...],
    viewbox: tuple[float, float, float, float] | None,
    page_size_mm: tuple[float, float] | None,
) -> tuple[_PieceShape, ...]:
    if viewbox is None or page_size_mm is None:
        return pieces
    xmin, ymin, xmax, ymax = viewbox
    viewbox_width = xmax - xmin
    viewbox_height = ymax - ymin
    page_width_mm, page_height_mm = page_size_mm
    if viewbox_width <= 0 or viewbox_height <= 0 or page_width_mm <= 0 or page_height_mm <= 0:
        return pieces
    x_scale = page_width_mm / viewbox_width
    y_scale = page_height_mm / viewbox_height
    scaled: list[_PieceShape] = []
    for piece in pieces:
        points = tuple(((x - xmin) * x_scale, (y - ymin) * y_scale) for x, y in piece.points)
        bbox = _bbox_from_points_tuple(points)
        if bbox is None:
            continue
        scaled.append(
            _PieceShape(
                index=piece.index,
                points=points,
                bbox=bbox,
                source_tag=piece.source_tag,
            )
        )
    return tuple(scaled)


def _match_piece_shapes(
    candidate_pieces: tuple[_PieceShape, ...],
    reference_pieces: tuple[_PieceShape, ...],
    *,
    tolerance_mm: float,
    match_score_threshold: float,
) -> tuple[list[PieceAcceptanceMatch], tuple[_PieceShape, ...], tuple[_PieceShape, ...]]:
    pairs: list[tuple[float, _PieceShape, _PieceShape]] = []
    for candidate in candidate_pieces:
        for reference in reference_pieces:
            pairs.append((_bbox_match_score(candidate.bbox, reference.bbox), candidate, reference))
    pairs.sort(key=lambda item: item[0], reverse=True)

    used_candidates: set[int] = set()
    used_references: set[int] = set()
    matches: list[PieceAcceptanceMatch] = []
    for score, candidate, reference in pairs:
        if score < match_score_threshold:
            break
        if candidate.index in used_candidates or reference.index in used_references:
            continue
        used_candidates.add(candidate.index)
        used_references.add(reference.index)
        distances = _bidirectional_piece_distances(candidate, reference)
        max_deviation = max(distances) if distances else 0.0
        matches.append(
            PieceAcceptanceMatch(
                candidate_piece_index=candidate.index,
                reference_piece_index=reference.index,
                accepted=max_deviation <= tolerance_mm,
                bbox_iou=_bbox_iou(candidate.bbox, reference.bbox),
                mean_deviation_mm=sum(distances) / len(distances) if distances else 0.0,
                p95_deviation_mm=_percentile(distances, 0.95) if distances else 0.0,
                max_deviation_mm=max_deviation,
                sample_count=len(distances),
                candidate_bbox_mm=candidate.bbox,
                reference_bbox_mm=reference.bbox,
            )
        )

    unmatched_candidate = tuple(
        piece for piece in candidate_pieces if piece.index not in used_candidates
    )
    unmatched_reference = tuple(
        piece for piece in reference_pieces if piece.index not in used_references
    )
    matches.sort(key=lambda match: match.reference_piece_index)
    return matches, unmatched_candidate, unmatched_reference


def _bidirectional_piece_distances(candidate: _PieceShape, reference: _PieceShape) -> list[float]:
    candidate_samples = _resample_points(candidate.points, closed=True, target_spacing=0.2)
    reference_samples = _resample_points(reference.points, closed=True, target_spacing=0.2)
    if len(candidate_samples) < 2 or len(reference_samples) < 2:
        return []
    return [
        *[_point_to_polyline_distance(point, reference_samples, closed=True) for point in candidate_samples],
        *[_point_to_polyline_distance(point, candidate_samples, closed=True) for point in reference_samples],
    ]


def _viewbox_size(
    viewbox: tuple[float, float, float, float] | None,
) -> tuple[float, float] | None:
    if viewbox is None:
        return None
    return (viewbox[2] - viewbox[0], viewbox[3] - viewbox[1])


def _rect_points(attributes: dict[str, str]) -> tuple[tuple[float, float], ...] | None:
    try:
        x = float(attributes.get("x", "0"))
        y = float(attributes.get("y", "0"))
        width = float(attributes["width"])
        height = float(attributes["height"])
    except (KeyError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    return ((x, y), (x + width, y), (x + width, y + height), (x, y + height))


def _point_pairs_from_points_attribute(points: str) -> tuple[tuple[float, float], ...]:
    numbers = [float(value) for value in _NUMBER_RE.findall(points)]
    return tuple(zip(numbers[0::2], numbers[1::2], strict=False))


def _collect_path_shapes_in_mm(
    svg_path: Path,
    *,
    closed_paths_only: bool,
) -> tuple[tuple[_PathShape, ...], tuple[float, float, float, float] | None]:
    root = ElementTree.parse(svg_path).getroot()
    page_bbox = _svg_page_bbox_mm(root)
    scale_x, scale_y = _svg_units_to_mm(root)
    viewbox = _svg_viewbox_bbox_from_root(root)
    viewbox_x = viewbox[0] if viewbox is not None else 0.0
    viewbox_y = viewbox[1] if viewbox is not None else 0.0
    shapes: list[_PathShape] = []
    path_index = 0
    for element in root.iter():
        if _strip_namespace(element.tag) != "path":
            continue
        path_index += 1
        d = element.attrib.get("d", "")
        points, closed = _points_from_path_data(d)
        if closed_paths_only and not closed:
            continue
        if len(points) < 2:
            continue
        mm_points = tuple(
            (
                (x - viewbox_x) * scale_x,
                (y - viewbox_y) * scale_y,
            )
            for x, y in points
        )
        bbox = _bbox_from_points_tuple(mm_points)
        if bbox is None:
            continue
        shapes.append(_PathShape(index=path_index, points=mm_points, closed=closed, bbox=bbox))
    return tuple(shapes), page_bbox


def _svg_viewbox_bbox(svg_path: Path) -> tuple[float, float, float, float] | None:
    root = ElementTree.parse(svg_path).getroot()
    return _svg_viewbox_bbox_from_root(root)


def _svg_viewbox_bbox_from_root(root: ElementTree.Element) -> tuple[float, float, float, float] | None:
    view_box = root.attrib.get("viewBox")
    if not view_box:
        return None
    values = [float(value) for value in _NUMBER_RE.findall(view_box)]
    if len(values) != 4:
        return None
    x, y, width, height = values
    if width <= 0 or height <= 0:
        return None
    return (x, y, x + width, y + height)


def _svg_page_bbox_mm(root: ElementTree.Element) -> tuple[float, float, float, float] | None:
    viewbox = _svg_viewbox_bbox_from_root(root)
    if viewbox is None:
        return None
    scale_x, scale_y = _svg_units_to_mm(root)
    return (0.0, 0.0, (viewbox[2] - viewbox[0]) * scale_x, (viewbox[3] - viewbox[1]) * scale_y)


def _svg_units_to_mm(root: ElementTree.Element) -> tuple[float, float]:
    viewbox = _svg_viewbox_bbox_from_root(root)
    if viewbox is None:
        return (1.0, 1.0)
    viewbox_width = viewbox[2] - viewbox[0]
    viewbox_height = viewbox[3] - viewbox[1]
    width_mm = _parse_svg_length_mm(root.attrib.get("width"))
    height_mm = _parse_svg_length_mm(root.attrib.get("height"))
    if width_mm is not None and height_mm is not None and viewbox_width > 0 and viewbox_height > 0:
        return (width_mm / viewbox_width, height_mm / viewbox_height)
    # Illustrator reference SVG omits width/height but uses PDF-like pt user units.
    if viewbox_width > 500 and viewbox_height > 500:
        point_to_mm = 25.4 / 72.0
        return (point_to_mm, point_to_mm)
    return (1.0, 1.0)


def _parse_svg_length_mm(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip().lower()
    if value.endswith("mm"):
        return float(value[:-2])
    if value.endswith("pt"):
        return float(value[:-2]) * 25.4 / 72.0
    if value.endswith("px"):
        return None
    if re.fullmatch(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", value):
        return None
    return None


def _normalize_path_shapes(
    paths: tuple[_PathShape, ...],
    bbox: tuple[float, float, float, float] | None,
) -> tuple[_PathShape, ...]:
    if bbox is None:
        return ()
    xmin, ymin, xmax, ymax = bbox
    width = xmax - xmin
    height = ymax - ymin
    if width <= 0 or height <= 0:
        return ()
    normalized: list[_PathShape] = []
    for path in paths:
        points = tuple(((x - xmin) / width, (y - ymin) / height) for x, y in path.points)
        normalized_bbox = _bbox_from_points_tuple(points)
        if normalized_bbox is None:
            continue
        normalized.append(
            _PathShape(
                index=path.index,
                points=points,
                closed=path.closed,
                bbox=normalized_bbox,
            )
        )
    return tuple(normalized)


def _match_path_shapes(
    candidate_paths: tuple[_PathShape, ...],
    reference_paths: tuple[_PathShape, ...],
    *,
    match_score_threshold: float,
) -> tuple[list[PathShapeMatch], tuple[_PathShape, ...], tuple[_PathShape, ...]]:
    pairs: list[tuple[float, _PathShape, _PathShape]] = []
    for candidate in candidate_paths:
        for reference in reference_paths:
            pairs.append((_bbox_match_score(candidate.bbox, reference.bbox), candidate, reference))
    pairs.sort(key=lambda item: item[0], reverse=True)

    used_candidates: set[int] = set()
    used_references: set[int] = set()
    matches: list[PathShapeMatch] = []
    for score, candidate, reference in pairs:
        if score < match_score_threshold:
            break
        if candidate.index in used_candidates or reference.index in used_references:
            continue
        used_candidates.add(candidate.index)
        used_references.add(reference.index)
        distances = _bidirectional_path_distances(candidate, reference)
        matches.append(
            PathShapeMatch(
                candidate_index=candidate.index,
                reference_index=reference.index,
                bbox_iou=_bbox_iou(candidate.bbox, reference.bbox),
                mean_deviation_normalized=sum(distances) / len(distances) if distances else 0.0,
                p95_deviation_normalized=_percentile(distances, 0.95) if distances else 0.0,
                max_deviation_normalized=max(distances) if distances else 0.0,
                sample_count=len(distances),
                candidate_bbox=candidate.bbox,
                reference_bbox=reference.bbox,
            )
        )

    unmatched_candidate = tuple(
        path for path in candidate_paths if path.index not in used_candidates
    )
    unmatched_reference = tuple(
        path for path in reference_paths if path.index not in used_references
    )
    matches.sort(key=lambda match: match.reference_index)
    return matches, unmatched_candidate, unmatched_reference


def _bbox_match_score(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    iou = _bbox_iou(a, b)
    a_center = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
    b_center = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    center_distance = math.hypot(a_center[0] - b_center[0], a_center[1] - b_center[1])
    size_distance = math.hypot((a[2] - a[0]) - (b[2] - b[0]), (a[3] - a[1]) - (b[3] - b[1]))
    proximity = 1 / (1 + center_distance + size_distance)
    return (0.7 * iou) + (0.3 * proximity)


def _bidirectional_path_distances(candidate: _PathShape, reference: _PathShape) -> list[float]:
    candidate_samples = _resample_points(candidate.points, closed=candidate.closed)
    reference_samples = _resample_points(reference.points, closed=reference.closed)
    if len(candidate_samples) < 2 or len(reference_samples) < 2:
        return []
    return [
        *[_point_to_polyline_distance(point, reference_samples, closed=reference.closed) for point in candidate_samples],
        *[_point_to_polyline_distance(point, candidate_samples, closed=candidate.closed) for point in reference_samples],
    ]


def _resample_points(
    points: tuple[tuple[float, float], ...],
    *,
    closed: bool,
    target_spacing: float = 0.006,
) -> tuple[tuple[float, float], ...]:
    if len(points) < 2:
        return points
    segments = _segments(points, closed=closed)
    segment_lengths = [
        math.hypot(end[0] - start[0], end[1] - start[1])
        for start, end in segments
    ]
    total_length = sum(segment_lengths)
    if total_length <= 0:
        return (points[0],)
    samples: list[tuple[float, float]] = []
    sample_count = max(1, math.ceil(total_length / target_spacing))
    target_distances = [index * target_spacing for index in range(sample_count)]
    if not closed:
        target_distances.append(total_length)
    segment_index = 0
    segment_start_distance = 0.0
    for target_distance in target_distances:
        while (
            segment_index < len(segments) - 1
            and segment_start_distance + segment_lengths[segment_index] < target_distance
        ):
            segment_start_distance += segment_lengths[segment_index]
            segment_index += 1
        start, end = segments[segment_index]
        length = segment_lengths[segment_index]
        fraction = 0.0 if length <= 0 else (target_distance - segment_start_distance) / length
        fraction = max(0.0, min(1.0, fraction))
        samples.append(
            (
                start[0] + (end[0] - start[0]) * fraction,
                start[1] + (end[1] - start[1]) * fraction,
            )
        )
    return tuple(samples)


def _point_to_polyline_distance(
    point: tuple[float, float],
    polyline: tuple[tuple[float, float], ...],
    *,
    closed: bool,
) -> float:
    return min(
        _point_to_segment_distance(point, start, end)
        for start, end in _segments(polyline, closed=closed)
    )


def _segments(
    points: tuple[tuple[float, float], ...],
    *,
    closed: bool,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    if len(points) < 2:
        return []
    segment_count = len(points) if closed else len(points) - 1
    return [
        (points[index], points[(index + 1) % len(points)])
        for index in range(segment_count)
    ]


def _point_to_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0 and dy == 0:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    projection = (start[0] + t * dx, start[1] + t * dy)
    return math.hypot(point[0] - projection[0], point[1] - projection[1])


def _points_from_path_data(d: str) -> tuple[list[tuple[float, float]], bool]:
    points: list[tuple[float, float]] = []
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    command = ""
    previous_cubic_control: tuple[float, float] | None = None
    previous_quadratic_control: tuple[float, float] | None = None
    closed = False
    tokens = _PATH_TOKEN_RE.findall(d)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if _is_path_command(token):
            command = token
            index += 1
            if command in {"Z", "z"}:
                current = start
                closed = True
            continue
        if not command:
            index += 1
            continue

        upper = command.upper()
        relative = command.islower()
        if upper == "M":
            point, index = _read_point(tokens, index, relative=relative, current=current)
            current = point
            start = point
            points.append(point)
            command = "l" if relative else "L"
            previous_cubic_control = None
            previous_quadratic_control = None
        elif upper == "L":
            point, index = _read_point(tokens, index, relative=relative, current=current)
            points.append(point)
            current = point
            previous_cubic_control = None
            previous_quadratic_control = None
        elif upper == "H":
            value, index = _read_number(tokens, index)
            x = current[0] + value if relative else value
            current = (x, current[1])
            points.append(current)
            previous_cubic_control = None
            previous_quadratic_control = None
        elif upper == "V":
            value, index = _read_number(tokens, index)
            y = current[1] + value if relative else value
            current = (current[0], y)
            points.append(current)
            previous_cubic_control = None
            previous_quadratic_control = None
        elif upper == "C":
            values, index = _read_numbers(tokens, index, 6)
            control1 = _path_point(values[0], values[1], relative=relative, current=current)
            control2 = _path_point(values[2], values[3], relative=relative, current=current)
            end = _path_point(values[4], values[5], relative=relative, current=current)
            points.extend(_sample_cubic(current, control1, control2, end))
            current = end
            previous_cubic_control = control2
            previous_quadratic_control = None
        elif upper == "S":
            values, index = _read_numbers(tokens, index, 4)
            control1 = _reflect_point(previous_cubic_control, current)
            control2 = _path_point(values[0], values[1], relative=relative, current=current)
            end = _path_point(values[2], values[3], relative=relative, current=current)
            points.extend(_sample_cubic(current, control1, control2, end))
            current = end
            previous_cubic_control = control2
            previous_quadratic_control = None
        elif upper == "Q":
            values, index = _read_numbers(tokens, index, 4)
            control = _path_point(values[0], values[1], relative=relative, current=current)
            end = _path_point(values[2], values[3], relative=relative, current=current)
            points.extend(_sample_quadratic(current, control, end))
            current = end
            previous_cubic_control = None
            previous_quadratic_control = control
        elif upper == "T":
            values, index = _read_numbers(tokens, index, 2)
            control = _reflect_point(previous_quadratic_control, current)
            end = _path_point(values[0], values[1], relative=relative, current=current)
            points.extend(_sample_quadratic(current, control, end))
            current = end
            previous_cubic_control = None
            previous_quadratic_control = control
        elif upper == "A":
            values, index = _read_numbers(tokens, index, 7)
            point = _path_point(values[5], values[6], relative=relative, current=current)
            current = point
            points.append(point)
            previous_cubic_control = None
            previous_quadratic_control = None
        else:
            index += 1
    return points, closed


def _bbox_from_path_data(d: str) -> tuple[float, float, float, float] | None:
    points: list[tuple[float, float]] = []
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    command = ""
    tokens = _PATH_TOKEN_RE.findall(d)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if _is_path_command(token):
            command = token
            index += 1
            if command in {"Z", "z"}:
                current = start
            continue
        if not command:
            index += 1
            continue

        upper = command.upper()
        relative = command.islower()
        if upper == "M":
            point, index = _read_point(tokens, index, relative=relative, current=current)
            current = point
            start = point
            points.append(point)
            command = "l" if relative else "L"
        elif upper == "L":
            point, index = _read_point(tokens, index, relative=relative, current=current)
            current = point
            points.append(point)
        elif upper == "H":
            value, index = _read_number(tokens, index)
            x = current[0] + value if relative else value
            current = (x, current[1])
            points.append(current)
        elif upper == "V":
            value, index = _read_number(tokens, index)
            y = current[1] + value if relative else value
            current = (current[0], y)
            points.append(current)
        elif upper in {"C", "S", "Q", "T"}:
            parameter_count = {"C": 6, "S": 4, "Q": 4, "T": 2}[upper]
            values, index = _read_numbers(tokens, index, parameter_count)
            for value_index in range(0, len(values), 2):
                point = (values[value_index], values[value_index + 1])
                if relative:
                    point = (current[0] + point[0], current[1] + point[1])
                points.append(point)
            current = points[-1]
        elif upper == "A":
            values, index = _read_numbers(tokens, index, 7)
            point = (values[5], values[6])
            if relative:
                point = (current[0] + point[0], current[1] + point[1])
            current = point
            points.append(point)
        else:
            index += 1

    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _bbox_from_points(points: str) -> tuple[float, float, float, float] | None:
    numbers = [float(value) for value in _NUMBER_RE.findall(points)]
    return _bbox_from_number_pairs(numbers)


def _bbox_from_points_tuple(
    points: tuple[tuple[float, float], ...] | list[tuple[float, float]],
) -> tuple[float, float, float, float] | None:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _bbox_from_line(attributes: dict[str, str]) -> tuple[float, float, float, float] | None:
    try:
        x1 = float(attributes["x1"])
        y1 = float(attributes["y1"])
        x2 = float(attributes["x2"])
        y2 = float(attributes["y2"])
    except (KeyError, ValueError):
        return None
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def _bbox_from_rect(attributes: dict[str, str]) -> tuple[float, float, float, float] | None:
    try:
        x = float(attributes.get("x", "0"))
        y = float(attributes.get("y", "0"))
        width = float(attributes["width"])
        height = float(attributes["height"])
    except (KeyError, ValueError):
        return None
    return (x, y, x + width, y + height)


def _bbox_from_number_pairs(numbers: list[float]) -> tuple[float, float, float, float] | None:
    if len(numbers) < 2:
        return None
    xs = numbers[0::2]
    ys = numbers[1::2]
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _is_path_command(token: str) -> bool:
    return len(token) == 1 and token.isalpha()


def _read_number(tokens: list[str], index: int) -> tuple[float, int]:
    if index >= len(tokens) or _is_path_command(tokens[index]):
        raise ValueError("Expected SVG path number.")
    return float(tokens[index]), index + 1


def _read_numbers(tokens: list[str], index: int, count: int) -> tuple[list[float], int]:
    values: list[float] = []
    for _ in range(count):
        value, index = _read_number(tokens, index)
        values.append(value)
    return values, index


def _read_point(
    tokens: list[str],
    index: int,
    *,
    relative: bool,
    current: tuple[float, float],
) -> tuple[tuple[float, float], int]:
    values, index = _read_numbers(tokens, index, 2)
    point = (values[0], values[1])
    if relative:
        point = (current[0] + point[0], current[1] + point[1])
    return point, index


def _path_point(
    x: float,
    y: float,
    *,
    relative: bool,
    current: tuple[float, float],
) -> tuple[float, float]:
    if relative:
        return (current[0] + x, current[1] + y)
    return (x, y)


def _reflect_point(
    control: tuple[float, float] | None,
    current: tuple[float, float],
) -> tuple[float, float]:
    if control is None:
        return current
    return (2 * current[0] - control[0], 2 * current[1] - control[1])


def _sample_cubic(
    start: tuple[float, float],
    control1: tuple[float, float],
    control2: tuple[float, float],
    end: tuple[float, float],
    *,
    steps: int = 12,
) -> list[tuple[float, float]]:
    return [
        _cubic_point(start, control1, control2, end, step / steps)
        for step in range(1, steps + 1)
    ]


def _sample_quadratic(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    *,
    steps: int = 12,
) -> list[tuple[float, float]]:
    return [
        _quadratic_point(start, control, end, step / steps)
        for step in range(1, steps + 1)
    ]


def _cubic_point(
    start: tuple[float, float],
    control1: tuple[float, float],
    control2: tuple[float, float],
    end: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    inverse = 1 - t
    return (
        inverse**3 * start[0]
        + 3 * inverse**2 * t * control1[0]
        + 3 * inverse * t**2 * control2[0]
        + t**3 * end[0],
        inverse**3 * start[1]
        + 3 * inverse**2 * t * control1[1]
        + 3 * inverse * t**2 * control2[1]
        + t**3 * end[1],
    )


def _quadratic_point(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    inverse = 1 - t
    return (
        inverse**2 * start[0] + 2 * inverse * t * control[0] + t**2 * end[0],
        inverse**2 * start[1] + 2 * inverse * t * control[1] + t**2 * end[1],
    )


def _merge_bboxes(
    boxes: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float] | None:
    if not boxes:
        return None
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _bbox_width(bbox: tuple[float, float, float, float]) -> float:
    return bbox[2] - bbox[0]


def _bbox_height(bbox: tuple[float, float, float, float]) -> float:
    return bbox[3] - bbox[1]


def _bbox_iou(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    x_overlap = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    y_overlap = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = x_overlap * y_overlap
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(0, round((len(sorted_values) - 1) * percentile)))
    return sorted_values[index]
