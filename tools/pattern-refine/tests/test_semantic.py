from pathlib import Path

import numpy as np

from pattern_refine.geometry import LineGeometry, PathGeometry, Point, RectGeometry
from pattern_refine.scale import detect_scale_marker
from pattern_refine.semantic import (
    _centerline_piece_score,
    _fill_reference_near_anchor_gaps,
    _path_distance_summary,
    _snap_compact_piece_edge_anchors,
    _snap_large_piece_extreme_anchors,
    reconstruct_semantic_geometries,
    write_semantic_geometry_report,
)


def test_reconstruct_semantic_geometries_promotes_thin_contour_to_line() -> None:
    thin = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(40.0, 0.0),
            Point(40.0, 2.0),
            Point(0.0, 2.0),
        ),
        closed=True,
    )

    geometries, report = reconstruct_semantic_geometries((thin,))

    assert isinstance(geometries[0], LineGeometry)
    assert report.path_count == 0
    assert report.line_count == 1
    assert report.promoted_line_count == 1


def test_reconstruct_semantic_geometries_promotes_rectangular_contour_to_rect() -> None:
    rectangle = PathGeometry(
        points=(
            Point(10.0, 20.0),
            Point(30.0, 20.0),
            Point(30.0, 50.0),
            Point(10.0, 50.0),
        ),
        closed=True,
    )

    geometries, report = reconstruct_semantic_geometries((rectangle,))

    assert isinstance(geometries[0], RectGeometry)
    assert report.rect_count == 1
    assert report.promoted_rect_count == 1


def test_reconstruct_semantic_geometries_promotes_edge_aligned_rect_contour() -> None:
    points = []
    for x in range(0, 61, 10):
        points.append(Point(float(x), 0.0))
    for y in range(5, 26, 5):
        points.append(Point(60.0, float(y)))
    for x in range(50, -1, -10):
        points.append(Point(float(x), 25.0))
    for y in range(20, 0, -5):
        points.append(Point(0.0, float(y)))
    rectangle = PathGeometry(points=tuple(points), closed=True)

    geometries, report = reconstruct_semantic_geometries((rectangle,))

    assert isinstance(geometries[0], RectGeometry)
    assert report.rect_count == 1


def test_write_semantic_geometry_report(tmp_path: Path) -> None:
    thin = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(40.0, 0.0),
            Point(40.0, 2.0),
            Point(0.0, 2.0),
        ),
        closed=True,
    )
    _, report = reconstruct_semantic_geometries((thin,))
    report_path = tmp_path / "semantic-report.json"

    write_semantic_geometry_report(report, report_path)

    assert '"line_count": 1' in report_path.read_text(encoding="utf-8")


def test_reconstruct_semantic_geometries_discards_compact_noise_path() -> None:
    noise = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(5.0, 0.0),
            Point(5.0, 5.0),
            Point(0.0, 5.0),
        ),
        closed=True,
    )

    geometries, report = reconstruct_semantic_geometries((noise,))

    assert geometries == ()
    assert report.discarded_small_path_count == 1


def test_reconstruct_semantic_geometries_adds_scale_marker_lines() -> None:
    image = np.full((300, 800), 255, dtype=np.uint8)
    image[120:123, 100:401] = 0
    image[105:123, 100:103] = 0
    image[105:123, 200:203] = 0
    image[105:123, 300:303] = 0
    image[105:123, 400:403] = 0
    scale_report = detect_scale_marker(image, page_width_mm=80.0, expected_length_mm=30.0)

    geometries, report = reconstruct_semantic_geometries((), scale_report=scale_report)

    assert len(geometries) == 5
    assert all(isinstance(geometry, LineGeometry) for geometry in geometries)
    assert report.line_count == 5
    assert report.reconstructed_scale_line_count == 5


