from pattern_refine.features import Feature, FeatureReport
from pattern_refine.geometry import PathGeometry, Point
from pattern_refine.smooth import smooth_geometries


def test_smooth_geometries_keeps_protected_corner_point_fixed() -> None:
    geometry = PathGeometry(
        points=(
            Point(0, 0),
            Point(5, 1),
            Point(10, 0),
            Point(10, 10),
            Point(0, 10),
        ),
        closed=True,
    )
    feature_report = FeatureReport(
        feature_counts={"corner_candidate": 1},
        features=(
            Feature(
                kind="corner_candidate",
                path_index=1,
                point_index=2,
                segment_index=None,
                position=geometry.points[1],
                confidence=0.8,
                reason="test",
            ),
        ),
    )

    smoothed, report = smooth_geometries((geometry,), feature_report, tolerance_mm=0.2, alpha=0.2)

    assert smoothed[0].points[1] == geometry.points[1]
    assert report.protected_point_count == 1


def test_smooth_geometries_keeps_protected_notch_point_fixed() -> None:
    geometry = PathGeometry(
        points=(
            Point(0, 0),
            Point(5, 0),
            Point(6, 2),
            Point(7, 0),
            Point(12, 0),
            Point(12, 10),
            Point(0, 10),
        ),
        closed=True,
    )
    feature_report = FeatureReport(
        feature_counts={"notch_candidate": 1},
        features=(
            Feature(
                kind="notch_candidate",
                path_index=1,
                point_index=3,
                segment_index=None,
                position=geometry.points[2],
                confidence=0.8,
                reason="test",
            ),
        ),
    )

    smoothed, report = smooth_geometries((geometry,), feature_report, tolerance_mm=1.0, alpha=0.2)

    assert smoothed[0].points[2] == geometry.points[2]
    assert report.protected_point_count == 1


def test_smooth_geometries_skips_protected_triangle_mark_path() -> None:
    geometry = PathGeometry(
        points=(
            Point(0, 0),
            Point(8, 0),
            Point(4, 7),
        ),
        closed=True,
    )
    feature_report = FeatureReport(
        feature_counts={"triangle_mark_candidate": 1},
        features=(
            Feature(
                kind="triangle_mark_candidate",
                path_index=1,
                point_index=None,
                segment_index=None,
                position=Point(4, 3.5),
                confidence=0.75,
                reason="test",
            ),
        ),
    )

    smoothed, report = smooth_geometries((geometry,), feature_report, tolerance_mm=10.0, alpha=0.5)

    assert smoothed[0] == geometry
    assert report.path_results[0].protected_path is True


def test_smooth_geometries_reports_moved_points_when_accepted() -> None:
    geometry = PathGeometry(
        points=tuple(Point(x / 10, 0.02 if x % 2 else 0.0) for x in range(30)),
        closed=False,
    )
    feature_report = FeatureReport(feature_counts={}, features=())

    smoothed, report = smooth_geometries((geometry,), feature_report, tolerance_mm=0.2, alpha=0.2)

    assert report.accepted_path_count == 1
    assert report.moved_point_count > 0
    assert smoothed[0] != geometry
