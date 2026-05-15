from pattern_refine.classify import classify_geometries, write_classification_report
from pattern_refine.geometry import PathGeometry, Point


def test_classify_geometries_keeps_large_medium_and_linear_mark_candidates(tmp_path) -> None:
    large = PathGeometry(
        points=(
            Point(0, 0),
            Point(20, 0),
            Point(20, 10),
            Point(0, 10),
        ),
        closed=True,
    )
    medium = PathGeometry(
        points=(
            Point(0, 0),
            Point(5, 0),
            Point(5, 3),
            Point(0, 3),
        ),
        closed=True,
    )
    linear = PathGeometry(
        points=(
            Point(0, 0),
            Point(30, 0),
            Point(30, 0.3),
            Point(0, 0.3),
        ),
        closed=True,
    )
    noise = PathGeometry(
        points=(
            Point(0, 0),
            Point(1, 0),
            Point(1, 1),
            Point(0, 1),
        ),
        closed=True,
    )

    report = classify_geometries((large, medium, linear, noise))
    report_path = tmp_path / "classification-report.json"
    write_classification_report(report, report_path)

    assert report.input_count == 4
    assert report.kept_count == 3
    assert report.removed_count == 1
    assert report.label_counts["main_outline_candidate"] == 1
    assert report.label_counts["secondary_outline_candidate"] == 1
    assert report.label_counts["protected_linear_mark_candidate"] == 1
    assert report.label_counts["noise_candidate"] == 1
    assert report.kept_geometries() == (large, medium, linear)
    assert '"noise_candidate"' in report_path.read_text(encoding="utf-8")