def test_reconstruct_semantic_geometries_adds_ticks_for_promoted_scale_line() -> None:
    scale_contour = PathGeometry(
        points=(
            Point(10.0, 20.0),
            Point(40.0, 20.0),
            Point(40.0, 21.0),
            Point(10.0, 21.0),
        ),
        closed=True,
    )
    pattern_piece = PathGeometry(
        points=(
            Point(60.0, 10.0),
            Point(90.0, 10.0),
            Point(90.0, 40.0),
            Point(60.0, 40.0),
        ),
        closed=True,
    )

    geometries, report = reconstruct_semantic_geometries((scale_contour, pattern_piece))

    assert sum(isinstance(geometry, LineGeometry) for geometry in geometries) == 5
    assert report.rect_count == 1
    assert report.promoted_line_count == 1
    assert report.reconstructed_scale_line_count == 4


def test_reconstruct_semantic_geometries_deduplicates_detected_scale_line() -> None:
    scale_contour = PathGeometry(
        points=(
            Point(10.0, 20.0),
            Point(40.0, 20.0),
            Point(40.0, 21.0),
            Point(10.0, 21.0),
        ),
        closed=True,
    )
    pattern_piece = PathGeometry(
        points=(
            Point(60.0, 10.0),
            Point(90.0, 10.0),
            Point(90.0, 40.0),
            Point(60.0, 40.0),
        ),
        closed=True,
    )
    image = np.full((300, 800), 255, dtype=np.uint8)
    image[204:207, 100:401] = 0
    image[186:207, 100:103] = 0
    image[186:207, 200:203] = 0
    image[186:207, 300:303] = 0
    image[186:207, 400:403] = 0
    scale_report = detect_scale_marker(image, page_width_mm=80.0, expected_length_mm=30.0)

    geometries, report = reconstruct_semantic_geometries(
        (scale_contour, pattern_piece),
        scale_report=scale_report,
    )

    assert sum(isinstance(geometry, LineGeometry) for geometry in geometries) == 5
    assert report.rect_count == 1
    assert report.deduplicated_line_count >= 1


def test_reconstruct_semantic_geometries_uses_centerline_paths_but_keeps_outline_rect() -> None:
    rectangle = PathGeometry(
        points=(
            Point(10.0, 20.0),
            Point(30.0, 20.0),
            Point(30.0, 50.0),
            Point(10.0, 50.0),
        ),
        closed=True,
    )
    outline_piece = PathGeometry(
        points=(
            Point(50.0, 20.0),
            Point(90.0, 20.0),
            Point(84.0, 44.0),
            Point(72.0, 66.0),
            Point(54.0, 48.0),
        ),
        closed=True,
    )
    centerline_piece = PathGeometry(
        points=(Point(50.0, 40.0), Point(70.0, 40.0), Point(90.0, 40.0)),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (rectangle, outline_piece),
        centerline_geometries=(centerline_piece,),
    )

    assert any(isinstance(geometry, RectGeometry) for geometry in geometries)
    assert centerline_piece not in geometries
    assert outline_piece in geometries
    assert report.rect_count == 1
    assert report.path_count == 1


def test_reconstruct_semantic_geometries_replaces_outline_when_centerline_has_closed_paths() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(50.0, 20.0),
            Point(90.0, 20.0),
            Point(85.0, 48.0),
            Point(70.0, 68.0),
            Point(52.0, 50.0),
        ),
        closed=True,
    )
    centerline_piece = PathGeometry(
        points=(
            Point(50.0, 40.0),
            Point(70.0, 20.0),
            Point(90.0, 40.0),
            Point(70.0, 60.0),
        ),
        closed=True,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(centerline_piece,),
    )

    assert centerline_piece in geometries
    assert outline_piece not in geometries
    assert report.path_count == 1
    assert report.centerline_replacement_applied is True
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_reference_path_count == 1
    assert report.centerline_missing_reference_count == 0
    assert report.centerline_piece_diagnostics[0].matched is True
    assert report.centerline_piece_diagnostics[0].source is not None


