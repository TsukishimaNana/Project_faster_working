from pathlib import Path

import numpy as np
import pytest

from pattern_refine.scale import detect_scale_marker, write_scale_report


def test_detect_scale_marker_finds_axis_aligned_30mm_line(tmp_path: Path) -> None:
    image = np.full((300, 800), 255, dtype=np.uint8)
    image[120:123, 100:401] = 0
    image[105:123, 100:103] = 0
    image[105:123, 200:203] = 0
    image[105:123, 300:303] = 0
    image[105:123, 400:403] = 0

    report = detect_scale_marker(
        image,
        page_width_mm=80.0,
        expected_length_mm=30.0,
    )
    report_path = tmp_path / "scale-report.json"
    write_scale_report(report, report_path)

    assert report.detected is True
    assert report.selected_candidate is not None
    assert report.selected_candidate.orientation == "horizontal"
    assert report.selected_candidate.length_mm_nominal == pytest.approx(30.0, abs=0.5)
    assert len(report.selected_candidate.tick_positions_px) == 4
    assert report.selected_candidate.tick_interval_px == pytest.approx((100, 100, 100), abs=2)
    assert report.measured_pixel_to_mm == pytest.approx(30.0 / 300.0, rel=0.02)
    assert report.applied_source == "pdf-page-box"
    assert report.applied_pixel_to_mm == pytest.approx(0.1)
    assert report.marker_to_applied_delta_ratio == pytest.approx(0.0, abs=0.02)
    report_text = report_path.read_text(encoding="utf-8")
    assert '"detected": true' in report_text
    assert '"applied_source": "pdf-page-box"' in report_text


def test_detect_scale_marker_uses_tick_span_not_unmarked_extension() -> None:
    image = np.full((300, 900), 255, dtype=np.uint8)
    image[120:123, 100:601] = 0
    for x in (100, 200, 300, 400):
        image[105:123, x : x + 3] = 0

    report = detect_scale_marker(
        image,
        page_width_mm=90.0,
        expected_length_mm=30.0,
    )

    assert report.detected is True
    assert report.selected_candidate is not None
    assert report.selected_candidate.start_px[0] == pytest.approx(101, abs=2)
    assert report.selected_candidate.end_px[0] == pytest.approx(401, abs=2)
    assert report.selected_candidate.length_px == pytest.approx(300, abs=4)
    assert report.selected_candidate.length_mm_nominal == pytest.approx(30.0, abs=0.5)


def test_detect_scale_marker_reports_failure_without_candidate() -> None:
    image = np.full((120, 120), 255, dtype=np.uint8)

    report = detect_scale_marker(image, page_width_mm=120.0)

    assert report.detected is False
    assert report.applied_source == "pdf-page-box"
    assert report.applied_pixel_to_mm == pytest.approx(1.0)
    assert report.measured_pixel_to_mm is None
    assert report.marker_to_applied_delta_ratio is None
    assert report.selected_candidate is None
    assert report.failure_reason is not None


def test_detect_scale_marker_warns_when_marker_differs_from_applied_page_box() -> None:
    image = np.full((300, 800), 255, dtype=np.uint8)
    image[120:123, 100:401] = 0
    image[105:123, 100:103] = 0
    image[105:123, 200:203] = 0
    image[105:123, 300:303] = 0
    image[105:123, 400:403] = 0

    report = detect_scale_marker(
        image,
        page_width_mm=85.0,
        expected_length_mm=30.0,
    )

    assert report.detected is True
    assert report.applied_source == "pdf-page-box"
    assert report.marker_to_applied_delta_ratio is not None
    assert report.marker_to_applied_delta_ratio > 0.01
    assert report.warnings
