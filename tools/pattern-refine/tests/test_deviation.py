import pytest

from pattern_refine.deviation import build_simplification_deviation_report
from pattern_refine.geometry import PathGeometry, Point


def test_build_simplification_deviation_report_accepts_identical_path() -> None:
    source = PathGeometry(
        points=(
            Point(0, 0),
            Point(10, 0),
            Point(10, 10),
            Point(0, 10),
        ),
        closed=True,
    )

    report = build_simplification_deviation_report((source,), (source,), tolerance_mm=0.2)

    assert report.accepted is True
    assert report.matched_path_count == 1
    assert report.max_deviation_mm == pytest.approx(0.0)
    assert report.path_deviations[0].accepted is True


def test_build_simplification_deviation_report_rejects_excessive_deviation() -> None:
    source = PathGeometry(
        points=(
            Point(0, 0),
            Point(5, 0.5),
            Point(10, 0),
            Point(10, 10),
            Point(0, 10),
        ),
        closed=True,
    )
    simplified = PathGeometry(
        points=(
            Point(0, 0),
            Point(10, 0),
            Point(10, 10),
            Point(0, 10),
        ),
        closed=True,
    )

    report = build_simplification_deviation_report((source,), (simplified,), tolerance_mm=0.2)

    assert report.accepted is False
    assert report.matched_path_count == 1
    assert report.max_deviation_mm is not None
    assert report.max_deviation_mm > 0.2
    assert report.path_deviations[0].accepted is False
