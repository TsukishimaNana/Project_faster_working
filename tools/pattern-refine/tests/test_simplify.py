from pattern_refine.deviation import build_simplification_deviation_report
from pattern_refine.geometry import PathGeometry, Point
from pattern_refine.simplify import simplify_geometry_with_tolerance


def test_simplify_geometry_with_tolerance_reduces_points_without_exceeding_tolerance() -> None:
    source = PathGeometry(
        points=tuple(Point(x / 10, 0.02 if x % 2 else 0.0) for x in range(101)),
        closed=False,
    )

    simplified = simplify_geometry_with_tolerance(source, tolerance_mm=0.2)
    report = build_simplification_deviation_report((source,), (simplified,), tolerance_mm=0.2)

    assert len(simplified.points) < len(source.points)
    assert report.accepted is True


def test_simplify_geometry_with_tolerance_keeps_source_when_no_candidate_passes() -> None:
    source = PathGeometry(
        points=(
            Point(0, 0),
            Point(0.1, 2),
            Point(0.2, 0),
            Point(0.3, 2),
        ),
        closed=False,
    )

    simplified = simplify_geometry_with_tolerance(source, tolerance_mm=0.01)

    assert len(simplified.points) == len(source.points)
