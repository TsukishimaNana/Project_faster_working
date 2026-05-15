import pytest

from pattern_refine.geometry import LineGeometry, PathGeometry, Point, RectGeometry
from pattern_refine.orientation import PageCoordinateTransform, transform_geometry, transform_path_geometry


def test_page_coordinate_transform_maps_rotation_270_to_portrait_page() -> None:
    transform = PageCoordinateTransform(
        rotation=270,
        render_width_mm=420.0,
        render_height_mm=297.0,
        page_width_mm=297.0,
        page_height_mm=420.0,
    )

    _assert_point_close(transform.point_from_render(Point(0.0, 0.0)), Point(297.0, 0.0))
    _assert_point_close(transform.point_from_render(Point(420.0, 0.0)), Point(297.0, 420.0))
    _assert_point_close(transform.point_from_render(Point(0.0, 297.0)), Point(0.0, 0.0))
    _assert_point_close(transform.point_from_render(Point(420.0, 297.0)), Point(0.0, 420.0))


def test_transform_path_geometry_preserves_closed_state() -> None:
    transform = PageCoordinateTransform(
        rotation=270,
        render_width_mm=40.0,
        render_height_mm=20.0,
        page_width_mm=20.0,
        page_height_mm=40.0,
    )
    geometry = PathGeometry(
        points=(Point(5.0, 4.0), Point(15.0, 4.0), Point(15.0, 10.0)),
        closed=True,
    )

    transformed = transform_path_geometry(geometry, transform)

    assert transformed.closed is True
    _assert_point_close(transformed.points[0], Point(16.0, 5.0))
    _assert_point_close(transformed.points[1], Point(16.0, 15.0))


def test_transform_geometry_handles_lines_and_rects() -> None:
    transform = PageCoordinateTransform(
        rotation=0,
        render_width_mm=100.0,
        render_height_mm=200.0,
        page_width_mm=50.0,
        page_height_mm=100.0,
    )

    line = transform_geometry(LineGeometry(Point(10.0, 20.0), Point(30.0, 40.0)), transform)
    rect = transform_geometry(RectGeometry(10.0, 20.0, 30.0, 40.0), transform)

    assert isinstance(line, LineGeometry)
    _assert_point_close(line.start, Point(5.0, 10.0))
    _assert_point_close(line.end, Point(15.0, 20.0))
    assert isinstance(rect, RectGeometry)
    assert rect.x_mm == pytest.approx(5.0)
    assert rect.y_mm == pytest.approx(10.0)
    assert rect.width_mm == pytest.approx(15.0)
    assert rect.height_mm == pytest.approx(20.0)


def _assert_point_close(actual: Point, expected: Point) -> None:
    assert actual.x_mm == pytest.approx(expected.x_mm)
    assert actual.y_mm == pytest.approx(expected.y_mm)
