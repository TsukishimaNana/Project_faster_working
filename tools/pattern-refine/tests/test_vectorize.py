from pathlib import Path

import numpy as np

from pattern_refine.geometry import PathGeometry, Point
from pattern_refine.vectorize import (
    parse_cleaned_svg,
    parse_svg_d,
    path_to_curve_svg_d,
    path_to_svg_d,
    vectorize_lines,
    vectorize_lines_to_svg,
)


def test_path_to_svg_d_round_trips_simple_closed_path() -> None:
    geometry = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(10.0, 0.0),
            Point(10.0, 10.0),
        ),
        closed=True,
    )

    parsed = parse_svg_d(path_to_svg_d(geometry))

    assert parsed.closed is True
    assert parsed.points == geometry.points


def test_path_to_curve_svg_d_uses_cubic_commands() -> None:
    geometry = PathGeometry(
        points=(
            Point(0.0, 0.0),
            Point(10.0, 0.0),
            Point(20.0, 5.0),
            Point(30.0, 0.0),
            Point(40.0, 0.0),
        ),
        closed=False,
    )

    d = path_to_curve_svg_d(geometry)

    assert d.startswith("M 0.000000 0.000000 C ")
    assert " 40.000000 0.000000" in d


def test_vectorize_lines_to_svg_writes_mm_based_paths(tmp_path: Path) -> None:
    image = np.full((100, 100), 255, dtype=np.uint8)
    image[20:80, 20] = 0
    image[20:80, 80] = 0
    image[20, 20:81] = 0
    image[80, 20:81] = 0
    image[10:12, 10:12] = 0
    svg_path = tmp_path / "sample.cleaned.svg"

    geometries = vectorize_lines_to_svg(
        image,
        svg_path,
        page_width_mm=25.4,
        page_height_mm=25.4,
        dpi=100,
    )
    parsed = parse_cleaned_svg(svg_path)

    assert svg_path.exists()
    assert len(geometries) == 1
    assert parsed == geometries
    assert geometries[0].closed is True
    assert len(geometries[0].points) >= 4


def test_vectorize_lines_can_disable_contour_approximation() -> None:
    image = np.full((100, 100), 255, dtype=np.uint8)
    image[20:80, 20] = 0
    image[20:80, 80] = 0
    image[20, 20:81] = 0
    image[80, 20:81] = 0

    approximated = vectorize_lines(
        image,
        page_width_mm=25.4,
        page_height_mm=25.4,
        dpi=100,
        approximation="default",
    )
    unapproximated = vectorize_lines(
        image,
        page_width_mm=25.4,
        page_height_mm=25.4,
        dpi=100,
        approximation="none",
    )

    assert len(unapproximated) == len(approximated)
    assert len(unapproximated[0].points) >= len(approximated[0].points)
