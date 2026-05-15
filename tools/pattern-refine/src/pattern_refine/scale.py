"""Scale marker detection for scanned pattern pages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class ScaleCandidate:
    orientation: str
    length_px: float
    length_mm_nominal: float
    expected_length_mm: float
    relative_error: float
    start_px: tuple[int, int]
    end_px: tuple[int, int]
    tick_positions_px: tuple[tuple[int, int], ...] = ()
    tick_interval_px: tuple[float, ...] = ()

    @property
    def measured_pixel_to_mm(self) -> float:
        return self.expected_length_mm / self.length_px

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "orientation": self.orientation,
            "length_px": self.length_px,
            "length_mm_nominal": self.length_mm_nominal,
            "expected_length_mm": self.expected_length_mm,
            "relative_error": self.relative_error,
            "measured_pixel_to_mm": self.measured_pixel_to_mm,
            "start_px": list(self.start_px),
            "end_px": list(self.end_px),
            "tick_positions_px": [list(position) for position in self.tick_positions_px],
            "tick_interval_px": list(self.tick_interval_px),
        }


@dataclass(frozen=True)
class ScaleDetectionReport:
    detected: bool
    method: str
    expected_length_mm: float
    nominal_pixel_to_mm: float
    applied_source: str
    applied_pixel_to_mm: float
    measured_pixel_to_mm: float | None
    marker_to_applied_delta_ratio: float | None
    warnings: tuple[str, ...]
    selected_candidate: ScaleCandidate | None
    candidates: tuple[ScaleCandidate, ...]
    failure_reason: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "method": self.method,
            "expected_length_mm": self.expected_length_mm,
            "nominal_pixel_to_mm": self.nominal_pixel_to_mm,
            "applied_source": self.applied_source,
            "applied_pixel_to_mm": self.applied_pixel_to_mm,
            "measured_pixel_to_mm": self.measured_pixel_to_mm,
            "marker_to_applied_delta_ratio": self.marker_to_applied_delta_ratio,
            "warnings": list(self.warnings),
            "selected_candidate": (
                self.selected_candidate.to_json_dict() if self.selected_candidate is not None else None
            ),
            "candidates": [candidate.to_json_dict() for candidate in self.candidates],
            "failure_reason": self.failure_reason,
        }


def detect_scale_marker(
    lines_image: np.ndarray,
    *,
    page_width_mm: float,
    expected_length_mm: float = 30.0,
    tolerance: float = 0.12,
) -> ScaleDetectionReport:
    """Detect a known straight scale marker from a black-on-white line image."""

    if lines_image.ndim == 3:
        gray = cv2.cvtColor(lines_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = lines_image

    nominal_pixel_to_mm = page_width_mm / gray.shape[1]
    foreground = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1]
    candidates = _tick_marked_scale_candidates(
        foreground,
        nominal_pixel_to_mm=nominal_pixel_to_mm,
        expected_length_mm=expected_length_mm,
        tolerance=tolerance,
    )

    candidates = sorted(candidates, key=lambda candidate: candidate.relative_error)
    selected = candidates[0] if candidates else None
    applied_pixel_to_mm = nominal_pixel_to_mm
    measured_pixel_to_mm = selected.measured_pixel_to_mm if selected is not None else None
    marker_to_applied_delta_ratio = None
    warnings: list[str] = []
    if measured_pixel_to_mm is not None:
        marker_to_applied_delta_ratio = (
            abs(measured_pixel_to_mm - applied_pixel_to_mm) / applied_pixel_to_mm
        )
        if marker_to_applied_delta_ratio > 0.01:
            warnings.append(
                "Detected scale marker differs from the currently applied PDF page-box scale."
            )
        warnings.append(
            "Scale marker detection is reported but not applied to geometry/export in this MVP slice."
        )
    return ScaleDetectionReport(
        detected=selected is not None,
        method="tick-marked-axis-aligned-line",
        expected_length_mm=expected_length_mm,
        nominal_pixel_to_mm=nominal_pixel_to_mm,
        applied_source="pdf-page-box",
        applied_pixel_to_mm=applied_pixel_to_mm,
        measured_pixel_to_mm=measured_pixel_to_mm,
        marker_to_applied_delta_ratio=marker_to_applied_delta_ratio,
        warnings=tuple(warnings),
        selected_candidate=selected,
        candidates=tuple(candidates[:10]),
        failure_reason=(
            None
            if selected is not None
            else "No 4-tick axis-aligned 30mm scale marker candidate found."
        ),
    )


def write_scale_report(report: ScaleDetectionReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _tick_marked_scale_candidates(
    foreground: np.ndarray,
    *,
    nominal_pixel_to_mm: float,
    expected_length_mm: float,
    tolerance: float,
) -> list[ScaleCandidate]:
    expected_length_px = expected_length_mm / nominal_pixel_to_mm
    expected_interval_px = expected_length_px / 3
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats(foreground, 8)
    candidates: list[ScaleCandidate] = []
    for component_index in range(1, component_count):
        x, y, width, height, area = (int(value) for value in stats[component_index])
        if area < 100:
            continue
        long_side = max(width, height)
        short_side = min(width, height)
        if long_side < expected_length_px * (1 - tolerance * 2):
            continue
        if short_side > expected_interval_px * 0.35:
            continue
        component_mask = labels[y : y + height, x : x + width] == component_index
        if width >= height:
            candidate = _scale_candidate_from_component_projection(
                component_mask,
                origin=(x, y),
                orientation="horizontal",
                nominal_pixel_to_mm=nominal_pixel_to_mm,
                expected_length_mm=expected_length_mm,
                expected_interval_px=expected_interval_px,
                tolerance=tolerance,
            )
        else:
            candidate = _scale_candidate_from_component_projection(
                component_mask,
                origin=(x, y),
                orientation="vertical",
                nominal_pixel_to_mm=nominal_pixel_to_mm,
                expected_length_mm=expected_length_mm,
                expected_interval_px=expected_interval_px,
                tolerance=tolerance,
            )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _scale_candidate_from_component_projection(
    component_mask: np.ndarray,
    *,
    origin: tuple[int, int],
    orientation: str,
    nominal_pixel_to_mm: float,
    expected_length_mm: float,
    expected_interval_px: float,
    tolerance: float,
) -> ScaleCandidate | None:
    if orientation == "horizontal":
        projection = component_mask.sum(axis=0)
        groups = _projection_peak_groups(projection, min_peak_height=max(8, component_mask.shape[0] // 3))
    else:
        projection = component_mask.sum(axis=1)
        groups = _projection_peak_groups(projection, min_peak_height=max(8, component_mask.shape[1] // 3))
    centers = tuple((start + end) / 2 for start, end in groups)
    best = _best_four_tick_sequence(centers, expected_interval_px=expected_interval_px, tolerance=tolerance)
    if best is None:
        return None
    intervals = tuple(best[index + 1] - best[index] for index in range(3))
    length_px = best[-1] - best[0]
    length_mm_nominal = length_px * nominal_pixel_to_mm
    relative_error = abs(length_mm_nominal - expected_length_mm) / expected_length_mm
    if relative_error > tolerance:
        return None
    if orientation == "horizontal":
        y_px = origin[1] + int(round(_dominant_axis_position(component_mask, axis=1)))
        tick_positions = tuple((origin[0] + int(round(center)), y_px) for center in best)
        start_px = tick_positions[0]
        end_px = tick_positions[-1]
    else:
        x_px = origin[0] + int(round(_dominant_axis_position(component_mask, axis=0)))
        tick_positions = tuple((x_px, origin[1] + int(round(center))) for center in best)
        start_px = tick_positions[0]
        end_px = tick_positions[-1]
    return ScaleCandidate(
        orientation=orientation,
        length_px=length_px,
        length_mm_nominal=length_mm_nominal,
        expected_length_mm=expected_length_mm,
        relative_error=relative_error,
        start_px=start_px,
        end_px=end_px,
        tick_positions_px=tick_positions,
        tick_interval_px=intervals,
    )


def _projection_peak_groups(
    projection: np.ndarray,
    *,
    min_peak_height: int,
    max_gap_px: int = 3,
) -> tuple[tuple[int, int], ...]:
    peak_indices = np.flatnonzero(projection >= min_peak_height)
    if len(peak_indices) == 0:
        return ()
    groups: list[tuple[int, int]] = []
    start = int(peak_indices[0])
    previous = int(peak_indices[0])
    for value in peak_indices[1:]:
        current = int(value)
        if current - previous > max_gap_px:
            groups.append((start, previous))
            start = current
        previous = current
    groups.append((start, previous))
    return tuple(groups)


def _best_four_tick_sequence(
    centers: tuple[float, ...],
    *,
    expected_interval_px: float,
    tolerance: float,
) -> tuple[float, float, float, float] | None:
    if len(centers) < 4:
        return None
    sorted_centers = sorted(centers)
    best: tuple[float, tuple[float, float, float, float]] | None = None
    for first_index in range(len(sorted_centers) - 3):
        sequence = tuple(sorted_centers[first_index : first_index + 4])
        intervals = [sequence[index + 1] - sequence[index] for index in range(3)]
        if any(interval <= 0 for interval in intervals):
            continue
        max_relative_error = max(
            abs(interval - expected_interval_px) / expected_interval_px
            for interval in intervals
        )
        if max_relative_error > max(tolerance, 0.18):
            continue
        score = sum(
            abs(interval - expected_interval_px) / expected_interval_px
            for interval in intervals
        )
        if best is None or score < best[0]:
            best = (score, sequence)
    return best[1] if best is not None else None


def _dominant_axis_position(component_mask: np.ndarray, *, axis: int) -> float:
    projection = component_mask.sum(axis=axis)
    if projection.sum() == 0:
        return 0.0
    indices = np.arange(len(projection), dtype=float)
    return float((indices * projection).sum() / projection.sum())
