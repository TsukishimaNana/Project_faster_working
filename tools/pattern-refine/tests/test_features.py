from pattern_refine.features import classify_features, write_feature_report
from pattern_refine.geometry import PathGeometry, Point


def test_classify_features_finds_right_angles_and_straight_edges(tmp_path) -> None:
    rectangle = PathGeometry(
        points=(
            Point(0, 0),
            Point(20, 0),
            Point(20, 10),
            Point(0, 10),
        ),
        closed=True,
    )

    report = classify_features((rectangle,))
    report_path = tmp_path / "feature-report.json"
    write_feature_report(report, report_path)

    assert report.feature_counts["right_angle_candidate"] == 4
    assert report.feature_counts["straight_edge_candidate"] == 4
    assert "right_angle_candidate" in report_path.read_text(encoding="utf-8")


def test_classify_features_finds_short_alignment_mark_candidate() -> None:
    mark = PathGeometry(
        points=(
            Point(0, 0),
            Point(30, 0),
            Point(30, 1),
            Point(0, 1),
        ),
        closed=True,
    )

    report = classify_features((mark,))

    assert report.feature_counts["short_alignment_mark_candidate"] == 1
    assert report.feature_counts == {"short_alignment_mark_candidate": 1}


def test_classify_features_finds_notch_candidate() -> None:
    notched_edge = PathGeometry(
        points=(
            Point(0, 0),
            Point(10, 0),
            Point(12, 3),
            Point(14, 0),
            Point(24, 0),
            Point(24, 20),
            Point(0, 20),
        ),
        closed=True,
    )

    report = classify_features((notched_edge,))

    assert report.feature_counts["notch_candidate"] == 1
    notch = next(feature for feature in report.features if feature.kind == "notch_candidate")
    assert notch.point_index == 3
    assert not any(
        feature.kind == "corner_candidate" and feature.point_index == notch.point_index
        for feature in report.features
    )


def test_classify_features_finds_triangle_mark_candidate() -> None:
    triangle = PathGeometry(
        points=(
            Point(0, 0),
            Point(8, 0),
            Point(4, 7),
        ),
        closed=True,
    )

    report = classify_features((triangle,))

    assert report.feature_counts["triangle_mark_candidate"] == 1
    assert report.feature_counts == {"triangle_mark_candidate": 1}