def test_reconstruct_semantic_geometries_filters_local_centerline_loops() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(100.0, 0.0),
            Point(86.0, 50.0),
            Point(50.0, 86.0),
            Point(5.0, 54.0),
        ),
        closed=True,
    )
    local_loop = PathGeometry(
        points=(
            Point(10.0, 10.0),
            Point(20.0, 10.0),
            Point(20.0, 20.0),
            Point(10.0, 20.0),
        ),
        closed=True,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(local_loop,),
    )

    assert outline_piece in geometries
    assert local_loop not in geometries
    assert report.centerline_closed_candidate_count == 1
    assert report.centerline_piece_candidate_count == 0
    assert report.centerline_replacement_applied is False
    assert report.centerline_reference_path_count == 1
    assert report.centerline_missing_reference_count == 1
    assert report.centerline_piece_diagnostics[0].matched is False
    assert report.centerline_piece_diagnostics[0].source is None


def test_reconstruct_semantic_geometries_merges_local_open_centerline_branches_per_piece() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(100.0, 0.0),
            Point(92.0, 68.0),
            Point(48.0, 84.0),
            Point(0.0, 60.0),
        ),
        closed=True,
    )
    branch_a = PathGeometry(
        points=(Point(10.0, 10.0), Point(70.0, 10.0), Point(90.0, 40.0)),
        closed=False,
    )
    branch_b = PathGeometry(
        points=(Point(90.0, 40.0), Point(70.0, 70.0), Point(10.0, 70.0)),
        closed=False,
    )
    branch_c = PathGeometry(
        points=(Point(10.0, 70.0), Point(10.0, 10.0)),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(branch_a, branch_b, branch_c),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    assert len(piece_paths) == 1
    assert piece_paths[0].closed is True
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_replacement_applied is True


def test_reconstruct_semantic_geometries_can_close_open_centerline_with_outline_guidance() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(80.0, 0.0),
            Point(100.0, 40.0),
            Point(70.0, 90.0),
            Point(10.0, 80.0),
        ),
        closed=True,
    )
    centerline_piece = PathGeometry(
        points=(
            Point(2.0, 2.0),
            Point(78.0, 2.0),
            Point(96.0, 40.0),
            Point(68.0, 86.0),
            Point(16.0, 78.0),
        ),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(centerline_piece,),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    assert len(piece_paths) == 1
    assert piece_paths[0].closed is True
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_replacement_applied is True


def test_reconstruct_semantic_geometries_aggregates_slender_open_branches_into_matched_candidate() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(65.0, -1.2),
            Point(135.0, -1.7),
            Point(220.0, -0.8),
            Point(260.0, 0.0),
            Point(260.0, 3.4),
            Point(220.0, 4.2),
            Point(135.0, 5.1),
            Point(65.0, 4.7),
            Point(0.0, 3.4),
        ),
        closed=True,
    )
    upper_left = PathGeometry(
        points=(Point(0.4, 0.1), Point(58.0, -1.0)),
        closed=False,
    )
    upper_middle = PathGeometry(
        points=(Point(74.0, -1.3), Point(130.0, -1.6), Point(188.0, -1.2)),
        closed=False,
    )
    upper_right_and_tip = PathGeometry(
        points=(Point(205.0, -0.8), Point(258.5, 0.1), Point(258.5, 3.3)),
        closed=False,
    )
    lower_right = PathGeometry(
        points=(Point(246.0, 3.7), Point(185.0, 4.7), Point(125.0, 5.0)),
        closed=False,
    )
    lower_left = PathGeometry(
        points=(Point(108.0, 4.9), Point(50.0, 4.4), Point(0.4, 3.3)),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(
            upper_left,
            upper_middle,
            upper_right_and_tip,
            lower_right,
            lower_left,
        ),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    diagnostic = report.centerline_piece_diagnostics[0]
    assert outline_piece.area_mm2 / (outline_piece.perimeter_mm * outline_piece.perimeter_mm) < 0.006
    assert len(piece_paths) == 1
    assert piece_paths[0].closed is True
    assert piece_paths[0] is diagnostic.candidate_geometry
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_missing_reference_count == 0
    assert report.centerline_replacement_applied is True
    assert diagnostic.matched is True
    assert diagnostic.source is not None
    assert diagnostic.source.startswith("reference-ordered-open")
    assert diagnostic.candidate_area_mm2 is not None
    assert diagnostic.candidate_perimeter_mm is not None


def test_reconstruct_semantic_geometries_collects_disconnected_long_arc_branches() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(120.0, 10.0),
            Point(240.0, 5.0),
            Point(360.0, 20.0),
            Point(500.0, 18.0),
            Point(650.0, 9.0),
            Point(650.0, 11.0),
            Point(500.0, 20.0),
            Point(360.0, 22.0),
            Point(240.0, 7.0),
            Point(120.0, 12.0),
            Point(0.0, 2.0),
        ),
        closed=True,
    )
    upper_arc = PathGeometry(
        points=(
            Point(0.4, 0.1),
            Point(120.3, 9.8),
            Point(239.7, 5.2),
        ),
        closed=False,
    )
    tip_arc = PathGeometry(
        points=(
            Point(240.2, 5.0),
            Point(360.2, 20.1),
            Point(499.8, 18.1),
            Point(649.6, 9.1),
            Point(649.7, 10.9),
        ),
        closed=False,
    )
    lower_arc = PathGeometry(
        points=(
            Point(500.2, 19.9),
            Point(360.1, 21.8),
            Point(240.1, 7.1),
            Point(119.8, 12.1),
            Point(0.2, 1.9),
        ),
        closed=False,
    )
    interior_noise = PathGeometry(
        points=(Point(250.0, 12.0), Point(280.0, 14.0), Point(320.0, 13.0)),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(upper_arc, tip_arc, lower_arc, interior_noise),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    diagnostic = report.centerline_piece_diagnostics[0]
    assert outline_piece.area_mm2 / (outline_piece.perimeter_mm * outline_piece.perimeter_mm) < 0.001
    assert len(piece_paths) == 1
    assert piece_paths[0].closed is True
    assert piece_paths[0] is diagnostic.candidate_geometry
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_missing_reference_count == 0
    assert report.centerline_replacement_applied is True
    assert diagnostic.matched is True
    assert diagnostic.source in {"reference-near-open", "slender-reference-near-fill"}


def test_reconstruct_semantic_geometries_fills_long_arc_branch_gap_from_outline() -> None:
    outline_points = (
        Point(0.0, 0.0),
        Point(55.0, 1.5),
        Point(110.0, 3.0),
        Point(165.0, 4.5),
        Point(220.0, 16.0),
        Point(275.0, 29.5),
        Point(330.0, 36.0),
        Point(385.0, 29.5),
        Point(440.0, 16.0),
        Point(495.0, 13.5),
        Point(550.0, 15.0),
        Point(605.0, 16.5),
        Point(660.0, 18.0),
        Point(715.0, 19.5),
        Point(770.0, 21.0),
        Point(825.0, 22.5),
        Point(825.0, 24.0),
        Point(770.0, 22.5),
        Point(715.0, 21.0),
        Point(660.0, 19.5),
        Point(605.0, 18.0),
        Point(550.0, 16.5),
        Point(495.0, 15.0),
        Point(440.0, 17.5),
        Point(385.0, 31.0),
        Point(330.0, 37.5),
        Point(275.0, 31.0),
        Point(220.0, 17.5),
        Point(165.0, 6.0),
        Point(110.0, 4.5),
        Point(55.0, 3.0),
        Point(0.0, 1.5),
    )
    outline_piece = PathGeometry(points=outline_points, closed=True)
    start_branch = PathGeometry(
        points=(outline_points[0], outline_points[1], outline_points[2], outline_points[3]),
        closed=False,
    )
    middle_branch = PathGeometry(
        points=(outline_points[9], outline_points[10], outline_points[11], outline_points[12]),
        closed=False,
    )
    tip_branch = PathGeometry(
        points=(outline_points[13], outline_points[14], outline_points[15], outline_points[16]),
        closed=False,
    )
    lower_branch = PathGeometry(
        points=(outline_points[17], outline_points[18], outline_points[19], outline_points[20]),
        closed=False,
    )
    lower_start = PathGeometry(
        points=(outline_points[27], outline_points[28], outline_points[29], outline_points[30], outline_points[31]),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(start_branch, middle_branch, tip_branch, lower_branch, lower_start),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    diagnostic = report.centerline_piece_diagnostics[0]
    assert outline_piece.area_mm2 / (outline_piece.perimeter_mm * outline_piece.perimeter_mm) < 0.001
    assert len(piece_paths) == 1
    assert piece_paths[0].closed is True
    assert piece_paths[0] is diagnostic.candidate_geometry
    assert len(piece_paths[0].points) > sum(
        len(path.points)
        for path in (start_branch, middle_branch, tip_branch, lower_branch, lower_start)
    )
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_missing_reference_count == 0
    assert report.centerline_replacement_applied is True
    assert diagnostic.matched is True
    assert diagnostic.source in {"reference-near-open", "slender-reference-near-fill"}


def test_reconstruct_semantic_geometries_fills_slender_reference_near_gaps() -> None:
    outline_points = (
        Point(0.0, 0.0),
        Point(35.0, 5.0),
        Point(70.0, 18.0),
        Point(100.0, 36.0),
        Point(130.0, 60.0),
        Point(158.0, 90.0),
        Point(157.6, 90.5),
        Point(129.6, 60.5),
        Point(99.6, 36.5),
        Point(69.6, 18.5),
        Point(34.6, 5.5),
        Point(0.0, 0.5),
    )
    outline_piece = PathGeometry(points=outline_points, closed=True)
    upper = PathGeometry(
        points=(outline_points[0], outline_points[1], outline_points[2], outline_points[3]),
        closed=False,
    )
    middle = PathGeometry(
        points=(outline_points[4], outline_points[5], outline_points[6], outline_points[7]),
        closed=False,
    )
    lower = PathGeometry(
        points=(outline_points[8], outline_points[9], outline_points[10], outline_points[11]),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(upper, middle, lower),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    diagnostic = report.centerline_piece_diagnostics[0]
    assert outline_piece.area_mm2 / (outline_piece.perimeter_mm * outline_piece.perimeter_mm) < 0.001
    assert len(piece_paths) == 1
    assert piece_paths[0] is diagnostic.candidate_geometry
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_replacement_applied is True
    assert diagnostic.source == "slender-reference-near-fill"


def test_reconstruct_semantic_geometries_fills_compact_reference_near_gaps() -> None:
    outline_points = (
        Point(0.0, 0.0),
        Point(24.0, 1.0),
        Point(43.0, 10.0),
        Point(48.0, 25.0),
        Point(39.0, 41.0),
        Point(20.0, 50.0),
        Point(3.0, 42.0),
        Point(-2.0, 25.0),
        Point(7.0, 19.0),
        Point(20.0, 30.0),
        Point(33.0, 23.0),
        Point(30.0, 10.0),
        Point(12.0, 6.0),
    )
    outline_piece = PathGeometry(points=outline_points, closed=True)
    branches = (
        PathGeometry(points=outline_points[0:3], closed=False),
        PathGeometry(points=outline_points[3:6], closed=False),
        PathGeometry(points=outline_points[6:9], closed=False),
        PathGeometry(points=outline_points[9:12], closed=False),
        PathGeometry(points=(outline_points[12], outline_points[0]), closed=False),
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=branches,
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    diagnostic = report.centerline_piece_diagnostics[0]
    assert outline_piece.area_mm2 > 350.0
    assert len(piece_paths) == 1
    assert piece_paths[0].closed is True
    assert piece_paths[0] is diagnostic.candidate_geometry
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_missing_reference_count == 0
    assert report.centerline_replacement_applied is True
    assert diagnostic.source == "compact-reference-near-fill"


def test_reference_near_anchor_fill_handles_wrapped_short_gap() -> None:
    reference = PathGeometry(
        points=tuple(
            Point(float(index), 0.0 if index < 5 else 10.0)
            for index in range(10)
        ),
        closed=True,
    )
    ordered_anchor_points = [
        (8, (0.0, reference.points[8], 1)),
        (9, (0.0, reference.points[9], 1)),
        (1, (0.0, reference.points[1], 1)),
        (2, (0.0, reference.points[2], 1)),
    ]

    points = _fill_reference_near_anchor_gaps(reference, ordered_anchor_points)

    assert reference.points[0] in points


def test_large_piece_extreme_anchor_snap_repairs_bbox_edge_drift() -> None:
    reference = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(120.0, 0.0),
            Point(160.0, 40.0),
            Point(150.0, 120.0),
            Point(80.0, 150.0),
            Point(10.0, 130.0),
            Point(-10.0, 60.0),
        ),
        closed=True,
    )
    candidate = PathGeometry(
        points=(
            Point(4.0, 4.0),
            Point(116.0, 4.0),
            Point(158.0, 42.0),
            Point(146.0, 116.0),
            Point(76.0, 146.0),
            Point(13.0, 126.0),
            Point(-6.0, 64.0),
        ),
        closed=True,
    )

    snapped = _snap_large_piece_extreme_anchors(candidate, reference)

    assert _path_distance_summary(snapped, reference)[1] < _path_distance_summary(candidate, reference)[1]
    assert snapped.bounds[0] == reference.bounds[0]
    assert snapped.bounds[1] == reference.bounds[1]
    assert snapped.bounds[3] == reference.bounds[3]


def test_compact_piece_edge_anchor_snap_repairs_edge_drift() -> None:
    reference = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(30.0, 0.0),
            Point(44.0, 16.0),
            Point(38.0, 38.0),
            Point(16.0, 44.0),
            Point(0.0, 28.0),
        ),
        closed=True,
    )
    candidate = PathGeometry(
        points=(
            Point(1.4, 1.4),
            Point(28.6, 1.3),
            Point(42.5, 16.5),
            Point(37.0, 37.0),
            Point(16.4, 43.5),
            Point(1.2, 26.5),
        ),
        closed=True,
    )

    snapped = _snap_compact_piece_edge_anchors(candidate, reference)

    assert _path_distance_summary(snapped, reference)[1] < _path_distance_summary(candidate, reference)[1]
    assert snapped.bounds[0] == reference.bounds[0]
    assert snapped.bounds[1] == reference.bounds[1]


