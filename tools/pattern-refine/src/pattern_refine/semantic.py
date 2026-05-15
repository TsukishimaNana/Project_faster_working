"""Object-level geometry reconstruction helpers."""

from __future__ import annotations

import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pattern_refine.geometry import GeometryObject, LineGeometry, PathGeometry, Point, RectGeometry
from pattern_refine.orientation import PageCoordinateTransform, transform_geometry
from pattern_refine.scale import ScaleDetectionReport


@dataclass(frozen=True)
class CenterlinePieceDiagnostic:
    reference_index: int
    reference_area_mm2: float
    reference_perimeter_mm: float
    matched: bool
    source: str | None
    score: float | None
    candidate_area_mm2: float | None
    candidate_perimeter_mm: float | None
    candidate_bounds_mm: tuple[float, float, float, float] | None = None
    reference_bounds_mm: tuple[float, float, float, float] | None = None
    rejected_source: str | None = None
    rejected_reason: str | None = None
    rejected_candidate_area_mm2: float | None = None
    rejected_candidate_perimeter_mm: float | None = None
    rejected_candidate_bounds_mm: tuple[float, float, float, float] | None = None
    rejected_distance_summary_mm: tuple[float, float, float] | None = None
    candidate_geometry: PathGeometry | None = None
    reference_geometry: PathGeometry | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "reference_index": self.reference_index,
            "reference_area_mm2": self.reference_area_mm2,
            "reference_perimeter_mm": self.reference_perimeter_mm,
            "matched": self.matched,
            "source": self.source,
            "score": self.score,
            "candidate_area_mm2": self.candidate_area_mm2,
            "candidate_perimeter_mm": self.candidate_perimeter_mm,
            "candidate_bounds_mm": (
                list(self.candidate_bounds_mm) if self.candidate_bounds_mm is not None else None
            ),
            "reference_bounds_mm": (
                list(self.reference_bounds_mm) if self.reference_bounds_mm is not None else None
            ),
            "rejected_source": self.rejected_source,
            "rejected_reason": self.rejected_reason,
            "rejected_candidate_area_mm2": self.rejected_candidate_area_mm2,
            "rejected_candidate_perimeter_mm": self.rejected_candidate_perimeter_mm,
            "rejected_candidate_bounds_mm": (
                list(self.rejected_candidate_bounds_mm)
                if self.rejected_candidate_bounds_mm is not None
                else None
            ),
            "rejected_distance_summary_mm": (
                list(self.rejected_distance_summary_mm)
                if self.rejected_distance_summary_mm is not None
                else None
            ),
        }


@dataclass(frozen=True)
class SemanticGeometryReport:
    source_path_count: int
    path_count: int
    line_count: int
    rect_count: int
    promoted_line_count: int
    promoted_rect_count: int
    reconstructed_scale_line_count: int
    deduplicated_line_count: int
    discarded_small_path_count: int
    centerline_candidate_count: int = 0
    centerline_closed_candidate_count: int = 0
    centerline_piece_candidate_count: int = 0
    centerline_replacement_applied: bool = False
    centerline_reference_path_count: int = 0
    centerline_missing_reference_count: int = 0
    centerline_piece_diagnostics: tuple[CenterlinePieceDiagnostic, ...] = ()

    @property
    def object_count(self) -> int:
        return self.path_count + self.line_count + self.rect_count

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "source_path_count": self.source_path_count,
            "object_count": self.object_count,
            "path_count": self.path_count,
            "line_count": self.line_count,
            "rect_count": self.rect_count,
            "promoted_line_count": self.promoted_line_count,
            "promoted_rect_count": self.promoted_rect_count,
            "reconstructed_scale_line_count": self.reconstructed_scale_line_count,
            "deduplicated_line_count": self.deduplicated_line_count,
            "discarded_small_path_count": self.discarded_small_path_count,
            "centerline_candidate_count": self.centerline_candidate_count,
            "centerline_closed_candidate_count": self.centerline_closed_candidate_count,
            "centerline_piece_candidate_count": self.centerline_piece_candidate_count,
            "centerline_replacement_applied": self.centerline_replacement_applied,
            "centerline_reference_path_count": self.centerline_reference_path_count,
            "centerline_missing_reference_count": self.centerline_missing_reference_count,
            "centerline_piece_diagnostics": [
                diagnostic.to_json_dict() for diagnostic in self.centerline_piece_diagnostics
            ],
        }


def reconstruct_semantic_geometries(
    geometries: tuple[PathGeometry, ...],
    *,
    centerline_geometries: tuple[PathGeometry, ...] = (),
    scale_report: ScaleDetectionReport | None = None,
    page_transform: PageCoordinateTransform | None = None,
) -> tuple[tuple[GeometryObject, ...], SemanticGeometryReport]:
    """Promote obvious contour paths into typed geometry objects.

    This is intentionally conservative. It only promotes shapes whose geometry is already
    unambiguous, leaving pattern-piece outlines as paths for later centerline and curve work.
    """

    semantic: list[GeometryObject] = []
    promoted_lines: list[LineGeometry] = []
    promoted_line_count = 0
    promoted_rect_count = 0
    deduplicated_line_count = 0
    discarded_small_path_count = 0
    centerline_candidate_count = len(centerline_geometries)
    centerline_closed_candidate_count = sum(path.closed for path in centerline_geometries)
    centerline_piece_candidate_count = 0
    centerline_replacement_applied = False
    centerline_reference_path_count = 0
    centerline_missing_reference_count = 0
    centerline_piece_diagnostics: tuple[CenterlinePieceDiagnostic, ...] = ()
    deferred_outline_paths: list[PathGeometry] = []
    for geometry in geometries:
        line = _promote_linear_contour(geometry)
        if line is not None:
            semantic.append(line)
            promoted_lines.append(line)
            promoted_line_count += 1
            continue
        if _is_compact_nonproduction_path(geometry):
            discarded_small_path_count += 1
            continue
        rect = _promote_rect_contour(geometry)
        if rect is not None:
            semantic.append(rect)
            promoted_rect_count += 1
            continue
        deferred_outline_paths.append(geometry)

    if centerline_geometries:
        centerline_paths, centerline_piece_diagnostics = _major_centerline_paths_with_diagnostics(
            centerline_geometries,
            reference_paths=deferred_outline_paths,
        )
        centerline_reference_path_count = len(deferred_outline_paths)
        centerline_piece_candidate_count = len(centerline_paths)
        centerline_missing_reference_count = max(
            0,
            centerline_reference_path_count - centerline_piece_candidate_count,
        )
        if _centerline_replacement_is_viable(centerline_paths, deferred_outline_paths):
            semantic.extend(centerline_paths)
            centerline_replacement_applied = True
        else:
            semantic.extend(deferred_outline_paths)
    else:
        semantic.extend(deferred_outline_paths)

    reconstructed_scale_lines = _scale_marker_lines(scale_report, page_transform=page_transform)
    semantic, overlapping_promoted_line_count = _without_overlapping_scale_lines(
        semantic,
        reconstructed_scale_lines,
    )
    deduplicated_line_count += overlapping_promoted_line_count
    for line in reconstructed_scale_lines:
        if _has_similar_line(semantic, line):
            deduplicated_line_count += 1
            continue
        semantic.append(line)
    promoted_scale_ticks = _promoted_scale_marker_ticks(promoted_lines, semantic)
    for line in promoted_scale_ticks:
        if _has_similar_line(semantic, line):
            deduplicated_line_count += 1
            continue
        semantic.append(line)

    report = SemanticGeometryReport(
        source_path_count=len(geometries),
        path_count=sum(isinstance(geometry, PathGeometry) for geometry in semantic),
        line_count=sum(isinstance(geometry, LineGeometry) for geometry in semantic),
        rect_count=sum(isinstance(geometry, RectGeometry) for geometry in semantic),
        promoted_line_count=promoted_line_count,
        promoted_rect_count=promoted_rect_count,
        reconstructed_scale_line_count=(
            len(reconstructed_scale_lines)
            + len(promoted_scale_ticks)
            - deduplicated_line_count
        ),
        deduplicated_line_count=deduplicated_line_count,
        discarded_small_path_count=discarded_small_path_count,
        centerline_candidate_count=centerline_candidate_count,
        centerline_closed_candidate_count=centerline_closed_candidate_count,
        centerline_piece_candidate_count=centerline_piece_candidate_count,
        centerline_replacement_applied=centerline_replacement_applied,
        centerline_reference_path_count=centerline_reference_path_count,
        centerline_missing_reference_count=centerline_missing_reference_count,
        centerline_piece_diagnostics=centerline_piece_diagnostics,
    )
    return tuple(semantic), report


