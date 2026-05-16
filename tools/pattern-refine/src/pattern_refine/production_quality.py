"""Production cleanliness/topology gate for final SVG candidates."""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import atan2, cos, hypot, sin
from pathlib import Path
import re
from typing import Any

from lxml import etree


SVG_NS = {"svg": "http://www.w3.org/2000/svg"}
COMMAND_RE = re.compile(r"[MmLlHhVvCcQqSsTtAaZz]")
NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


@dataclass(frozen=True)
class ProductionQualityIssue:
    issue_type: str
    object_id: str | None
    severity: str
    detail: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "object_id": self.object_id,
            "severity": self.severity,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ProductionQualityReport:
    input_svg_path: str
    accepted: bool
    manual_review_required: bool
    blockers: tuple[str, ...]
    issue_count: int
    path_count: int
    line_count: int
    rect_count: int
    max_path_command_count: int
    max_path_point_count: int
    max_short_segment_ratio: float
    overlapping_segment_pair_count: int
    open_path_count: int
    issues: tuple[ProductionQualityIssue, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "input_svg_path": self.input_svg_path,
            "accepted": self.accepted,
            "manual_review_required": self.manual_review_required,
            "blockers": list(self.blockers),
            "issue_count": self.issue_count,
            "path_count": self.path_count,
            "line_count": self.line_count,
            "rect_count": self.rect_count,
            "max_path_command_count": self.max_path_command_count,
            "max_path_point_count": self.max_path_point_count,
            "max_short_segment_ratio": self.max_short_segment_ratio,
            "overlapping_segment_pair_count": self.overlapping_segment_pair_count,
            "open_path_count": self.open_path_count,
            "issues": [issue.to_json_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class _Segment:
    object_id: str | None
    start: tuple[float, float]
    end: tuple[float, float]

    @property
    def length(self) -> float:
        return hypot(self.end[0] - self.start[0], self.end[1] - self.start[1])


def evaluate_production_quality(svg_path: Path) -> ProductionQualityReport:
    root = etree.fromstring(svg_path.read_bytes())
    paths = root.xpath(".//svg:path", namespaces=SVG_NS)
    lines = root.xpath(".//svg:line", namespaces=SVG_NS)
    rects = root.xpath(".//svg:rect", namespaces=SVG_NS)

    issues: list[ProductionQualityIssue] = []
    path_segments: list[_Segment] = []
    max_command_count = 0
    max_point_count = 0
    max_short_segment_ratio = 0.0
    open_path_count = 0

    for path in paths:
        object_id = _object_id(path)
        d = path.get("d", "")
        command_count = len(COMMAND_RE.findall(d))
        points = _path_points(d)
        segments = _polyline_segments(object_id, points, _path_is_closed(d))
        short_segment_ratio = _short_segment_ratio(segments)
        max_command_count = max(max_command_count, command_count)
        max_point_count = max(max_point_count, len(points))
        max_short_segment_ratio = max(max_short_segment_ratio, short_segment_ratio)
        path_segments.extend(segments)

        if not _path_is_closed(d):
            open_path_count += 1
            issues.append(
                ProductionQualityIssue(
                    issue_type="open_or_broken_contour_detected",
                    object_id=object_id,
                    severity="blocker",
                    detail="Path is not explicitly closed with Z.",
                )
            )
        if command_count > 120 or len(points) > 240 or short_segment_ratio > 0.55:
            issues.append(
                ProductionQualityIssue(
                    issue_type="jagged_polyline_detected",
                    object_id=object_id,
                    severity="blocker",
                    detail=(
                        f"path_commands={command_count}, points={len(points)}, "
                        f"short_segment_ratio={short_segment_ratio:.3f}"
                    ),
                )
            )

    line_segments = [_line_segment(line) for line in lines]
    all_segments = [segment for segment in (*path_segments, *line_segments) if segment.length > 0.05]
    overlapping_pair_count = _overlapping_pair_count(all_segments)
    if overlapping_pair_count:
        issues.append(
            ProductionQualityIssue(
                issue_type="overlapping_lines_detected",
                object_id=None,
                severity="blocker",
                detail=f"{overlapping_pair_count} near-overlapping segment pairs detected.",
            )
        )

    if not paths:
        issues.append(
            ProductionQualityIssue(
                issue_type="object_semantics_unclear",
                object_id=None,
                severity="blocker",
                detail="No piece paths found in the final SVG.",
            )
        )

    blockers = tuple(sorted({issue.issue_type for issue in issues if issue.severity == "blocker"}))
    manual_review_required = True
    if manual_review_required:
        blockers = tuple((*blockers, "manual_production_review_required"))
    return ProductionQualityReport(
        input_svg_path=str(svg_path),
        accepted=not blockers,
        manual_review_required=manual_review_required,
        blockers=blockers,
        issue_count=len(issues),
        path_count=len(paths),
        line_count=len(lines),
        rect_count=len(rects),
        max_path_command_count=max_command_count,
        max_path_point_count=max_point_count,
        max_short_segment_ratio=max_short_segment_ratio,
        overlapping_segment_pair_count=overlapping_pair_count,
        open_path_count=open_path_count,
        issues=tuple(issues),
    )


def write_production_quality_report(report: ProductionQualityReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _object_id(element: etree._Element) -> str | None:
    value = element.get("id")
    return value if value else None


def _path_is_closed(d: str) -> bool:
    return bool(re.search(r"[Zz]\s*$", d.strip()))


def _path_points(d: str) -> tuple[tuple[float, float], ...]:
    numbers = [float(match.group(0)) for match in NUMBER_RE.finditer(d)]
    return tuple(zip(numbers[0::2], numbers[1::2], strict=False))


def _polyline_segments(
    object_id: str | None,
    points: tuple[tuple[float, float], ...],
    closed: bool,
) -> list[_Segment]:
    if len(points) < 2:
        return []
    segments = [_Segment(object_id=object_id, start=start, end=end) for start, end in zip(points, points[1:])]
    if closed:
        segments.append(_Segment(object_id=object_id, start=points[-1], end=points[0]))
    return segments


def _line_segment(element: etree._Element) -> _Segment:
    return _Segment(
        object_id=_object_id(element),
        start=(_float_attr(element, "x1"), _float_attr(element, "y1")),
        end=(_float_attr(element, "x2"), _float_attr(element, "y2")),
    )


def _float_attr(element: etree._Element, name: str) -> float:
    value = element.get(name)
    return float(value) if value is not None else 0.0


def _short_segment_ratio(segments: list[_Segment]) -> float:
    if not segments:
        return 0.0
    short_count = sum(1 for segment in segments if segment.length < 0.35)
    return short_count / len(segments)


def _overlapping_pair_count(segments: list[_Segment]) -> int:
    pair_count = 0
    for index, first in enumerate(segments):
        for second in segments[index + 1 :]:
            if first.object_id == second.object_id:
                continue
            if _segments_nearly_overlap(first, second):
                pair_count += 1
    return pair_count


def _segments_nearly_overlap(first: _Segment, second: _Segment) -> bool:
    if first.length < 0.5 or second.length < 0.5:
        return False
    first_angle = atan2(first.end[1] - first.start[1], first.end[0] - first.start[0])
    second_angle = atan2(second.end[1] - second.start[1], second.end[0] - second.start[0])
    if abs(sin(first_angle - second_angle)) > 0.05:
        return False
    if abs(_signed_distance_to_line(second.start, first)) > 0.15:
        return False
    first_axis = (cos(first_angle), sin(first_angle))
    first_range = _projected_range(first, first.start, first_axis)
    second_range = _projected_range(second, first.start, first_axis)
    overlap = min(first_range[1], second_range[1]) - max(first_range[0], second_range[0])
    return overlap > 0.5


def _signed_distance_to_line(point: tuple[float, float], segment: _Segment) -> float:
    dx = segment.end[0] - segment.start[0]
    dy = segment.end[1] - segment.start[1]
    length = hypot(dx, dy)
    if length == 0:
        return 0.0
    return ((point[0] - segment.start[0]) * dy - (point[1] - segment.start[1]) * dx) / length


def _projected_range(
    segment: _Segment,
    origin: tuple[float, float],
    axis: tuple[float, float],
) -> tuple[float, float]:
    start = (segment.start[0] - origin[0]) * axis[0] + (segment.start[1] - origin[1]) * axis[1]
    end = (segment.end[0] - origin[0]) * axis[0] + (segment.end[1] - origin[1]) * axis[1]
    return (min(start, end), max(start, end))