def test_reconstruct_semantic_geometries_rejects_partial_large_piece_candidate() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(200.0, 0.0),
            Point(210.0, 86.0),
            Point(145.0, 118.0),
            Point(30.0, 104.0),
        ),
        closed=True,
    )
    partial_candidate = PathGeometry(
        points=(
            Point(84.0, 2.0),
            Point(198.0, 2.0),
            Point(206.0, 84.0),
            Point(145.0, 114.0),
            Point(92.0, 102.0),
        ),
        closed=True,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(partial_candidate,),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    diagnostic = report.centerline_piece_diagnostics[0]
    assert piece_paths == [outline_piece]
    assert report.centerline_piece_candidate_count == 0
    assert report.centerline_missing_reference_count == 1
    assert report.centerline_replacement_applied is False
    assert diagnostic.matched is False


def test_centerline_piece_score_rejects_large_piece_hull_with_full_bbox_but_bad_geometry() -> None:
    reference = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(180.0, 0.0),
            Point(200.0, 90.0),
            Point(135.0, 180.0),
            Point(92.0, -40.0),
            Point(40.0, 170.0),
            Point(-5.0, 95.0),
        ),
        closed=True,
    )
    full_bbox_candidate = PathGeometry(
        points=(
            Point(-7.0, 0.0),
            Point(182.0, 0.0),
            Point(202.0, 90.0),
            Point(135.0, 181.0),
            Point(40.0, 170.0),
            Point(-7.0, 94.0),
        ),
        closed=True,
    )

    assert full_bbox_candidate.area_mm2 / reference.area_mm2 > 1.35
    assert _centerline_piece_score(full_bbox_candidate, reference) is None


