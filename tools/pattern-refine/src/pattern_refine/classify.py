"""Candidate geometry classification for conservative cleanup."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pattern_refine.geometry import PathGeometry


@dataclass(frozen=True)
class ClassifiedGeometry:
    index: int
    geometry: PathGeometry
    label: str
    keep: bool
    reason: str
    area_mm2: float
    perimeter_mm: float
    width_mm: float
    height_mm: float
    point_count: int
    bbox: tuple[float, float, float, float]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "label": self.label,
            "keep": self.keep,
            "reason": self.reason,
            "area_mm2": self.area_mm2,
            "perimeter_mm": self.perimeter_mm,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "point_count": self.point_count,
            "bbox": list(self.bbox),
        }


@dataclass(frozen=True)
class ClassificationReport:
    input_count: int
    kept_count: int
    removed_count: int
    label_counts: dict[str, int]
    candidates: tuple[ClassifiedGeometry, ...]

    def kept_geometries(self) -> tuple[PathGeometry, ...]:
        return tuple(candidate.geometry for candidate in self.candidates if candidate.keep)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "input_count": self.input_count,
            "kept_count": self.kept_count,
            "removed_count": self.removed_count,
            "label_counts": self.label_counts,
            "candidates": [candidate.to_json_dict() for candidate in self.candidates],
        }


def classify_geometries(geometries: tuple[PathGeometry, ...]) -> ClassificationReport:
    """Classify raw vector candidates before writing object-level cleaned SVG."""

    classified = tuple(
        _classify_geometry(index, geometry) for index, geometry in enumerate(geometries, start=1)
    )
    label_counts: dict[str, int] = {}
    for candidate in classified:
        label_counts[candidate.label] = label_counts.get(candidate.label, 0) + 1
    kept_count = sum(1 for candidate in classified if candidate.keep)
    return ClassificationReport(
        input_count=len(classified),
        kept_count=kept_count,
        removed_count=len(classified) - kept_count,
        label_counts=label_counts,
        candidates=classified,
    )


def write_classification_report(report: ClassificationReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _classify_geometry(index: int, geometry: PathGeometry) -> ClassifiedGeometry:
    x_min, y_min, x_max, y_max = geometry.bounds
    width_mm = x_max - x_min
    height_mm = y_max - y_min
    area_mm2 = geometry.area_mm2
    perimeter_mm = geometry.perimeter_mm
    label = "noise_candidate"
    keep = False
    reason = "Small closed contour below conservative keep thresholds."

    if area_mm2 >= 100:
        label = "main_outline_candidate"
        keep = True
        reason = "Large contour likely belongs to a pattern piece."
    elif area_mm2 >= 10:
        label = "secondary_outline_candidate"
        keep = True
        reason = "Medium contour retained for downstream object reconstruction."
    elif _is_protected_linear_mark(width_mm, height_mm, area_mm2):
        label = "protected_linear_mark_candidate"
        keep = True
        reason = "Long thin contour retained as possible scale/alignment mark."

    return ClassifiedGeometry(
        index=index,
        geometry=geometry,
        label=label,
        keep=keep,
        reason=reason,
        area_mm2=area_mm2,
        perimeter_mm=perimeter_mm,
        width_mm=width_mm,
        height_mm=height_mm,
        point_count=len(geometry.points),
        bbox=(x_min, y_min, x_max, y_max),
    )


def _is_protected_linear_mark(width_mm: float, height_mm: float, area_mm2: float) -> bool:
    long_side = max(width_mm, height_mm)
    short_side = min(width_mm, height_mm)
    return area_mm2 >= 5 and long_side >= 25 and short_side <= 3
