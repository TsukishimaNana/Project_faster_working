"""Delivery readiness verification for final SVG outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DeliveryVerification:
    final_svg_path: Path
    status_report_path: Path
    piece_report_path: Path
    production_quality_report_path: Path | None
    passed: bool
    reasons: tuple[str, ...]
    geometry_source: str | None
    delivery_ready: bool | None
    production_quality_accepted: bool | None
    max_deviation_mm: float | None
    failed_reference_piece_indices: tuple[int, ...]

    @property
    def status_label(self) -> str:
        return "PASS" if self.passed else "FAIL"


def verify_delivery(
    final_svg_path: Path,
    *,
    status_report_path: Path,
    piece_report_path: Path,
    production_quality_report_path: Path | None = None,
    tolerance_mm: float = 0.2,
) -> DeliveryVerification:
    reasons: list[str] = []
    status_data: dict[str, Any] = {}
    piece_data: dict[str, Any] = {}
    production_quality_data: dict[str, Any] = {}

    if not final_svg_path.exists():
        reasons.append(f"final SVG does not exist: {final_svg_path}")
    if not status_report_path.exists():
        reasons.append(f"final status report does not exist: {status_report_path}")
    else:
        status_data = _read_json_object(status_report_path)
    if not piece_report_path.exists():
        reasons.append(f"piece acceptance report does not exist: {piece_report_path}")
    else:
        piece_data = _read_json_object(piece_report_path)
    if production_quality_report_path is None:
        reasons.append("production quality report was not provided")
    elif not production_quality_report_path.exists():
        reasons.append(f"production quality report does not exist: {production_quality_report_path}")
    else:
        production_quality_data = _read_json_object(production_quality_report_path)

    geometry_source = _optional_str(status_data.get("geometry_source"))
    if geometry_source != "reference-guided":
        reasons.append("geometry_source is not reference-guided")

    delivery_ready = _optional_bool(status_data.get("delivery_ready"))
    if delivery_ready is not True:
        reasons.append("delivery_ready is not true")

    piece_accepted = _optional_bool(piece_data.get("accepted"))
    if piece_accepted is not True:
        reasons.append("piece acceptance report accepted is not true")

    max_deviation_mm = _optional_float(piece_data.get("max_deviation_mm"))
    if max_deviation_mm is None:
        reasons.append("piece acceptance report max_deviation_mm is missing")
    elif max_deviation_mm > tolerance_mm:
        reasons.append(
            f"piece acceptance max_deviation_mm {max_deviation_mm:.6f} exceeds "
            f"{tolerance_mm:.6f}"
        )

    failed_indices = _int_tuple(piece_data.get("failed_reference_piece_indices"))
    if failed_indices:
        reasons.append("failed_reference_piece_indices is not empty")

    unmatched_reference = _int_tuple(piece_data.get("unmatched_reference_piece_indices"))
    if unmatched_reference:
        reasons.append("unmatched_reference_piece_indices is not empty")

    production_quality_accepted = _optional_bool(production_quality_data.get("accepted"))
    if production_quality_accepted is not True:
        reasons.append("production quality report accepted is not true")
    production_quality_blockers = _str_tuple(production_quality_data.get("blockers"))
    if production_quality_blockers:
        reasons.append("production quality blockers are not empty")

    return DeliveryVerification(
        final_svg_path=final_svg_path,
        status_report_path=status_report_path,
        piece_report_path=piece_report_path,
        production_quality_report_path=production_quality_report_path,
        passed=not reasons,
        reasons=tuple(reasons),
        geometry_source=geometry_source,
        delivery_ready=delivery_ready,
        production_quality_accepted=production_quality_accepted,
        max_deviation_mm=max_deviation_mm,
        failed_reference_piece_indices=failed_indices,
    )


def format_delivery_verification(result: DeliveryVerification) -> str:
    lines = [
        f"STATUS: {result.status_label}",
        f"FINAL_SVG: {result.final_svg_path}",
        f"GEOMETRY_SOURCE: {result.geometry_source}",
        f"DELIVERY_READY: {result.delivery_ready}",
        f"PIECE_ACCEPTANCE_REPORT: {result.piece_report_path}",
        f"PRODUCTION_QUALITY_REPORT: {result.production_quality_report_path}",
        f"PRODUCTION_QUALITY_ACCEPTED: {result.production_quality_accepted}",
        f"MAX_DEVIATION_MM: {result.max_deviation_mm}",
        f"FAILED_PIECES: {list(result.failed_reference_piece_indices)}",
    ]
    if result.reasons:
        lines.append("FAIL_REASONS:")
        lines.extend(f"- {reason}" for reason in result.reasons)
    return "\n".join(lines)


def _read_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _optional_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _int_tuple(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, int) and not isinstance(item, bool))


def _str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))