def test_reconstruct_semantic_geometries_reports_best_rejected_centerline_candidate() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(180.0, 0.0),
            Point(200.0, 90.0),
            Point(135.0, 180.0),
            Point(92.0, -40.0),
            Point(40.0, 170.0),
            Point(-5.0, 95.0),
        ),
        closed=True,
    )
    bad_hull_branch_a = PathGeometry(
        points=(Point(-7.0, 0.0), Point(182.0, 0.0), Point(202.0, 90.0)),
        closed=False,
    )
    bad_hull_branch_b = PathGeometry(
        points=(Point(202.0, 90.0), Point(135.0, 181.0), Point(40.0, 170.0)),
        closed=False,
    )
    bad_hull_branch_c = PathGeometry(
        points=(Point(40.0, 170.0), Point(-7.0, 94.0), Point(-7.0, 0.0)),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(bad_hull_branch_a, bad_hull_branch_b, bad_hull_branch_c),
    )

    diagnostic = report.centerline_piece_diagnostics[0]
    assert geometries == (outline_piece,)
    assert diagnostic.matched is False
    assert diagnostic.rejected_source is not None
    assert diagnostic.rejected_reason == "area ratio is outside limits"
    assert diagnostic.rejected_candidate_bounds_mm is not None
    assert diagnostic.rejected_distance_summary_mm is not None


