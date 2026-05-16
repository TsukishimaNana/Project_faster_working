"""Reports that keep scan-only diagnostics separate from final delivery geometry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pattern_refine.evaluate import SvgPieceAcceptanceReport
from pattern_refine.report import FinalSvgStatusReport


@dataclass(frozen=True)
class ScanVsReferenceGuidedReport:
    scan_only_layer: str
    final_layer: str
    final_geometry_source: str
    scan_only_delivery_ready: bool
    reference_guided_delivery_ready: bool
    scan_only_max_deviation_mm: float | None
    reference_guided_max_deviation_mm: float | None
    decision: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "scan_only_layer": self.scan_only_layer,
            "final_layer": self.final_layer,
            "final_geometry_source": self.final_geometry_source,
            "scan_only_delivery_ready": self.scan_only_delivery_ready,
            "reference_guided_delivery_ready": self.reference_guided_delivery_ready,
            "scan_only_max_deviation_mm": self.scan_only_max_deviation_mm,
            "reference_guided_max_deviation_mm": self.reference_guided_max_deviation_mm,
            "decision": self.decision,
        }


def build_scan_vs_reference_guided_report(
    *,
    scan_only_layer: Path,
    final_layer: Path,
    final_status_report: FinalSvgStatusReport,
    piece_acceptance_report: SvgPieceAcceptanceReport | None,
    scan_only_max_deviation_mm: float | None,
) -> ScanVsReferenceGuidedReport:
    return ScanVsReferenceGuidedReport(
        scan_only_layer=str(scan_only_layer),
        final_layer=str(final_layer),
        final_geometry_source=final_status_report.final_geometry_source,
        scan_only_delivery_ready=False,
        reference_guided_delivery_ready=(
            final_status_report.delivery_ready
            and piece_acceptance_report is not None
            and piece_acceptance_report.accepted
        ),
        scan_only_max_deviation_mm=scan_only_max_deviation_mm,
        reference_guided_max_deviation_mm=(
            piece_acceptance_report.max_deviation_mm
            if piece_acceptance_report is not None
            else None
        ),
        decision="scan-only remains diagnostic",
    )


def write_scan_vs_reference_guided_report(
    report: ScanVsReferenceGuidedReport,
    report_path: Path,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
