"""Geometry deviation checks between source candidates and simplified paths."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pattern_refine.geometry import PathGeometry, Point


@dataclass(frozen=True)
class PathDeviation:
    source_index: int
    simplified_index: int | None
    matched: bool
    accepted: bool
    mean_deviation_mm: float | None
    p95_deviation_mm: float | None
    max_deviation_mm: float | None
    sample_count: int
    source_bbox: tuple[float, float, float, float]
    simplified_bbox: tuple[float, float, float, float] | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "source_index": self.source_index,
            "simplified_index": self.simplified_index,
            "matched": self.matched,
            "accepted": self.accepted,
            "mean_deviation_mm": self.mean_deviation_mm,
            "p95_deviation_mm": self.p95_deviation_mm,
            "max_deviation_mm": self.max_deviation_mm,
            "sample_count": self.sample_count,
            "source_bbox": list(self.source_bbox),
            "simplified_bbox": list(self.simplified_bbox) if self.simplified_bbox is not None else None,
        }


@dataclass(frozen=True)
class SimplificationDeviationReport:
    tolerance_mm: float
    accepted: bool
    source_path_count: int
    simplified_path_count: int
    matched_path_count: int
    unmatched_source_count: int
    max_deviation_mm: float | None
    path_deviations: tuple[PathDeviation, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "tolerance_mm": self.tolerance_mm,
            "accepted": self.accepted,
            "source_path_count": self.source_path_count,
            "simplified_path_count": self.simplified_path_count,
            "matched_path_count": self.matched_path_count,
            "unmatched_source_count": self.unmatched_source_count,
            "max_deviation_mm": self.max_deviation_mm,
            "path_deviations": [path.to_json_dict() for path in self.path_deviations],
        }


def build_simplification_deviation_report(
    source_geometries: tuple[PathGeometry, ...],
    simplified_geometries: tuple[PathGeometry, ...],
    *,
    tolerance_mm: float = 0.2,
) -> SimplificationDeviationReport:
    """Measure source-to-simplified path distance for matched candidates."""

    used_simplified: set[int] = set()
    path_reports: list[PathDeviation] = []
    for source_index, source in enumerate(source_geometries, start=1):
        simplified_index = _find_best_bbox_match(source, simplified_geometries, used_simplified)
        if simplified_index is None:
            path_reports.append(
                PathDeviation(
                    source_index=source_index,
                    simplified_index=None,
                    matched=False,
                    accepted=False,
                    mean_deviation_mm=None,
                    p95_deviation_mm=None,
                    max_deviation_mm=None,
                    sample_count=0,
                    source_bbox=source.bounds,
                    simplified_bbox=None,
                )
            )
            continue
        used_simplified.add(simplified_index)
        simplified = simplified_geometries[simplified_index - 1]
        distances = _point_to_path_distances(source.points, simplified)
        max_distance = max(distances) if distances else 0.0
        path_reports.append(
            PathDeviation(
                source_index=source_index,
                simplified_index=simplified_index,
                matched=True,
                accepted=max_distance <= tolerance_mm,
                mean_deviation_mm=sum(distances) / len(distances) if distances else 0.0,
                p95_deviation_mm=_percentile(distances, 0.95) if distances else 0.0,
                max_deviation_mm=max_distance,
                sample_count=len(distances),
                source_bbox=source.bounds,
                simplified_bbox=simplified.bounds,
            )
        )

    matched_reports = [report for report in path_reports if report.matched]
    max_deviation = (
        max(report.max_deviation_mm for report in matched_reports if report.max_deviation_mm is not None)
        if matched_reports
        else None
    )
    accepted = (
        bool(matched_reports)
        and all(report.accepted for report in matched_reports)
        and len(matched_reports) == len(simplified_geometries)
    )
    return SimplificationDeviationReport(
        tolerance_mm=tolerance_mm,
        accepted=accepted,
        source_path_count=len(source_geometries),
        simplified_path_count=len(simplified_geometries),
        matched_path_count=len(matched_reports),
        unmatched_source_count=sum(1 for report in path_reports if not report.matched),
        max_deviation_mm=max_deviation,
        path_deviations=tuple(path_reports),
    )


def write_simplification_deviation_report(
    report: SimplificationDeviationReport,
    report_path: Path,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _find_best_bbox_match(
    source: PathGeometry,
    simplified_geometries: tuple[PathGeometry, ...],
    used_simplified: set[int],
) -> int | None:
    best_index: int | None = None
    best_score = 0.0
    for simplified_index, simplified in enumerate(simplified_geometries, start=1):
        if simplified_index in used_simplified:
            continue
        score = _bbox_iou(source.bounds, simplified.bounds)
        if score > best_score:
            best_score = score
            best_index = simplified_index
    return best_index if best_score >= 0.85 else None


def _point_to_path_distances(points: tuple[Point, ...], path: PathGeometry) -> list[float]:
    if len(path.points) < 2:
        return []
    segment_count = len(path.points) if path.closed else len(path.points) - 1
    segments = [
        (path.points[index], path.points[(index + 1) % len(path.points)])
        for index in range(segment_count)
    ]
    return [min(_point_to_segment_distance(point, start, end) for start, end in segments) for point in points]


def _point_to_segment_distance(point: Point, start: Point, end: Point) -> float:
    dx = end.x_mm - start.x_mm
    dy = end.y_mm - start.y_mm
    if dx == 0 and dy == 0:
        return math.hypot(point.x_mm - start.x_mm, point.y_mm - start.y_mm)
    t = ((point.x_mm - start.x_mm) * dx + (point.y_mm - start.y_mm) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    projection_x = start.x_mm + t * dx
    projection_y = start.y_mm + t * dy
    return math.hypot(point.x_mm - projection_x, point.y_mm - projection_y)


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