def test_reconstruct_semantic_geometries_keeps_more_ordered_branches_for_large_piece() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(80.0, 0.0),
            Point(160.0, 0.0),
            Point(240.0, 20.0),
            Point(280.0, 80.0),
            Point(280.0, 150.0),
            Point(235.0, 210.0),
            Point(160.0, 240.0),
            Point(80.0, 235.0),
            Point(20.0, 190.0),
            Point(-10.0, 120.0),
            Point(-5.0, 45.0),
        ),
        closed=True,
    )
    branches = (
        PathGeometry(points=(Point(0.0, 0.0), Point(76.0, 0.0)), closed=False),
        PathGeometry(points=(Point(84.0, 0.0), Point(156.0, 0.0)), closed=False),
        PathGeometry(points=(Point(164.0, 1.0), Point(236.0, 19.0)), closed=False),
        PathGeometry(points=(Point(244.0, 26.0), Point(276.0, 74.0)), closed=False),
        PathGeometry(points=(Point(280.0, 87.0), Point(280.0, 143.0)), closed=False),
        PathGeometry(points=(Point(275.8, 155.6), Point(239.2, 204.4)), closed=False),
        PathGeometry(points=(Point(228.0, 212.8), Point(167.0, 237.2)), closed=False),
        PathGeometry(points=(Point(152.0, 239.5), Point(88.0, 235.5)), closed=False),
        PathGeometry(points=(Point(73.6, 230.2), Point(26.4, 194.8)), closed=False),
        PathGeometry(points=(Point(17.2, 183.6), Point(-7.2, 126.4)), closed=False),
        PathGeometry(points=(Point(-9.5, 112.5), Point(-5.5, 52.5)), closed=False),
        PathGeometry(points=(Point(-4.5, 40.5), Point(-0.5, 4.5)), closed=False),
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=branches,
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    diagnostic = report.centerline_piece_diagnostics[0]
    assert len(piece_paths) == 1
    assert piece_paths[0] is diagnostic.candidate_geometry
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_replacement_applied is True
    assert diagnostic.source is not None
    assert diagnostic.source.startswith("reference-ordered-open")


def test_reconstruct_semantic_geometries_uses_large_piece_reference_near_ring() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(80.0, 0.0),
            Point(160.0, 0.0),
            Point(240.0, 20.0),
            Point(280.0, 80.0),
            Point(280.0, 150.0),
            Point(235.0, 210.0),
            Point(160.0, 240.0),
            Point(80.0, 235.0),
            Point(20.0, 190.0),
            Point(-10.0, 120.0),
            Point(-5.0, 45.0),
        ),
        closed=True,
    )
    branches = (
        PathGeometry(points=(Point(0.5, 0.2), Point(82.0, 0.3)), closed=False),
        PathGeometry(points=(Point(159.0, 0.4), Point(238.0, 20.8)), closed=False),
        PathGeometry(points=(Point(279.2, 80.0), Point(279.4, 150.0)), closed=False),
        PathGeometry(points=(Point(234.0, 209.0), Point(160.5, 239.2)), closed=False),
        PathGeometry(points=(Point(79.4, 234.2), Point(20.4, 189.0)), closed=False),
        PathGeometry(points=(Point(-9.2, 119.0), Point(-4.5, 45.5), Point(0.5, 0.2)), closed=False),
        PathGeometry(points=(Point(80.0, 80.0), Point(180.0, 120.0)), closed=False),
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=branches,
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    diagnostic = report.centerline_piece_diagnostics[0]
    assert len(piece_paths) == 1
    assert piece_paths[0] is diagnostic.candidate_geometry
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_replacement_applied is True
    assert diagnostic.source in {"large-piece-reference-near", "reference-ordered-open"}


def test_reconstruct_semantic_geometries_component_candidate_can_replace_outline() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(120.0, 0.0),
            Point(112.0, 78.0),
            Point(36.0, 90.0),
            Point(0.0, 62.0),
        ),
        closed=True,
    )
    branch_a = PathGeometry(
        points=(Point(2.0, 2.0), Point(118.0, 2.0), Point(118.0, 30.0)),
        closed=False,
    )
    branch_b = PathGeometry(
        points=(Point(118.0, 30.0), Point(118.0, 78.0), Point(70.0, 78.0)),
        closed=False,
    )
    branch_c = PathGeometry(
        points=(Point(70.0, 78.0), Point(2.0, 78.0), Point(2.0, 40.0)),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(branch_a, branch_b, branch_c),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    assert len(piece_paths) == 1
    assert piece_paths[0].closed is True
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_replacement_applied is True


def test_reconstruct_semantic_geometries_matches_slender_open_branch_piece() -> None:
    outline_piece = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(70.0, 0.0),
            Point(70.0, 1.0),
            Point(36.0, 5.0),
            Point(0.0, 1.0),
        ),
        closed=True,
    )
    branch_a = PathGeometry(
        points=(Point(1.0, 0.5), Point(24.0, 0.5), Point(35.0, 4.3)),
        closed=False,
    )
    branch_b = PathGeometry(
        points=(Point(35.0, 4.3), Point(48.0, 0.5), Point(69.0, 0.5)),
        closed=False,
    )
    branch_c = PathGeometry(
        points=(Point(69.0, 0.5), Point(36.0, 4.7), Point(1.0, 0.5)),
        closed=False,
    )

    geometries, report = reconstruct_semantic_geometries(
        (outline_piece,),
        centerline_geometries=(branch_a, branch_b, branch_c),
    )

    piece_paths = [geometry for geometry in geometries if isinstance(geometry, PathGeometry)]
    assert len(piece_paths) == 1
    assert piece_paths[0].closed is True
    assert piece_paths[0] != outline_piece
    assert report.centerline_piece_candidate_count == 1
    assert report.centerline_replacement_applied is True
    assert report.centerline_piece_diagnostics[0].matched is True
