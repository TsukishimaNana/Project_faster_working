"""Feature-aware smoothing with deviation backoff."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pattern_refine.deviation import build_simplification_deviation_report
from pattern_refine.features import FeatureReport
from pattern_refine.geometry import PathGeometry, Point


@dataclass(frozen=True)
class SmoothingPathResult:
    path_index: int
    accepted: bool
    moved_point_count: int
    protected_point_count: int
    protected_path: bool
    max_deviation_mm: float

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "path_index": self.path_index,
            "accepted": self.accepted,
            "moved_point_count": self.moved_point_count,
            "protected_point_count": self.protected_point_count,
            "protected_path": self.protected_path,
            "max_deviation_mm": self.max_deviation_mm,
        }


@dataclass(frozen=True)
class SmoothingReport:
    tolerance_mm: float
    accepted_path_count: int
    rejected_path_count: int
    moved_point_count: int
    protected_point_count: int
    max_deviation_mm: float
    path_results: tuple[SmoothingPathResult, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "tolerance_mm": self.tolerance_mm,
            "accepted_path_count": self.accepted_path_count,
            "rejected_path_count": self.rejected_path_count,
            "moved_point_count": self.moved_point_count,
            "protected_point_count": self.protected_point_count,
            "max_deviation_mm": self.max_deviation_mm,
            "path_results": [result.to_json_dict() for result in self.path_results],
        }


def smooth_geometries(
    geometries: tuple[PathGeometry, ...],
    feature_report: FeatureReport,
    *,
    tolerance_mm: float = 0.2,
    alpha: float = 0.35,
) -> tuple[tuple[PathGeometry, ...], SmoothingReport]:
    smoothed: list[PathGeometry] = []
    results: list[SmoothingPathResult] = []
    protected_points = _protected_points_by_path(feature_report)
    protected_paths = _protected_paths(feature_report)
    for path_index, geometry in enumerate(geometries, start=1):
        if path_index in protected_paths:
            smoothed.append(geometry)
            results.append(
                SmoothingPathResult(
                    path_index=path_index,
                    accepted=False,
                    moved_point_count=0,
                    protected_point_count=len(geometry.points),
                    protected_path=True,
                    max_deviation_mm=0.0,
                )
            )
            continue
        protected = protected_points.get(path_index, set())
        candidate, moved_count = _smooth_geometry(geometry, protected, alpha=alpha)
        deviation = build_simplification_deviation_report(
            (geometry,),
            (candidate,),
            tolerance_mm=tolerance_mm,
        )
        max_deviation = deviation.max_deviation_mm or 0.0
        accepted = deviation.accepted and moved_count > 0
        if accepted:
            smoothed.append(candidate)
        else:
            smoothed.append(geometry)
            max_deviation = 0.0
        results.append(
            SmoothingPathResult(
                path_index=path_index,
                accepted=accepted,
                moved_point_count=moved_count if accepted else 0,
                protected_point_count=len(protected),
                protected_path=False,
                max_deviation_mm=max_deviation,
            )
        )

    report = SmoothingReport(
        tolerance_mm=tolerance_mm,
        accepted_path_count=sum(1 for result in results if result.accepted),
        rejected_path_count=sum(1 for result in results if not result.accepted),
        moved_point_count=sum(result.moved_point_count for result in results),
        protected_point_count=sum(result.protected_point_count for result in results),
        max_deviation_mm=max((result.max_deviation_mm for result in results), default=0.0),
        path_results=tuple(results),
    )
    return tuple(smoothed), report


def write_smoothing_report(report: SmoothingReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _protected_points_by_path(feature_report: FeatureReport) -> dict[int, set[int]]:
    protected: dict[int, set[int]] = {}
    for feature in feature_report.features:
        if feature.point_index is None:
            continue
        if feature.kind not in {"corner_candidate", "right_angle_candidate", "notch_candidate"}:
            continue
        protected.setdefault(feature.path_index, set()).add(feature.point_index - 1)
    return protected


def _protected_paths(feature_report: FeatureReport) -> set[int]:
    protected_kinds = {"triangle_mark_candidate", "short_alignment_mark_candidate"}
    return {
        feature.path_index
        for feature in feature_report.features
        if feature.kind in protected_kinds
    }


def _smooth_geometry(
    geometry: PathGeometry,
    protected: set[int],
    *,
    alpha: float,
) -> tuple[PathGeometry, int]:
    if len(geometry.points) < 3:
        return geometry, 0
    points = list(geometry.points)
    smoothed: list[Point] = []
    moved_count = 0
    for index, point in enumerate(points):
        if index in protected or (not geometry.closed and index in {0, len(points) - 1}):
            smoothed.append(point)
            continue
        previous_point = points[(index - 1) % len(points)]
        next_point = points[(index + 1) % len(points)]
        target = Point(
            x_mm=(previous_point.x_mm + next_point.x_mm) / 2,
            y_mm=(previous_point.y_mm + next_point.y_mm) / 2,
        )
        new_point = Point(
            x_mm=point.x_mm * (1 - alpha) + target.x_mm * alpha,
            y_mm=point.y_mm * (1 - alpha) + target.y_mm * alpha,
        )
        if abs(new_point.x_mm - point.x_mm) > 1e-9 or abs(new_point.y_mm - point.y_mm) > 1e-9:
            moved_count += 1
        smoothed.append(new_point)
    return PathGeometry(points=tuple(smoothed), closed=geometry.closed), moved_count
