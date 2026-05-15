"""Feature classification for protecting pattern-critical geometry."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pattern_refine.geometry import PathGeometry, Point


@dataclass(frozen=True)
class Feature:
    kind: str
    path_index: int
    point_index: int | None
    segment_index: int | None
    position: Point
    confidence: float
    reason: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path_index": self.path_index,
            "point_index": self.point_index,
            "segment_index": self.segment_index,
            "position": {"x_mm": self.position.x_mm, "y_mm": self.position.y_mm},
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FeatureReport:
    feature_counts: dict[str, int]
    features: tuple[Feature, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "feature_counts": self.feature_counts,
            "features": [feature.to_json_dict() for feature in self.features],
        }


def classify_features(geometries: tuple[PathGeometry, ...]) -> FeatureReport:
    features: list[Feature] = []
    for path_index, geometry in enumerate(geometries, start=1):
        features.extend(_classify_path_features(path_index, geometry))
    counts: dict[str, int] = {}
    for feature in features:
        counts[feature.kind] = counts.get(feature.kind, 0) + 1
    return FeatureReport(feature_counts=counts, features=tuple(features))


def write_feature_report(report: FeatureReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _classify_path_features(path_index: int, geometry: PathGeometry) -> list[Feature]:
    triangle = _triangle_mark_feature(path_index, geometry)
    if triangle is not None:
        return [triangle]
    mark = _short_linear_mark_feature(path_index, geometry)
    if mark is not None:
        return [mark]

    features: list[Feature] = []
    notch_features = _notch_features(path_index, geometry)
    features.extend(notch_features)
    notch_point_indices = {
        feature.point_index for feature in notch_features if feature.point_index is not None
    }
    features.extend(
        _corner_features(
            path_index,
            geometry,
            excluded_point_indices=notch_point_indices,
        )
    )
    features.extend(_straight_segment_features(path_index, geometry))
    return features


def _notch_features(path_index: int, geometry: PathGeometry) -> list[Feature]:
    """Find local V-shaped production marks on a pattern edge."""

    if len(geometry.points) < 5:
        return []
    features: list[Feature] = []
    point_count = len(geometry.points)
    indices = range(point_count) if geometry.closed else range(1, point_count - 1)
    for point_index in indices:
        previous_point = geometry.points[(point_index - 1) % point_count]
        point = geometry.points[point_index]
        next_point = geometry.points[(point_index + 1) % point_count]
        incoming = _distance(previous_point, point)
        outgoing = _distance(point, next_point)
        if not (0.8 <= incoming <= 8.0 and 0.8 <= outgoing <= 8.0):
            continue
        angle = _turn_angle_degrees(previous_point, point, next_point)
        if not (25 <= angle <= 75):
            continue
        before = geometry.points[(point_index - 2) % point_count]
        after = geometry.points[(point_index + 2) % point_count]
        neighbor_span = max(_distance(before, previous_point), _distance(next_point, after))
        if neighbor_span < 2.0:
            continue
        features.append(
            Feature(
                kind="notch_candidate",
                path_index=path_index,
                point_index=point_index + 1,
                segment_index=None,
                position=point,
                confidence=0.8 if angle <= 60 else 0.65,
                reason=(
                    f"Short V-shaped turn angle is {angle:.1f} degrees "
                    f"with {incoming:.1f}mm/{outgoing:.1f}mm sides."
                ),
            )
        )
    return features


def _triangle_mark_feature(path_index: int, geometry: PathGeometry) -> Feature | None:
    """Find compact triangular closed marks before smoothing can round them away."""

    if not geometry.closed or len(geometry.points) < 3 or len(geometry.points) > 8:
        return None
    x_min, y_min, x_max, y_max = geometry.bounds
    width = x_max - x_min
    height = y_max - y_min
    if width > 16.0 or height > 16.0 or geometry.area_mm2 > 90.0:
        return None
    if width < 1.0 or height < 1.0 or geometry.area_mm2 < 1.0:
        return None
    sharp_count = 0
    for point_index, point in enumerate(geometry.points):
        previous_point = geometry.points[(point_index - 1) % len(geometry.points)]
        next_point = geometry.points[(point_index + 1) % len(geometry.points)]
        incoming = _distance(previous_point, point)
        outgoing = _distance(point, next_point)
        if incoming < 0.5 or outgoing < 0.5:
            continue
        angle = _turn_angle_degrees(previous_point, point, next_point)
        if 30 <= angle <= 105:
            sharp_count += 1
    if sharp_count < 3:
        return None
    return Feature(
        kind="triangle_mark_candidate",
        path_index=path_index,
        point_index=None,
        segment_index=None,
        position=Point((x_min + x_max) / 2, (y_min + y_max) / 2),
        confidence=0.75,
        reason=(
            f"Compact closed contour has {sharp_count} sharp triangle-like turns "
            f"and bbox {width:.1f}mm x {height:.1f}mm."
        ),
    )


def _corner_features(
    path_index: int,
    geometry: PathGeometry,
    *,
    excluded_point_indices: set[int] | None = None,
) -> list[Feature]:
    if len(geometry.points) < 3:
        return []
    features: list[Feature] = []
    excluded = excluded_point_indices or set()
    point_count = len(geometry.points)
    indices = range(point_count) if geometry.closed else range(1, point_count - 1)
    for point_index in indices:
        if point_index + 1 in excluded:
            continue
        previous_point = geometry.points[(point_index - 1) % point_count]
        point = geometry.points[point_index]
        next_point = geometry.points[(point_index + 1) % point_count]
        incoming = _distance(previous_point, point)
        outgoing = _distance(point, next_point)
        if incoming < 0.5 or outgoing < 0.5:
            continue
        angle = _turn_angle_degrees(previous_point, point, next_point)
        if 35 <= angle <= 145:
            kind = "right_angle_candidate" if 75 <= angle <= 105 else "corner_candidate"
            features.append(
                Feature(
                    kind=kind,
                    path_index=path_index,
                    point_index=point_index + 1,
                    segment_index=None,
                    position=point,
                    confidence=_angle_confidence(angle),
                    reason=f"Local turn angle is {angle:.1f} degrees.",
                )
            )
    return features


def _straight_segment_features(path_index: int, geometry: PathGeometry) -> list[Feature]:
    if len(geometry.points) < 2:
        return []
    features: list[Feature] = []
    segment_count = len(geometry.points) if geometry.closed else len(geometry.points) - 1
    for segment_index in range(segment_count):
        start = geometry.points[segment_index]
        end = geometry.points[(segment_index + 1) % len(geometry.points)]
        length = _distance(start, end)
        if length < 8.0:
            continue
        features.append(
            Feature(
                kind="straight_edge_candidate",
                path_index=path_index,
                point_index=None,
                segment_index=segment_index + 1,
                position=Point((start.x_mm + end.x_mm) / 2, (start.y_mm + end.y_mm) / 2),
                confidence=min(1.0, length / 50.0),
                reason=f"Segment length is {length:.1f}mm.",
            )
        )
    return features


def _short_linear_mark_feature(path_index: int, geometry: PathGeometry) -> Feature | None:
    x_min, y_min, x_max, y_max = geometry.bounds
    width = x_max - x_min
    height = y_max - y_min
    long_side = max(width, height)
    short_side = min(width, height)
    if 10 <= long_side <= 60 and short_side <= 3 and geometry.area_mm2 <= 80:
        return Feature(
            kind="short_alignment_mark_candidate",
            path_index=path_index,
            point_index=None,
            segment_index=None,
            position=Point((x_min + x_max) / 2, (y_min + y_max) / 2),
            confidence=0.75,
            reason=f"Long thin contour is {long_side:.1f}mm x {short_side:.1f}mm.",
        )
    return None


def _turn_angle_degrees(previous_point: Point, point: Point, next_point: Point) -> float:
    v1 = (previous_point.x_mm - point.x_mm, previous_point.y_mm - point.y_mm)
    v2 = (next_point.x_mm - point.x_mm, next_point.y_mm - point.y_mm)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])
    if mag1 == 0 or mag2 == 0:
        return 180.0
    cosine = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cosine))


def _angle_confidence(angle: float) -> float:
    if 75 <= angle <= 105:
        return 0.9
    return 0.65


def _distance(start: Point, end: Point) -> float:
    return math.hypot(end.x_mm - start.x_mm, end.y_mm - start.y_mm)
