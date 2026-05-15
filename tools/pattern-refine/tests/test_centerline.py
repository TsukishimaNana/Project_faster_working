import numpy as np
import pytest

from pattern_refine.centerline import (
    build_centerline_report,
    reconstruct_centerline_paths,
    reconstruct_centerline_paths_for_regions,
    reconstruct_centerline_paths_with_report,
    write_centerline_report,
)
from pattern_refine.geometry import PathGeometry, Point


def test_reconstruct_centerline_paths_collapses_thick_line_to_single_stroke() -> None:
    image = np.full((80, 140), 255, dtype=np.uint8)
    image[38:43, 20:121] = 0

    paths = reconstruct_centerline_paths(
        image,
        page_width_mm=140.0,
        page_height_mm=80.0,
        dpi=100,
        min_path_length_mm=30.0,
    )

    assert len(paths) == 1
    path = paths[0]
    assert path.closed is False
    assert path.perimeter_mm == pytest.approx(100.0, abs=6.0)
    assert max(point.y_mm for point in path.points) - min(point.y_mm for point in path.points) <= 2.0


def test_reconstruct_centerline_paths_collapses_rectangular_ink_outline() -> None:
    image = np.full((120, 120), 255, dtype=np.uint8)
    image[20:25, 20:101] = 0
    image[95:100, 20:101] = 0
    image[20:100, 20:25] = 0
    image[20:100, 95:100] = 0

    paths = reconstruct_centerline_paths(
        image,
        page_width_mm=120.0,
        page_height_mm=120.0,
        dpi=100,
        min_path_length_mm=30.0,
    )

    assert paths
    assert sum(path.perimeter_mm for path in paths) == pytest.approx(300.0, abs=35.0)
    assert all(path.perimeter_mm >= 30.0 for path in paths)


def test_reconstruct_centerline_paths_stitches_small_collinear_gap() -> None:
    image = np.full((80, 160), 255, dtype=np.uint8)
    image[38:43, 20:70] = 0
    image[38:43, 76:121] = 0

    paths = reconstruct_centerline_paths(
        image,
        page_width_mm=160.0,
        page_height_mm=80.0,
        dpi=100,
        min_path_length_mm=20.0,
        stitch_gap_mm=12.0,
    )

    assert len(paths) == 1
    assert paths[0].perimeter_mm == pytest.approx(100.0, abs=8.0)


def test_reconstruct_centerline_paths_with_report_counts_stitched_paths() -> None:
    image = np.full((80, 160), 255, dtype=np.uint8)
    image[38:43, 20:70] = 0
    image[38:43, 76:121] = 0

    paths, report = reconstruct_centerline_paths_with_report(
        image,
        page_width_mm=160.0,
        page_height_mm=80.0,
        dpi=100,
        min_path_length_mm=20.0,
        stitch_gap_mm=12.0,
    )

    assert len(paths) == 1
    assert report.path_count == 1
    assert report.stitched_path_count_delta == 1
    assert report.longest_path_mm == pytest.approx(paths[0].perimeter_mm)


def test_reconstruct_centerline_paths_does_not_stitch_large_gap() -> None:
    image = np.full((80, 180), 255, dtype=np.uint8)
    image[38:43, 20:70] = 0
    image[38:43, 100:151] = 0

    paths = reconstruct_centerline_paths(
        image,
        page_width_mm=180.0,
        page_height_mm=80.0,
        dpi=100,
        min_path_length_mm=20.0,
        stitch_gap_mm=4.0,
    )

    assert len(paths) == 2


def test_reconstruct_centerline_paths_prunes_short_terminal_spur() -> None:
    image = np.full((80, 140), 255, dtype=np.uint8)
    image[38:43, 20:121] = 0
    image[34:39, 70:75] = 0

    paths, report = reconstruct_centerline_paths_with_report(
        image,
        page_width_mm=140.0,
        page_height_mm=80.0,
        dpi=100,
        min_path_length_mm=30.0,
        prune_spur_length_mm=8.0,
    )

    assert len(paths) == 1
    assert report.pruned_spur_count >= 1
    assert report.pruned_spur_length_mm > 0
    path = paths[0]
    assert max(point.y_mm for point in path.points) - min(point.y_mm for point in path.points) <= 2.0


def test_reconstruct_centerline_paths_keeps_independent_short_mark() -> None:
    image = np.full((80, 140), 255, dtype=np.uint8)
    image[38:43, 20:121] = 0
    image[58:63, 70:86] = 0

    paths, report = reconstruct_centerline_paths_with_report(
        image,
        page_width_mm=140.0,
        page_height_mm=80.0,
        dpi=100,
        min_path_length_mm=8.0,
        prune_spur_length_mm=8.0,
    )

    assert len(paths) == 2
    assert report.pruned_spur_count == 0
    assert report.skeleton_endpoint_count >= 4


def test_write_centerline_report(tmp_path) -> None:
    image = np.full((80, 140), 255, dtype=np.uint8)
    image[38:43, 20:121] = 0
    paths = reconstruct_centerline_paths(
        image,
        page_width_mm=140.0,
        page_height_mm=80.0,
        dpi=100,
        min_path_length_mm=30.0,
    )
    report = build_centerline_report(paths)
    report_path = tmp_path / "centerline-report.json"

    write_centerline_report(report, report_path)

    text = report_path.read_text(encoding="utf-8")
    assert '"path_count": 1' in text
    assert '"closed_path_count": 0' in text
    assert '"skeleton_endpoint_count": 0' in text


def test_reconstruct_centerline_paths_for_regions_limits_paths_to_piece_bbox() -> None:
    image = np.full((120, 220), 255, dtype=np.uint8)
    image[20:25, 20:101] = 0
    image[95:100, 20:101] = 0
    image[20:100, 20:25] = 0
    image[20:100, 95:100] = 0
    image[20:25, 140:201] = 0
    image[95:100, 140:201] = 0
    image[20:100, 140:145] = 0
    image[20:100, 195:200] = 0
    region = PathGeometry(
        points=(
            Point(10.0, 10.0),
            Point(110.0, 10.0),
            Point(110.0, 110.0),
            Point(10.0, 110.0),
        ),
        closed=True,
    )

    paths = reconstruct_centerline_paths_for_regions(
        image,
        (region,),
        page_width_mm=220.0,
        page_height_mm=120.0,
        dpi=100,
        min_path_length_mm=30.0,
    )

    assert paths
    assert all(path.bounds[2] <= 120.0 for path in paths)


def test_reconstruct_centerline_paths_for_regions_masks_outside_neighboring_piece() -> None:
    image = np.full((120, 220), 255, dtype=np.uint8)
    image[20:25, 20:101] = 0
    image[95:100, 20:101] = 0
    image[20:100, 20:25] = 0
    image[20:100, 95:100] = 0
    image[20:25, 140:201] = 0
    image[95:100, 140:201] = 0
    image[20:100, 140:145] = 0
    image[20:100, 195:200] = 0
    left_region = PathGeometry(
        points=(
            Point(10.0, 10.0),
            Point(110.0, 10.0),
            Point(110.0, 110.0),
            Point(10.0, 110.0),
        ),
        closed=True,
    )

    paths = reconstruct_centerline_paths_for_regions(
        image,
        (left_region,),
        page_width_mm=220.0,
        page_height_mm=120.0,
        dpi=100,
        min_path_length_mm=30.0,
    )

    assert paths
    assert all(path.bounds[0] < 120.0 for path in paths)
    assert all(path.bounds[2] < 120.0 for path in paths)
