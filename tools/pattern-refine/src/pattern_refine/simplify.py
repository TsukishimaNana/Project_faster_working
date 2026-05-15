"""Tolerance-constrained path simplification."""

from __future__ import annotations

import cv2
import numpy as np

from pattern_refine.deviation import build_simplification_deviation_report
from pattern_refine.geometry import PathGeometry, Point


def simplify_geometries_with_tolerance(
    source_geometries: tuple[PathGeometry, ...],
    *,
    tolerance_mm: float = 0.2,
) -> tuple[PathGeometry, ...]:
    """Simplify each path while preserving max source-to-simplified deviation."""

    return tuple(
        simplify_geometry_with_tolerance(geometry, tolerance_mm=tolerance_mm)
        for geometry in source_geometries
    )


def simplify_geometry_with_tolerance(
    geometry: PathGeometry,
    *,
    tolerance_mm: float = 0.2,
) -> PathGeometry:
    if len(geometry.points) <= 3:
        return geometry
    for epsilon in _epsilon_candidates(geometry.perimeter_mm):
        simplified = _approximate_geometry(geometry, epsilon)
        if len(simplified.points) < 3:
            continue
        report = build_simplification_deviation_report((geometry,), (simplified,), tolerance_mm=tolerance_mm)
        if report.accepted:
            return simplified
    return geometry


def _epsilon_candidates(perimeter_mm: float) -> tuple[float, ...]:
    upper = max(0.02, perimeter_mm * 0.002)
    return tuple(max(0.001, upper * factor) for factor in (1.0, 0.75, 0.5, 0.25, 0.125, 0.0625))


def _approximate_geometry(geometry: PathGeometry, epsilon: float) -> PathGeometry:
    contour = np.array(
        [[[point.x_mm, point.y_mm]] for point in geometry.points],
        dtype=np.float32,
    )
    approximated = cv2.approxPolyDP(contour, epsilon, geometry.closed)
    points = tuple(
        Point(x_mm=float(point[0][0]), y_mm=float(point[0][1]))
        for point in approximated
    )
    return PathGeometry(points=points, closed=geometry.closed)
