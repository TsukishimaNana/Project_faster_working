"""Overlay and orientation diagnostics for delivery closure."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DeliveryOverlayReport:
    page_rotation: int
    orientation_normalized: bool
    scale_report_path: str
    final_svg_viewbox_matches_page_mm: bool
    overlay_svg_path: str
    manual_overlay_review_required: bool
    known_visual_risks: tuple[str, ...]
    decision: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "page_rotation": self.page_rotation,
            "orientation_normalized": self.orientation_normalized,
            "scale_report_path": self.scale_report_path,
            "final_svg_viewbox_matches_page_mm": self.final_svg_viewbox_matches_page_mm,
            "overlay_svg_path": self.overlay_svg_path,
            "manual_overlay_review_required": self.manual_overlay_review_required,
            "known_visual_risks": list(self.known_visual_risks),
            "decision": self.decision,
        }


def build_delivery_overlay_report(
    *,
    page_rotation: int,
    page_width_mm: float,
    page_height_mm: float,
    final_svg_path: Path,
    scale_report_path: Path,
    overlay_svg_path: Path,
) -> DeliveryOverlayReport:
    viewbox_matches = _svg_viewbox_matches_page_mm(
        final_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    risks: list[str] = []
    if not viewbox_matches:
        risks.append("final SVG viewBox does not match normalized PDF page size in mm")
    return DeliveryOverlayReport(
        page_rotation=page_rotation,
        orientation_normalized=True,
        scale_report_path=str(scale_report_path),
        final_svg_viewbox_matches_page_mm=viewbox_matches,
        overlay_svg_path=str(overlay_svg_path),
        manual_overlay_review_required=True,
        known_visual_risks=tuple(risks),
        decision="overlay diagnostics retained",
    )


def write_delivery_overlay_report(report: DeliveryOverlayReport, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _svg_viewbox_matches_page_mm(
    svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
    tolerance_mm: float = 0.01,
) -> bool:
    text = svg_path.read_text(encoding="utf-8")
    marker = 'viewBox="'
    start = text.find(marker)
    if start < 0:
        return False
    start += len(marker)
    end = text.find('"', start)
    if end < 0:
        return False
    try:
        min_x, min_y, width, height = (float(value) for value in text[start:end].split())
    except ValueError:
        return False
    return (
        abs(min_x) <= tolerance_mm
        and abs(min_y) <= tolerance_mm
        and abs(width - page_width_mm) <= tolerance_mm
        and abs(height - page_height_mm) <= tolerance_mm
    )