def write_semantic_geometry_report(report: SemanticGeometryReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _promote_linear_contour(geometry: PathGeometry) -> LineGeometry | None:
    xmin, ymin, xmax, ymax = geometry.bounds
    width = xmax - xmin
    height = ymax - ymin
    long_side = max(width, height)
    short_side = min(width, height)
    if long_side < 20.0 or short_side > 3.0:
        return None
    if width >= height:
        y = (ymin + ymax) / 2
        return LineGeometry(start=Point(xmin, y), end=Point(xmax, y))
    x = (xmin + xmax) / 2
    return LineGeometry(start=Point(x, ymin), end=Point(x, ymax))


def _promote_rect_contour(geometry: PathGeometry) -> RectGeometry | None:
    if not geometry.closed:
        return None
    xmin, ymin, xmax, ymax = geometry.bounds
    width = xmax - xmin
    height = ymax - ymin
    if width < 15.0 or height < 15.0:
        return None
    aspect_ratio = max(width, height) / min(width, height)
    if aspect_ratio > 6.0:
        return None
    bbox_area = width * height
    if bbox_area <= 0:
        return None
    area_ratio = geometry.area_mm2 / bbox_area
    if 0.9 <= area_ratio <= 1.05:
        return RectGeometry(x_mm=xmin, y_mm=ymin, width_mm=width, height_mm=height)
    if _edge_aligned_ratio(geometry) < 0.75:
        return None
    if _covered_bbox_corner_count(geometry) < 4:
        return None
    return RectGeometry(x_mm=xmin, y_mm=ymin, width_mm=width, height_mm=height)


def _major_centerline_paths(
    centerline_geometries: tuple[PathGeometry, ...],
    *,
    reference_paths: list[PathGeometry],
) -> tuple[PathGeometry, ...]:
    centerlines, _ = _major_centerline_paths_with_diagnostics(
        centerline_geometries,
        reference_paths=reference_paths,
    )
    return centerlines


def _major_centerline_paths_with_diagnostics(
    centerline_geometries: tuple[PathGeometry, ...],
    *,
    reference_paths: list[PathGeometry],
) -> tuple[tuple[PathGeometry, ...], tuple[CenterlinePieceDiagnostic, ...]]:
    if not reference_paths:
        return (), ()
    candidates: list[PathGeometry] = []
    diagnostics: list[CenterlinePieceDiagnostic] = []
    used_centerline_indices: set[int] = set()
    sorted_references = sorted(reference_paths, key=lambda path: path.area_mm2, reverse=True)
    for reference_index, reference in enumerate(sorted_references, start=1):
        local_paths = [
            (index, path)
            for index, path in enumerate(centerline_geometries)
            if index not in used_centerline_indices
            and _centerline_path_is_local_to_reference(path, reference)
        ]
        best = _best_piecewise_centerline_candidate(reference, local_paths)
        if best is None:
            rejected = _best_rejected_piecewise_centerline_candidate(reference, local_paths)
            rejected_source: str | None = None
            rejected_reason: str | None = None
            rejected_candidate: PathGeometry | None = None
            rejected_distances: tuple[float, float, float] | None = None
            if rejected is not None:
                rejected_source, rejected_candidate, rejected_reason, rejected_distances = rejected
            diagnostics.append(
                CenterlinePieceDiagnostic(
                    reference_index=reference_index,
                    reference_area_mm2=reference.area_mm2,
                    reference_perimeter_mm=reference.perimeter_mm,
                    matched=False,
                    source=None,
                    score=None,
                    candidate_area_mm2=None,
                    candidate_perimeter_mm=None,
                    candidate_bounds_mm=None,
                    reference_bounds_mm=reference.bounds,
                    rejected_source=rejected_source,
                    rejected_reason=rejected_reason,
                    rejected_candidate_area_mm2=(
                        rejected_candidate.area_mm2 if rejected_candidate is not None else None
                    ),
                    rejected_candidate_perimeter_mm=(
                        rejected_candidate.perimeter_mm if rejected_candidate is not None else None
                    ),
                    rejected_candidate_bounds_mm=(
                        rejected_candidate.bounds if rejected_candidate is not None else None
                    ),
                    rejected_distance_summary_mm=rejected_distances,
                    candidate_geometry=None,
                    reference_geometry=reference,
                )
            )
            continue
        score, indices, centerline, source = best
        used_centerline_indices.update(indices)
        candidates.append(centerline)
        diagnostics.append(
            CenterlinePieceDiagnostic(
                reference_index=reference_index,
                reference_area_mm2=reference.area_mm2,
                reference_perimeter_mm=reference.perimeter_mm,
                matched=True,
                source=source,
                score=score,
                candidate_area_mm2=centerline.area_mm2,
                candidate_perimeter_mm=centerline.perimeter_mm,
                candidate_bounds_mm=centerline.bounds,
                reference_bounds_mm=reference.bounds,
                candidate_geometry=centerline,
                reference_geometry=reference,
            )
        )
    return tuple(candidates), tuple(diagnostics)


def _best_piecewise_centerline_candidate(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[float, set[int], PathGeometry, str] | None:
    if not local_paths:
        return None
    best: tuple[float, set[int], PathGeometry, str] | None = None
    for source, indices, candidate in _piecewise_scored_centerline_candidates(
        reference,
        local_paths,
    ):
        for scored_source, scored_candidate, score in candidate:
            if score is None:
                continue
            branch_bonus = min(0.08, 0.01 * max(0, len(indices) - 1))
            total_score = score + branch_bonus
            if best is None or total_score > best[0]:
                best = (total_score, indices, scored_candidate, scored_source)
    return best


def _best_rejected_piecewise_centerline_candidate(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[str, PathGeometry, str, tuple[float, float, float] | None] | None:
    if not local_paths:
        return None
    best: tuple[float, str, PathGeometry, str, tuple[float, float, float] | None] | None = None
    for _, _, scored_candidates in _piecewise_scored_centerline_candidates(reference, local_paths):
        for source, candidate, score in scored_candidates:
            if score is not None:
                continue
            reason = _centerline_piece_rejection_reason(candidate, reference)
            distances = _path_distance_summary(candidate, reference) if candidate.closed else None
            priority = _rejected_centerline_priority(candidate, reference, distances)
            if best is None or priority > best[0]:
                best = (priority, source, candidate, reason, distances)
    if best is None:
        return None
    _, source, candidate, reason, distances = best
    return source, candidate, reason, distances


def _piecewise_scored_centerline_candidates(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> list[tuple[str, set[int], list[tuple[str, PathGeometry, float | None]]]]:
    branch_groups: list[tuple[str, set[int], PathGeometry]] = [
        ("stitched-branches", indices, candidate)
        for indices, candidate in _merge_open_centerline_branches(
            local_paths,
            max_gap_mm=_piece_stitch_gap_mm(reference),
        )
    ]
    slender_reference_near = _slender_reference_near_fill_candidate(reference, local_paths)
    if slender_reference_near is not None:
        indices, candidate = slender_reference_near
        branch_groups.append(("slender-reference-near-fill", indices, candidate))
    reference_near = _reference_near_open_branch_candidate(reference, local_paths)
    if reference_near is not None:
        indices, candidate = reference_near
        branch_groups.append(("reference-near-open", indices, candidate))
    large_piece_reference_near = _large_piece_reference_near_candidate(reference, local_paths)
    if large_piece_reference_near is not None:
        indices, candidate = large_piece_reference_near
        branch_groups.append(("large-piece-reference-near", indices, candidate))
    compact_reference_near = _compact_reference_near_fill_candidate(reference, local_paths)
    if compact_reference_near is not None:
        indices, candidate = compact_reference_near
        branch_groups.append(("compact-reference-near-fill", indices, candidate))
    aggregated = _aggregate_reference_ordered_branches(reference, local_paths)
    if aggregated is not None:
        indices, candidate = aggregated
        branch_groups.append(("reference-ordered-open", indices, candidate))
    component_candidate = _largest_local_component_candidate(reference, local_paths)
    if component_candidate is not None:
        indices, candidate = component_candidate
        branch_groups.append(("component-hull", indices, candidate))
    dominant_open_candidate = _dominant_open_component_candidate(reference, local_paths)
    if dominant_open_candidate is not None:
        indices, candidate = dominant_open_candidate
        branch_groups.append(("dominant-open-angle-sorted", indices, candidate))

    scored_groups: list[tuple[str, set[int], list[tuple[str, PathGeometry, float | None]]]] = []
    for source, indices, candidate in branch_groups:
        closed_candidate = _close_path_when_near_loop(
            candidate,
            max_gap_mm=_piece_close_gap_mm(reference),
        )
        scored_candidates: list[tuple[str, PathGeometry, float | None]] = [
            (source, closed_candidate, _centerline_piece_score(closed_candidate, reference))
        ]
        if not closed_candidate.closed:
            outline_guided = _outline_guided_closed_candidate(closed_candidate, reference)
            if outline_guided is not None:
                scored_candidates.append(
                    (
                        f"{source}+outline-guided-closure",
                        outline_guided,
                        _centerline_piece_score(outline_guided, reference),
                    )
                )
        scored_groups.append((source, indices, scored_candidates))
    return scored_groups


def _dominant_open_component_candidate(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[set[int], PathGeometry] | None:
    components = _endpoint_components(local_paths, max_gap_mm=4.0)
    if not components:
        return None
    ranked: list[tuple[float, set[int], PathGeometry]] = []
    for indices, paths in components:
        open_paths = [path for path in paths if not path.closed]
        if len(open_paths) < 2:
            continue
        open_paths.sort(key=lambda path: path.area_mm2, reverse=True)
        dominant = open_paths[:3]
        dominant_perimeter = sum(path.perimeter_mm for path in dominant)
        total_perimeter = sum(path.perimeter_mm for path in paths)
        if total_perimeter <= 0:
            continue
        slenderness = (
            reference.area_mm2 / (reference.perimeter_mm * reference.perimeter_mm)
            if reference.perimeter_mm > 0
            else 0.0
        )
        coverage_threshold = 0.7
        if slenderness < 0.001:
            coverage_threshold = 0.5
        elif slenderness < 0.002:
            coverage_threshold = 0.6
        # Large piece components often contain many small interior loops. Gate on
        # coverage against the reference perimeter first, then use component share
        # as a secondary signal for smaller pieces.
        if dominant_perimeter < reference.perimeter_mm * coverage_threshold:
            continue
        if (
            reference.perimeter_mm < 250.0
            and dominant_perimeter / total_perimeter < 0.45
        ):
            continue
        candidate = _angle_sorted_candidate_from_paths(dominant)
        overlap = _bbox_overlap_ratio(candidate.bounds, reference.bounds)
        if overlap < 0.85:
            continue
        ranked.append((overlap + dominant_perimeter / total_perimeter, indices, candidate))
    if not ranked:
        return None
    ranked.sort(reverse=True, key=lambda item: item[0])
    _, indices, candidate = ranked[0]
    return indices, candidate


def _largest_local_component_candidate(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[set[int], PathGeometry] | None:
    components = _endpoint_components(local_paths, max_gap_mm=4.0)
    if not components:
        return None
    ranked: list[tuple[float, set[int], PathGeometry]] = []
    for indices, paths in components:
        if len(paths) < 2:
            continue
        candidate = _component_hull_candidate(paths)
        overlap = _bbox_overlap_ratio(candidate.bounds, reference.bounds)
        if overlap < 0.85:
            continue
        ranked.append((overlap + len(paths) * 0.01, indices, candidate))
    if not ranked:
        return None
    ranked.sort(reverse=True, key=lambda item: item[0])
    _, indices, candidate = ranked[0]
    return indices, candidate


def _aggregate_reference_ordered_branches(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[set[int], PathGeometry] | None:
    usable: list[tuple[int, PathGeometry, int]] = []
    for index, path in local_paths:
        if path.closed:
            continue
        if path.perimeter_mm < _reference_ordered_min_branch_length(reference):
            continue
        anchor = _nearest_reference_index(reference.points, _path_centroid(path))
        if anchor is None:
            continue
        usable.append((index, path, anchor))
    if len(usable) < 2:
        return None
    usable.sort(key=lambda item: item[2])
    max_branches = min(_reference_ordered_branch_limit(reference), len(usable))
    ordered = usable[:max_branches]
    merged_indices: set[int] = {index for index, _, _ in ordered}
    merged_points: list[Point] = []
    for _, path, _ in ordered:
        points = path.points
        if not points:
            continue
        if not merged_points:
            merged_points.extend(points)
            continue
        forward_gap = _point_distance(merged_points[-1], points[0])
        reverse_gap = _point_distance(merged_points[-1], points[-1])
        oriented = points if forward_gap <= reverse_gap else tuple(reversed(points))
        if _point_distance(merged_points[-1], oriented[0]) <= 2.5:
            merged_points.extend(oriented[1:])
        else:
            merged_points.extend(oriented)
    if len(merged_points) < 3:
        return None
    candidate = PathGeometry(points=tuple(merged_points), closed=False)
    if candidate.perimeter_mm < reference.perimeter_mm * 0.45:
        return None
    return merged_indices, candidate


def _reference_ordered_branch_limit(reference: PathGeometry) -> int:
    if _is_large_piece_reference(reference):
        return 32
    return 8


def _reference_ordered_min_branch_length(reference: PathGeometry) -> float:
    if _is_large_piece_reference(reference):
        return max(8.0, reference.perimeter_mm * 0.05)
    return max(8.0, reference.perimeter_mm * 0.08)


def _is_large_piece_reference(reference: PathGeometry) -> bool:
    return reference.area_mm2 >= 5000.0 or reference.perimeter_mm >= 650.0


def _reference_near_open_branch_candidate(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[set[int], PathGeometry] | None:
    if _path_slenderness(reference) >= 0.001 or len(reference.points) < 4:
        return None
    nearest_by_anchor: dict[int, tuple[float, Point, int]] = {}
    used_indices: set[int] = set()
    max_distance_mm = 3.5
    for index, path in local_paths:
        if path.perimeter_mm < max(8.0, reference.perimeter_mm * 0.02):
            continue
        if path.closed and path.area_mm2 > max(200.0, reference.area_mm2 * 4.0):
            continue
        samples = path.points[:: max(1, len(path.points) // 80)]
        near_sample_count = 0
        for point in samples:
            distance = _point_to_path_distance(point, reference)
            if distance > max_distance_mm:
                continue
            anchor = _nearest_reference_index(reference.points, point)
            if anchor is None:
                continue
            near_sample_count += 1
            current = nearest_by_anchor.get(anchor)
            if current is None or distance < current[0]:
                nearest_by_anchor[anchor] = (distance, point, index)
        if near_sample_count < 2:
            continue
        near_ratio = near_sample_count / max(1, len(samples))
        if near_ratio >= 0.25 or path.perimeter_mm <= reference.perimeter_mm * 0.25:
            used_indices.add(index)
    if len(nearest_by_anchor) < 3:
        return None
    anchor_coverage = len(nearest_by_anchor) / len(reference.points)
    if anchor_coverage < 0.45:
        return None
    ordered_anchor_points = sorted(nearest_by_anchor.items(), key=lambda item: item[0])
    cut_index = _largest_cyclic_anchor_gap_cut(
        [anchor for anchor, _ in ordered_anchor_points],
        reference_point_count=len(reference.points),
    )
    ordered = ordered_anchor_points[cut_index:] + ordered_anchor_points[:cut_index]
    points = _fill_reference_near_anchor_gaps(reference, ordered)
    indices = {index for _, (_, _, index) in ordered}
    if not indices.issubset(used_indices):
        return None
    candidate = PathGeometry(points=points, closed=True)
    if candidate.perimeter_mm < reference.perimeter_mm * 0.35:
        return None
    return indices, candidate


def _slender_reference_near_fill_candidate(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[set[int], PathGeometry] | None:
    if _path_slenderness(reference) >= 0.001 or len(reference.points) < 4:
        return None
    nearest_by_anchor: dict[int, tuple[float, Point, int]] = {}
    used_indices: set[int] = set()
    max_distance_mm = 3.5
    for index, path in local_paths:
        if path.perimeter_mm < max(8.0, reference.perimeter_mm * 0.015):
            continue
        if path.closed and path.area_mm2 > max(200.0, reference.area_mm2 * 4.0):
            continue
        samples = path.points[:: max(1, len(path.points) // 120)]
        near_sample_count = 0
        for point in samples:
            distance = _point_to_path_distance(point, reference)
            if distance > max_distance_mm:
                continue
            anchor = _nearest_reference_index(reference.points, point)
            if anchor is None:
                continue
            near_sample_count += 1
            current = nearest_by_anchor.get(anchor)
            if current is None or distance < current[0]:
                nearest_by_anchor[anchor] = (distance, point, index)
        if near_sample_count >= 1:
            used_indices.add(index)
    if len(nearest_by_anchor) < 3:
        return None
    anchor_coverage = len(nearest_by_anchor) / len(reference.points)
    if anchor_coverage < 0.55:
        return None
    ordered_anchor_points = sorted(nearest_by_anchor.items(), key=lambda item: item[0])
    cut_index = _largest_cyclic_anchor_gap_cut(
        [anchor for anchor, _ in ordered_anchor_points],
        reference_point_count=len(reference.points),
    )
    ordered = ordered_anchor_points[cut_index:] + ordered_anchor_points[:cut_index]
    indices = {index for _, (_, _, index) in ordered}
    if not indices.issubset(used_indices):
        return None
    candidate = PathGeometry(
        points=_fill_reference_near_anchor_gaps(reference, ordered),
        closed=True,
    )
    if candidate.perimeter_mm < reference.perimeter_mm * 0.6:
        return None
    _, p95_distance, max_distance = _path_distance_summary(candidate, reference)
    if p95_distance > 1.0 or max_distance > 2.0:
        return None
    return indices, candidate


def _large_piece_reference_near_candidate(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[set[int], PathGeometry] | None:
    if not _is_large_piece_reference(reference) or len(reference.points) < 4:
        return None
    nearest_by_anchor: dict[int, tuple[float, Point, int]] = {}
    used_indices: set[int] = set()
    max_distance_mm = 3.5
    for index, path in local_paths:
        if path.perimeter_mm < max(8.0, reference.perimeter_mm * 0.015):
            continue
        samples = path.points[:: max(1, len(path.points) // 120)]
        near_sample_count = 0
        for point in samples:
            distance = _point_to_path_distance(point, reference)
            if distance > max_distance_mm:
                continue
            anchor = _nearest_reference_index(reference.points, point)
            if anchor is None:
                continue
            near_sample_count += 1
            current = nearest_by_anchor.get(anchor)
            if current is None or distance < current[0]:
                nearest_by_anchor[anchor] = (distance, point, index)
        if near_sample_count < 2:
            continue
        near_ratio = near_sample_count / max(1, len(samples))
        if near_ratio >= 0.2:
            used_indices.add(index)
    if len(nearest_by_anchor) < 3:
        return None
    anchor_coverage = len(nearest_by_anchor) / len(reference.points)
    if anchor_coverage < 0.55:
        return None
    ordered_anchor_points = sorted(nearest_by_anchor.items(), key=lambda item: item[0])
    cut_index = _largest_cyclic_anchor_gap_cut(
        [anchor for anchor, _ in ordered_anchor_points],
        reference_point_count=len(reference.points),
    )
    ordered = ordered_anchor_points[cut_index:] + ordered_anchor_points[:cut_index]
    points = _fill_reference_near_anchor_gaps(reference, ordered)
    indices = {index for _, (_, _, index) in ordered}
    if not indices.issubset(used_indices):
        return None
    candidate = _snap_large_piece_extreme_anchors(
        PathGeometry(points=points, closed=True),
        reference,
    )
    if candidate.perimeter_mm < reference.perimeter_mm * 0.6:
        return None
    mean_distance, p95_distance, max_distance = _path_distance_summary(candidate, reference)
    if p95_distance > 1.25 or max_distance > 8.0:
        return None
    return indices, candidate


def _snap_large_piece_extreme_anchors(
    candidate: PathGeometry,
    reference: PathGeometry,
) -> PathGeometry:
    xmin, ymin, xmax, ymax = reference.bounds
    snapped_points: list[Point] = []
    for point in candidate.points:
        anchor = _nearest_reference_index(reference.points, point)
        if anchor is None:
            snapped_points.append(point)
            continue
        reference_point = reference.points[anchor]
        near_extreme = (
            reference_point.y_mm <= ymin + 14.0
            or reference_point.y_mm >= ymax - 14.0
            or reference_point.x_mm <= xmin + 8.0
            or reference_point.x_mm >= xmax - 8.0
        )
        if near_extreme and _point_distance(point, reference_point) > 3.0:
            snapped_points.append(reference_point)
        else:
            snapped_points.append(point)
    return PathGeometry(points=tuple(snapped_points), closed=candidate.closed)


def _compact_reference_near_fill_candidate(
    reference: PathGeometry,
    local_paths: list[tuple[int, PathGeometry]],
) -> tuple[set[int], PathGeometry] | None:
    if _is_large_piece_reference(reference) or _path_slenderness(reference) < 0.01:
        return None
    if len(reference.points) < 8 or reference.area_mm2 < 350.0:
        return None
    nearest_by_anchor: dict[int, tuple[float, Point, int]] = {}
    used_indices: set[int] = set()
    max_distance_mm = 2.5
    for index, path in local_paths:
        if path.perimeter_mm < max(6.0, reference.perimeter_mm * 0.015):
            continue
        if path.closed and path.area_mm2 > max(200.0, reference.area_mm2 * 1.5):
            continue
        samples = path.points[:: max(1, len(path.points) // 120)]
        near_sample_count = 0
        for point in samples:
            distance = _point_to_path_distance(point, reference)
            if distance > max_distance_mm:
                continue
            anchor = _nearest_reference_index(reference.points, point)
            if anchor is None:
                continue
            near_sample_count += 1
            current = nearest_by_anchor.get(anchor)
            if current is None or distance < current[0]:
                nearest_by_anchor[anchor] = (distance, point, index)
        if near_sample_count >= 1:
            used_indices.add(index)
    if len(nearest_by_anchor) < 6:
        return None
    anchor_coverage = len(nearest_by_anchor) / len(reference.points)
    if anchor_coverage < 0.7:
        return None
    ordered_anchor_points = sorted(nearest_by_anchor.items(), key=lambda item: item[0])
    cut_index = _largest_cyclic_anchor_gap_cut(
        [anchor for anchor, _ in ordered_anchor_points],
        reference_point_count=len(reference.points),
    )
    ordered = ordered_anchor_points[cut_index:] + ordered_anchor_points[:cut_index]
    indices = {index for _, (_, _, index) in ordered}
    if not indices.issubset(used_indices):
        return None
    candidate = PathGeometry(
        points=_fill_reference_near_anchor_gaps(reference, ordered),
        closed=True,
    )
    candidate = _snap_compact_piece_edge_anchors(candidate, reference)
    if candidate.perimeter_mm < reference.perimeter_mm * 0.75:
        return None
    _, p95_distance, max_distance = _path_distance_summary(candidate, reference)
    if p95_distance > 2.25 or max_distance > 4.0:
        return None
    return indices, candidate


def _snap_compact_piece_edge_anchors(
    candidate: PathGeometry,
    reference: PathGeometry,
) -> PathGeometry:
    xmin, ymin, xmax, ymax = reference.bounds
    snapped_points: list[Point] = []
    for point in candidate.points:
        anchor = _nearest_reference_index(reference.points, point)
        if anchor is None:
            snapped_points.append(point)
            continue
        reference_point = reference.points[anchor]
        near_edge = (
            reference_point.y_mm <= ymin + 8.0
            or reference_point.y_mm >= ymax - 8.0
            or reference_point.x_mm <= xmin + 8.0
            or reference_point.x_mm >= xmax - 8.0
        )
        if near_edge and _point_distance(point, reference_point) > 0.8:
            snapped_points.append(reference_point)
        else:
            snapped_points.append(point)
    snapped = PathGeometry(points=tuple(snapped_points), closed=candidate.closed)
    _, p95_distance, max_distance = _path_distance_summary(snapped, reference)
    if p95_distance > 0.6 or max_distance > 1.25:
        return candidate
    return snapped


def _fill_reference_near_anchor_gaps(
    reference: PathGeometry,
    ordered_anchor_points: list[tuple[int, tuple[float, Point, int]]],
) -> tuple[Point, ...]:
    if not ordered_anchor_points:
        return ()
    points: list[Point] = []
    reference_point_count = len(reference.points)
    max_fill_gap = max(3, round(reference_point_count * 0.25))
    for index, (anchor, (_, point, _)) in enumerate(ordered_anchor_points):
        points.append(point)
        next_anchor = ordered_anchor_points[(index + 1) % len(ordered_anchor_points)][0]
        gap = (next_anchor - anchor) % reference_point_count
        if gap <= 1 or gap > max_fill_gap:
            continue
        arc = _reference_arc(reference.points, anchor, next_anchor)
        points.extend(arc[1:-1])
    return tuple(points)


def _largest_cyclic_anchor_gap_cut(
    anchors: list[int],
    *,
    reference_point_count: int,
) -> int:
    if len(anchors) < 2:
        return 0
    gaps: list[int] = []
    for index, anchor in enumerate(anchors):
        next_anchor = anchors[(index + 1) % len(anchors)]
        gap = (
            reference_point_count + next_anchor - anchor
            if index == len(anchors) - 1
            else next_anchor - anchor
        )
        gaps.append(gap)
    return (max(range(len(gaps)), key=lambda index: gaps[index]) + 1) % len(anchors)


def _endpoint_components(
    local_paths: list[tuple[int, PathGeometry]],
    *,
    max_gap_mm: float,
) -> list[tuple[set[int], list[PathGeometry]]]:
    adjacency: dict[int, set[int]] = defaultdict(set)
    path_by_index = {index: path for index, path in local_paths}
    for first_pos, (first_index, first_path) in enumerate(local_paths):
        for second_index, second_path in local_paths[first_pos + 1 :]:
            if _paths_have_close_endpoints(first_path, second_path, max_gap_mm=max_gap_mm):
                adjacency[first_index].add(second_index)
                adjacency[second_index].add(first_index)
    visited: set[int] = set()
    components: list[tuple[set[int], list[PathGeometry]]] = []
    for index, path in local_paths:
        if index in visited:
            continue
        queue = deque([index])
        visited.add(index)
        component_indices: set[int] = set()
        component_paths: list[PathGeometry] = []
        while queue:
            current = queue.popleft()
            component_indices.add(current)
            component_paths.append(path_by_index[current])
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append((component_indices, component_paths))
    return components


def _paths_have_close_endpoints(
    first: PathGeometry,
    second: PathGeometry,
    *,
    max_gap_mm: float,
) -> bool:
    if not first.points or not second.points:
        return False
    first_points = (first.points[0], first.points[-1])
    second_points = (second.points[0], second.points[-1])
    return any(
        _point_distance(a, b) <= max_gap_mm
        for a in first_points
        for b in second_points
    )


def _component_union_bbox_path(paths: list[PathGeometry]) -> PathGeometry:
    xmin = min(path.bounds[0] for path in paths)
    ymin = min(path.bounds[1] for path in paths)
    xmax = max(path.bounds[2] for path in paths)
    ymax = max(path.bounds[3] for path in paths)
    return PathGeometry(
        points=(
            Point(xmin, ymin),
            Point(xmax, ymin),
            Point(xmax, ymax),
            Point(xmin, ymax),
        ),
        closed=True,
    )


def _component_hull_candidate(paths: list[PathGeometry]) -> PathGeometry:
    sampled_points: list[tuple[float, float]] = []
    for path in paths:
        if not path.points:
            continue
        step = max(1, len(path.points) // 50)
        sampled_points.extend((point.x_mm, point.y_mm) for point in path.points[::step])
    hull = _convex_hull(sampled_points)
    if len(hull) < 3:
        return _component_union_bbox_path(paths)
    return PathGeometry(points=tuple(Point(x, y) for x, y in hull), closed=True)


def _angle_sorted_candidate_from_paths(paths: list[PathGeometry]) -> PathGeometry:
    sampled: list[Point] = []
    for path in paths:
        if not path.points:
            continue
        step = max(1, len(path.points) // 120)
        sampled.extend(path.points[::step])
    if len(sampled) < 3:
        return _component_hull_candidate(paths)
    center = Point(
        x_mm=sum(point.x_mm for point in sampled) / len(sampled),
        y_mm=sum(point.y_mm for point in sampled) / len(sampled),
    )
    ordered = sorted(
        sampled,
        key=lambda point: math.atan2(point.y_mm - center.y_mm, point.x_mm - center.x_mm),
    )
    return PathGeometry(points=tuple(ordered), closed=True)


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(
        origin: tuple[float, float],
        first: tuple[float, float],
        second: tuple[float, float],
    ) -> float:
        return (
            (first[0] - origin[0]) * (second[1] - origin[1])
            - (first[1] - origin[1]) * (second[0] - origin[0])
        )

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def _merge_open_centerline_branches(
    local_paths: list[tuple[int, PathGeometry]],
    *,
    max_gap_mm: float,
) -> list[tuple[set[int], PathGeometry]]:
    groups = [(set((index,)), path) for index, path in local_paths]
    changed = True
    while changed:
        changed = False
        best: tuple[float, int, int, PathGeometry] | None = None
        for first_index, (_, first) in enumerate(groups):
            if first.closed:
                continue
            for second_index in range(first_index + 1, len(groups)):
                _, second = groups[second_index]
                if second.closed:
                    continue
                stitched = _best_stitched_path(first, second, max_gap_mm=max_gap_mm)
                if stitched is None:
                    continue
                gap, candidate = stitched
                if best is None or gap < best[0]:
                    best = (gap, first_index, second_index, candidate)
        if best is None:
            continue
        _, first_index, second_index, candidate = best
        merged_indices = groups[first_index][0] | groups[second_index][0]
        groups[first_index] = (merged_indices, candidate)
        groups.pop(second_index)
        changed = True
    return groups


def _centerline_path_is_local_to_reference(
    centerline: PathGeometry,
    reference: PathGeometry,
) -> bool:
    bbox_overlap = _bbox_overlap_ratio(centerline.bounds, reference.bounds)
    if bbox_overlap >= 0.35:
        return True
    expanded = _expand_bounds(reference.bounds, margin_mm=6.0)
    if _bounds_overlap(centerline.bounds, expanded):
        return True
    return any(_point_in_bounds(point, expanded) for point in centerline.points)


def _piece_stitch_gap_mm(reference: PathGeometry) -> float:
    xmin, ymin, xmax, ymax = reference.bounds
    diagonal = math.hypot(xmax - xmin, ymax - ymin)
    return max(1.5, min(10.0, diagonal * 0.05))


def _piece_close_gap_mm(reference: PathGeometry) -> float:
    xmin, ymin, xmax, ymax = reference.bounds
    diagonal = math.hypot(xmax - xmin, ymax - ymin)
    return max(2.0, min(12.0, diagonal * 0.06))


def _close_path_when_near_loop(path: PathGeometry, *, max_gap_mm: float) -> PathGeometry:
    if path.closed or len(path.points) < 3:
        return path
    if _point_distance(path.points[0], path.points[-1]) > max_gap_mm:
        return path
    return PathGeometry(points=path.points, closed=True)


def _outline_guided_closed_candidate(
    centerline: PathGeometry,
    reference: PathGeometry,
) -> PathGeometry | None:
    if centerline.closed or len(centerline.points) < 3 or len(reference.points) < 4:
        return None
    start_index = _nearest_reference_index(reference.points, centerline.points[0])
    end_index = _nearest_reference_index(reference.points, centerline.points[-1])
    if start_index is None or end_index is None or start_index == end_index:
        return None
    if (
        _point_distance(reference.points[start_index], centerline.points[0]) > 12.0
        or _point_distance(reference.points[end_index], centerline.points[-1]) > 12.0
    ):
        return None
    if centerline.perimeter_mm < reference.perimeter_mm * 0.45:
        return None
    best: tuple[float, PathGeometry] | None = None
    for arc in (
        _reference_arc(reference.points, end_index, start_index),
        tuple(reversed(_reference_arc(reference.points, start_index, end_index))),
    ):
        if len(arc) < 2:
            continue
        arc_length = _polyline_length(arc)
        if arc_length > reference.perimeter_mm * 0.35:
            continue
        candidate = PathGeometry(points=(*centerline.points, *arc), closed=True)
        closure_cost = (
            _point_distance(centerline.points[-1], arc[0])
            + _point_distance(arc[-1], centerline.points[0])
        )
        if best is None or closure_cost < best[0]:
            best = (closure_cost, candidate)
    return best[1] if best is not None else None


def _best_stitched_path(
    first: PathGeometry,
    second: PathGeometry,
    *,
    max_gap_mm: float,
) -> tuple[float, PathGeometry] | None:
    variants = (
        (first.points, second.points),
        (tuple(reversed(first.points)), second.points),
        (first.points, tuple(reversed(second.points))),
        (tuple(reversed(first.points)), tuple(reversed(second.points))),
    )
    best: tuple[float, PathGeometry] | None = None
    for left, right in variants:
        if not left or not right:
            continue
        gap = _point_distance(left[-1], right[0])
        if gap > max_gap_mm:
            continue
        if not _endpoint_directions_are_compatible(left, right):
            continue
        stitched_points = (*left, *right)
        closed = _point_distance(stitched_points[0], stitched_points[-1]) <= max_gap_mm
        if closed:
            stitched_points = stitched_points[:-1]
        candidate = PathGeometry(points=stitched_points, closed=closed)
        if best is None or gap < best[0]:
            best = (gap, candidate)
    return best


def _endpoint_directions_are_compatible(
    left: tuple[Point, ...],
    right: tuple[Point, ...],
    *,
    min_cosine: float = -0.2,
) -> bool:
    if len(left) < 2 or len(right) < 2:
        return True
    left_vector = (left[-1].x_mm - left[-2].x_mm, left[-1].y_mm - left[-2].y_mm)
    right_vector = (right[1].x_mm - right[0].x_mm, right[1].y_mm - right[0].y_mm)
    left_length = math.hypot(left_vector[0], left_vector[1])
    right_length = math.hypot(right_vector[0], right_vector[1])
    if left_length == 0 or right_length == 0:
        return True
    cosine = (
        left_vector[0] * right_vector[0] + left_vector[1] * right_vector[1]
    ) / (left_length * right_length)
    return cosine >= min_cosine


def _centerline_replacement_is_viable(
    centerline_paths: tuple[PathGeometry, ...],
    reference_paths: list[PathGeometry],
) -> bool:
    if not centerline_paths:
        return False
    if not reference_paths:
        return True
    closed_centerlines = sum(path.closed for path in centerline_paths)
    minimum_closed_paths = max(1, round(len(reference_paths) * 0.6))
    maximum_closed_paths = max(2, round(len(reference_paths) * 1.5))
    return minimum_closed_paths <= closed_centerlines <= maximum_closed_paths


def _centerline_piece_score(centerline: PathGeometry, reference: PathGeometry) -> float | None:
    if not centerline.closed:
        return None
    if centerline.perimeter_mm <= 0 or reference.perimeter_mm <= 0:
        return None
    bbox_overlap = _bbox_overlap_ratio(centerline.bounds, reference.bounds)
    if bbox_overlap < 0.65:
        return None
    if _path_slenderness(reference) < 0.001:
        mean_distance, p95_distance, max_distance = _path_distance_summary(centerline, reference)
        if p95_distance > 2.5 or max_distance > 12.0:
            return None
        perimeter_ratio = centerline.perimeter_mm / reference.perimeter_mm
        if not 0.25 <= perimeter_ratio <= 2.5:
            return None
        return (
            bbox_overlap
            - abs(1.0 - perimeter_ratio) * 0.12
            - min(0.2, mean_distance * 0.03)
        )
    centerline_area = centerline.area_mm2
    if centerline_area <= 0 or reference.area_mm2 <= 0:
        return None
    area_ratio = centerline_area / reference.area_mm2
    perimeter_ratio = centerline.perimeter_mm / reference.perimeter_mm
    if not 0.45 <= perimeter_ratio <= 1.8:
        return None
    if not _bbox_dimension_coverage_is_plausible(centerline, reference):
        return None
    if not 0.35 <= area_ratio <= 1.35:
        return None
    return bbox_overlap - abs(1.0 - area_ratio) * 0.25 - abs(1.0 - perimeter_ratio) * 0.15


def _centerline_piece_rejection_reason(centerline: PathGeometry, reference: PathGeometry) -> str:
    if not centerline.closed:
        return "candidate is not closed"
    if centerline.perimeter_mm <= 0 or reference.perimeter_mm <= 0:
        return "candidate or reference perimeter is zero"
    bbox_overlap = _bbox_overlap_ratio(centerline.bounds, reference.bounds)
    if bbox_overlap < 0.65:
        return "bbox overlap is below 0.65"
    if _path_slenderness(reference) < 0.001:
        mean_distance, p95_distance, max_distance = _path_distance_summary(centerline, reference)
        if p95_distance > 2.5 or max_distance > 12.0:
            return "slender piece distance exceeds limits"
        perimeter_ratio = centerline.perimeter_mm / reference.perimeter_mm
        if not 0.25 <= perimeter_ratio <= 2.5:
            return "slender piece perimeter ratio is outside limits"
        return "candidate was rejected by unknown slender-piece scoring rule"
    if centerline.area_mm2 <= 0 or reference.area_mm2 <= 0:
        return "candidate or reference area is zero"
    area_ratio = centerline.area_mm2 / reference.area_mm2
    if not 0.35 <= area_ratio <= 1.35:
        return "area ratio is outside limits"
    perimeter_ratio = centerline.perimeter_mm / reference.perimeter_mm
    if not 0.45 <= perimeter_ratio <= 1.8:
        return "perimeter ratio is outside limits"
    if not _bbox_dimension_coverage_is_plausible(centerline, reference):
        return "bbox dimension coverage is below limits"
    return "candidate was rejected by unknown scoring rule"


def _rejected_centerline_priority(
    centerline: PathGeometry,
    reference: PathGeometry,
    distances: tuple[float, float, float] | None,
) -> float:
    bbox_overlap = _bbox_overlap_ratio(centerline.bounds, reference.bounds)
    perimeter_ratio = (
        min(centerline.perimeter_mm, reference.perimeter_mm)
        / max(centerline.perimeter_mm, reference.perimeter_mm)
        if centerline.perimeter_mm > 0 and reference.perimeter_mm > 0
        else 0.0
    )
    area_ratio = (
        min(centerline.area_mm2, reference.area_mm2)
        / max(centerline.area_mm2, reference.area_mm2)
        if centerline.area_mm2 > 0 and reference.area_mm2 > 0
        else 0.0
    )
    distance_penalty = 0.0 if distances is None else min(1.0, distances[1] / 25.0)
    return bbox_overlap + perimeter_ratio * 0.4 + area_ratio * 0.2 - distance_penalty * 0.5


def _bbox_dimension_coverage_is_plausible(
    centerline: PathGeometry,
    reference: PathGeometry,
) -> bool:
    centerline_width, centerline_height = _bbox_dimensions(centerline.bounds)
    reference_width, reference_height = _bbox_dimensions(reference.bounds)
    if reference_width <= 0 or reference_height <= 0:
        return True
    width_ratio = centerline_width / reference_width
    height_ratio = centerline_height / reference_height
    return width_ratio >= 0.68 and height_ratio >= 0.68


def _bbox_dimensions(bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    return max(0.0, bounds[2] - bounds[0]), max(0.0, bounds[3] - bounds[1])


def _path_slenderness(path: PathGeometry) -> float:
    if path.perimeter_mm <= 0:
        return 0.0
    return path.area_mm2 / (path.perimeter_mm * path.perimeter_mm)


def _path_distance_summary(candidate: PathGeometry, reference: PathGeometry) -> tuple[float, float, float]:
    distances = [
        *_sampled_point_to_path_distances(candidate, reference),
        *_sampled_point_to_path_distances(reference, candidate),
    ]
    if not distances:
        return 0.0, 0.0, 0.0
    distances.sort()
    p95_index = min(len(distances) - 1, round((len(distances) - 1) * 0.95))
    return sum(distances) / len(distances), distances[p95_index], distances[-1]


def _point_to_path_distance(point: Point, path: PathGeometry) -> float:
    if len(path.points) < 2:
        return float("inf")
    segment_count = len(path.points) if path.closed else len(path.points) - 1
    return min(
        _point_to_segment_distance(
            point,
            path.points[index],
            path.points[(index + 1) % len(path.points)],
        )
        for index in range(segment_count)
    )


def _sampled_point_to_path_distances(source: PathGeometry, target: PathGeometry) -> list[float]:
    if not source.points or len(target.points) < 2:
        return []
    target_segments = [
        (target.points[index], target.points[(index + 1) % len(target.points)])
        for index in range(len(target.points) if target.closed else len(target.points) - 1)
    ]
    if not target_segments:
        return []
    step = max(1, len(source.points) // 200)
    return [
        min(_point_to_segment_distance(point, start, end) for start, end in target_segments)
        for point in source.points[::step]
    ]


def _point_to_segment_distance(point: Point, start: Point, end: Point) -> float:
    dx = end.x_mm - start.x_mm
    dy = end.y_mm - start.y_mm
    if dx == 0 and dy == 0:
        return _point_distance(point, start)
    t = ((point.x_mm - start.x_mm) * dx + (point.y_mm - start.y_mm) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    projection = Point(start.x_mm + t * dx, start.y_mm + t * dy)
    return _point_distance(point, projection)


def _is_compact_nonproduction_path(geometry: PathGeometry) -> bool:
    if not geometry.closed:
        return False
    xmin, ymin, xmax, ymax = geometry.bounds
    width = xmax - xmin
    height = ymax - ymin
    long_side = max(width, height)
    if long_side > 15.0:
        return False
    if geometry.area_mm2 > 100.0:
        return False
    return True


def _edge_aligned_ratio(geometry: PathGeometry, *, tolerance_mm: float = 1.2) -> float:
    xmin, ymin, xmax, ymax = geometry.bounds
    edge_point_count = sum(
        min(
            abs(point.x_mm - xmin),
            abs(point.x_mm - xmax),
            abs(point.y_mm - ymin),
            abs(point.y_mm - ymax),
        )
        <= tolerance_mm
        for point in geometry.points
    )
    return edge_point_count / len(geometry.points) if geometry.points else 0.0


def _covered_bbox_corner_count(geometry: PathGeometry, *, tolerance_mm: float = 3.0) -> int:
    xmin, ymin, xmax, ymax = geometry.bounds
    corners = ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax))
    covered = 0
    for corner_x, corner_y in corners:
        if any(
            ((point.x_mm - corner_x) ** 2 + (point.y_mm - corner_y) ** 2) ** 0.5
            <= tolerance_mm
            for point in geometry.points
        ):
            covered += 1
    return covered


def _merged_bounds(paths: list[PathGeometry]) -> tuple[float, float, float, float]:
    return (
        min(path.bounds[0] for path in paths),
        min(path.bounds[1] for path in paths),
        max(path.bounds[2] for path in paths),
        max(path.bounds[3] for path in paths),
    )


def _bounds_overlap(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    return max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3])


def _bbox_overlap_ratio(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    x_overlap = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    y_overlap = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    intersection = x_overlap * y_overlap
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    smaller = min(first_area, second_area)
    return intersection / smaller if smaller > 0 else 0.0


def _expand_bounds(
    bounds: tuple[float, float, float, float],
    *,
    margin_mm: float,
) -> tuple[float, float, float, float]:
    return (
        bounds[0] - margin_mm,
        bounds[1] - margin_mm,
        bounds[2] + margin_mm,
        bounds[3] + margin_mm,
    )


def _point_in_bounds(point: Point, bounds: tuple[float, float, float, float]) -> bool:
    return bounds[0] <= point.x_mm <= bounds[2] and bounds[1] <= point.y_mm <= bounds[3]


def _point_distance(a: Point, b: Point) -> float:
    return math.hypot(a.x_mm - b.x_mm, a.y_mm - b.y_mm)


def _nearest_reference_index(points: tuple[Point, ...], target: Point) -> int | None:
    if not points:
        return None
    best: tuple[float, int] | None = None
    for index, point in enumerate(points):
        distance = _point_distance(point, target)
        if best is None or distance < best[0]:
            best = (distance, index)
    return best[1] if best is not None else None


def _reference_arc(points: tuple[Point, ...], start_index: int, end_index: int) -> tuple[Point, ...]:
    if not points:
        return ()
    arc: list[Point] = []
    index = start_index
    while True:
        arc.append(points[index])
        if index == end_index:
            break
        index = (index + 1) % len(points)
        if len(arc) > len(points) + 1:
            return ()
    return tuple(arc)


def _polyline_length(points: tuple[Point, ...]) -> float:
    if len(points) < 2:
        return 0.0
    return sum(_point_distance(first, second) for first, second in zip(points, points[1:], strict=False))


def _path_centroid(path: PathGeometry) -> Point:
    if not path.points:
        return Point(0.0, 0.0)
    x = sum(point.x_mm for point in path.points) / len(path.points)
    y = sum(point.y_mm for point in path.points) / len(path.points)
    return Point(x, y)


def _scale_marker_lines(
    scale_report: ScaleDetectionReport | None,
    *,
    page_transform: PageCoordinateTransform | None = None,
) -> tuple[LineGeometry, ...]:
    if scale_report is None or scale_report.selected_candidate is None:
        return ()
    candidate = scale_report.selected_candidate
    pixel_to_mm = scale_report.applied_pixel_to_mm
    start = Point(candidate.start_px[0] * pixel_to_mm, candidate.start_px[1] * pixel_to_mm)
    end = Point(candidate.end_px[0] * pixel_to_mm, candidate.end_px[1] * pixel_to_mm)
    tick_length_mm = 4.0
    if candidate.orientation == "horizontal":
        y_tick_end = -tick_length_mm if start.y_mm > 0 else tick_length_mm
        main = _normalized_line(LineGeometry(start=start, end=end))
        ticks = tuple(
            LineGeometry(
                start=Point(_interpolate(start.x_mm, end.x_mm, fraction), start.y_mm),
                end=Point(_interpolate(start.x_mm, end.x_mm, fraction), start.y_mm + y_tick_end),
            )
            for fraction in (0.0, 1 / 3, 2 / 3, 1.0)
        )
        lines = (main, *ticks)
        return _transform_lines(lines, page_transform)
    if candidate.orientation == "vertical":
        x_tick_end = 4.0
        main = _normalized_line(LineGeometry(start=start, end=end))
        ticks = tuple(
            LineGeometry(
                start=Point(start.x_mm, _interpolate(start.y_mm, end.y_mm, fraction)),
                end=Point(start.x_mm + x_tick_end, _interpolate(start.y_mm, end.y_mm, fraction)),
            )
            for fraction in (0.0, 1 / 3, 2 / 3, 1.0)
        )
        lines = (main, *ticks)
        return _transform_lines(lines, page_transform)
    return ()


def _transform_lines(
    lines: tuple[LineGeometry, ...],
    page_transform: PageCoordinateTransform | None,
) -> tuple[LineGeometry, ...]:
    if page_transform is None:
        return lines
    transformed: list[LineGeometry] = []
    for line in lines:
        geometry = transform_geometry(line, page_transform)
        if isinstance(geometry, LineGeometry):
            transformed.append(geometry)
    return tuple(transformed)


def _promoted_scale_marker_ticks(
    promoted_lines: list[LineGeometry],
    semantic: list[GeometryObject],
) -> tuple[LineGeometry, ...]:
    if not any(not isinstance(geometry, LineGeometry) for geometry in semantic):
        return ()
    ticks: list[LineGeometry] = []
    for line in _longest_scale_like_lines_by_orientation(promoted_lines):
        if _has_overlapping_line(semantic, line, ignore_self=True):
            continue
        if not _is_axis_aligned_scale_line(line):
            continue
        ticks.extend(_tick_lines_for_axis_aligned_line(line))
    return tuple(ticks)


def _tick_lines_for_axis_aligned_line(line: LineGeometry) -> tuple[LineGeometry, ...]:
    tick_length_mm = 4.0
    if _line_orientation(line) == "horizontal":
        y_tick_end = -tick_length_mm if line.start.y_mm > tick_length_mm else tick_length_mm
        return tuple(
            LineGeometry(
                start=Point(_interpolate(line.start.x_mm, line.end.x_mm, fraction), line.start.y_mm),
                end=Point(
                    _interpolate(line.start.x_mm, line.end.x_mm, fraction),
                    line.start.y_mm + y_tick_end,
                ),
            )
            for fraction in (0.0, 1 / 3, 2 / 3, 1.0)
        )
    x_tick_end = tick_length_mm
    return tuple(
        LineGeometry(
            start=Point(line.start.x_mm, _interpolate(line.start.y_mm, line.end.y_mm, fraction)),
            end=Point(
                line.start.x_mm + x_tick_end,
                _interpolate(line.start.y_mm, line.end.y_mm, fraction),
            ),
        )
        for fraction in (0.0, 1 / 3, 2 / 3, 1.0)
    )


def _without_overlapping_scale_lines(
    semantic: list[GeometryObject],
    reconstructed_scale_lines: tuple[LineGeometry, ...],
) -> tuple[list[GeometryObject], int]:
    if not reconstructed_scale_lines:
        return semantic, 0
    filtered: list[GeometryObject] = []
    removed_count = 0
    main_scale_line = reconstructed_scale_lines[0]
    for geometry in semantic:
        if isinstance(geometry, LineGeometry) and _lines_overlap(geometry, main_scale_line):
            removed_count += 1
            continue
        filtered.append(geometry)
    return filtered, removed_count


def _is_axis_aligned_scale_line(line: LineGeometry) -> bool:
    return 25.0 <= line.length_mm <= 45.0 and _line_orientation(line) in {
        "horizontal",
        "vertical",
    }


def _longest_scale_like_lines_by_orientation(
    lines: list[LineGeometry],
) -> tuple[LineGeometry, ...]:
    longest_by_orientation: dict[str, LineGeometry] = {}
    for line in lines:
        orientation = _line_orientation(line)
        if orientation not in {"horizontal", "vertical"}:
            continue
        if not 25.0 <= line.length_mm <= 45.0:
            continue
        current = longest_by_orientation.get(orientation)
        if current is None or line.length_mm > current.length_mm:
            longest_by_orientation[orientation] = line
    return tuple(longest_by_orientation.values())


def _has_overlapping_line(
    geometries: list[GeometryObject],
    line: LineGeometry,
    *,
    ignore_self: bool = False,
) -> bool:
    for geometry in geometries:
        if not isinstance(geometry, LineGeometry):
            continue
        if ignore_self and _same_line(geometry, line):
            continue
        if _lines_overlap(geometry, line):
            return True
    return False


def _same_line(a: LineGeometry, b: LineGeometry, *, tolerance_mm: float = 0.001) -> bool:
    return (
        _point_distance(a.start, b.start) <= tolerance_mm
        and _point_distance(a.end, b.end) <= tolerance_mm
    ) or (
        _point_distance(a.start, b.end) <= tolerance_mm
        and _point_distance(a.end, b.start) <= tolerance_mm
    )


def _lines_overlap(a: LineGeometry, b: LineGeometry) -> bool:
    orientation = _line_orientation(a)
    if orientation != _line_orientation(b):
        return False
    if orientation == "horizontal":
        if abs(a.start.y_mm - b.start.y_mm) > 2.0:
            return False
        return _range_overlap_ratio(
            (a.start.x_mm, a.end.x_mm),
            (b.start.x_mm, b.end.x_mm),
        ) >= 0.65
    if orientation == "vertical":
        if abs(a.start.x_mm - b.start.x_mm) > 2.0:
            return False
        return _range_overlap_ratio(
            (a.start.y_mm, a.end.y_mm),
            (b.start.y_mm, b.end.y_mm),
        ) >= 0.65
    return False


def _line_orientation(line: LineGeometry) -> str:
    dx = abs(line.end.x_mm - line.start.x_mm)
    dy = abs(line.end.y_mm - line.start.y_mm)
    if dx <= 1.0 and dy > dx:
        return "vertical"
    if dy <= 1.0 and dx > dy:
        return "horizontal"
    return "diagonal"


def _range_overlap_ratio(a: tuple[float, float], b: tuple[float, float]) -> float:
    a_min, a_max = sorted(a)
    b_min, b_max = sorted(b)
    overlap = max(0.0, min(a_max, b_max) - max(a_min, b_min))
    shorter = min(a_max - a_min, b_max - b_min)
    return overlap / shorter if shorter > 0 else 0.0


def _has_similar_line(geometries: list[GeometryObject], line: LineGeometry) -> bool:
    return any(
        isinstance(geometry, LineGeometry)
        and abs(geometry.length_mm - line.length_mm) <= 1.0
        and _point_distance(geometry.start, line.start) <= 1.5
        and _point_distance(geometry.end, line.end) <= 1.5
        for geometry in geometries
    )


def _normalized_line(line: LineGeometry) -> LineGeometry:
    if (line.end.x_mm, line.end.y_mm) < (line.start.x_mm, line.start.y_mm):
        return LineGeometry(start=line.end, end=line.start)
    return line


def _point_distance(a: Point, b: Point) -> float:
    return ((a.x_mm - b.x_mm) ** 2 + (a.y_mm - b.y_mm) ** 2) ** 0.5


def _interpolate(start: float, end: float, fraction: float) -> float:
    return start + (end - start) * fraction
