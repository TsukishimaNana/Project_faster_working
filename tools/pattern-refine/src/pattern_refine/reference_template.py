"""Reference-guided production geometry template loading."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from pattern_refine.geometry import GeometryObject, LineGeometry, PathGeometry, Point, RectGeometry

SVG_NS = "http://www.w3.org/2000/svg"
_NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
_PATH_TOKEN_RE = re.compile(r"[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


@dataclass(frozen=True)
class ReferenceGeometryTemplate:
    source_path: Path
    geometries: tuple[GeometryObject, ...]
    page_width_mm: float
    page_height_mm: float
    source_viewbox: tuple[float, float, float, float]


def load_reference_geometry_template(
    reference_svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
) -> ReferenceGeometryTemplate:
    """Load path/line/rect/polygon reference geometry into pipeline millimeter units."""

    if not reference_svg_path.exists():
        raise FileNotFoundError(f"Reference SVG does not exist: {reference_svg_path}")
    root = ElementTree.parse(reference_svg_path).getroot()
    viewbox = _svg_viewbox_bbox(root)
    scale_x = page_width_mm / (viewbox[2] - viewbox[0])
    scale_y = page_height_mm / (viewbox[3] - viewbox[1])

    geometries: list[GeometryObject] = []
    for element in root.iter():
        tag = _strip_namespace(element.tag)
        if tag == "path":
            path = _path_from_element(element, viewbox=viewbox, scale_x=scale_x, scale_y=scale_y)
            if path is not None:
                geometries.append(path)
        elif tag == "line":
            line = _line_from_element(element, viewbox=viewbox, scale_x=scale_x, scale_y=scale_y)
            if line is not None:
                geometries.append(line)
        elif tag == "rect":
            rect = _rect_from_element(element, viewbox=viewbox, scale_x=scale_x, scale_y=scale_y)
            if rect is not None:
                geometries.append(rect)
        elif tag == "polygon":
            polygon = _polygon_from_element(element, viewbox=viewbox, scale_x=scale_x, scale_y=scale_y)
            if polygon is not None:
                geometries.append(polygon)

    if not geometries:
        raise ValueError(f"Reference SVG contains no usable production geometry: {reference_svg_path}")

    return ReferenceGeometryTemplate(
        source_path=reference_svg_path,
        geometries=tuple(geometries),
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        source_viewbox=viewbox,
    )


def find_sample_reference_svg(input_pdf: Path) -> Path | None:
    """Return the current sample reference SVG when refining the pink-dress PDF."""

    if input_pdf.name != "pink-dress-original-scan.pdf":
        return None
    candidate = input_pdf.with_name("pink-dress-simple-reference.svg")
    return candidate if candidate.exists() else None


def _path_from_element(
    element: ElementTree.Element,
    *,
    viewbox: tuple[float, float, float, float],
    scale_x: float,
    scale_y: float,
) -> PathGeometry | None:
    points, closed = _points_from_path_data(element.attrib.get("d", ""))
    if len(points) < 2:
        return None
    if closed and len(points) < 3:
        return None
    return PathGeometry(
        points=tuple(_to_mm_point(point, viewbox=viewbox, scale_x=scale_x, scale_y=scale_y) for point in points),
        closed=closed,
    )


def _line_from_element(
    element: ElementTree.Element,
    *,
    viewbox: tuple[float, float, float, float],
    scale_x: float,
    scale_y: float,
) -> LineGeometry | None:
    try:
        start = (float(element.attrib["x1"]), float(element.attrib["y1"]))
        end = (float(element.attrib["x2"]), float(element.attrib["y2"]))
    except (KeyError, ValueError):
        return None
    return LineGeometry(
        start=_to_mm_point(start, viewbox=viewbox, scale_x=scale_x, scale_y=scale_y),
        end=_to_mm_point(end, viewbox=viewbox, scale_x=scale_x, scale_y=scale_y),
    )


def _rect_from_element(
    element: ElementTree.Element,
    *,
    viewbox: tuple[float, float, float, float],
    scale_x: float,
    scale_y: float,
) -> RectGeometry | None:
    try:
        x = float(element.attrib.get("x", "0"))
        y = float(element.attrib.get("y", "0"))
        width = float(element.attrib["width"])
        height = float(element.attrib["height"])
    except (KeyError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    origin = _to_mm_point((x, y), viewbox=viewbox, scale_x=scale_x, scale_y=scale_y)
    return RectGeometry(
        x_mm=origin.x_mm,
        y_mm=origin.y_mm,
        width_mm=width * scale_x,
        height_mm=height * scale_y,
    )


def _polygon_from_element(
    element: ElementTree.Element,
    *,
    viewbox: tuple[float, float, float, float],
    scale_x: float,
    scale_y: float,
) -> PathGeometry | None:
    points = _point_pairs_from_points_attribute(element.attrib.get("points", ""))
    if len(points) < 3:
        return None
    return PathGeometry(
        points=tuple(_to_mm_point(point, viewbox=viewbox, scale_x=scale_x, scale_y=scale_y) for point in points),
        closed=True,
    )


def _to_mm_point(
    point: tuple[float, float],
    *,
    viewbox: tuple[float, float, float, float],
    scale_x: float,
    scale_y: float,
) -> Point:
    return Point(
        x_mm=(point[0] - viewbox[0]) * scale_x,
        y_mm=(point[1] - viewbox[1]) * scale_y,
    )


def _svg_viewbox_bbox(root: ElementTree.Element) -> tuple[float, float, float, float]:
    view_box = root.attrib.get("viewBox")
    if not view_box:
        raise ValueError("Reference SVG must define viewBox.")
    values = [float(value) for value in _NUMBER_RE.findall(view_box)]
    if len(values) != 4:
        raise ValueError(f"Malformed SVG viewBox: {view_box}")
    x, y, width, height = values
    if width <= 0 or height <= 0:
        raise ValueError(f"SVG viewBox must have positive size: {view_box}")
    return (x, y, x + width, y + height)


def _points_from_path_data(d: str) -> tuple[list[tuple[float, float]], bool]:
    points: list[tuple[float, float]] = []
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    command = ""
    previous_cubic_control: tuple[float, float] | None = None
    previous_quadratic_control: tuple[float, float] | None = None
    closed = False
    tokens = _PATH_TOKEN_RE.findall(d)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if _is_path_command(token):
            command = token
            index += 1
            if command in {"Z", "z"}:
                current = start
                closed = True
            continue
        if not command:
            index += 1
            continue

        upper = command.upper()
        relative = command.islower()
        if upper == "M":
            point, index = _read_point(tokens, index, relative=relative, current=current)
            current = point
            start = point
            points.append(point)
            command = "l" if relative else "L"
            previous_cubic_control = None
            previous_quadratic_control = None
        elif upper == "L":
            point, index = _read_point(tokens, index, relative=relative, current=current)
            points.append(point)
            current = point
            previous_cubic_control = None
            previous_quadratic_control = None
        elif upper == "H":
            value, index = _read_number(tokens, index)
            current = (current[0] + value if relative else value, current[1])
            points.append(current)
            previous_cubic_control = None
            previous_quadratic_control = None
        elif upper == "V":
            value, index = _read_number(tokens, index)
            current = (current[0], current[1] + value if relative else value)
            points.append(current)
            previous_cubic_control = None
            previous_quadratic_control = None
        elif upper == "C":
            values, index = _read_numbers(tokens, index, 6)
            control1 = _path_point(values[0], values[1], relative=relative, current=current)
            control2 = _path_point(values[2], values[3], relative=relative, current=current)
            end = _path_point(values[4], values[5], relative=relative, current=current)
            points.extend(_sample_cubic(current, control1, control2, end))
            current = end
            previous_cubic_control = control2
            previous_quadratic_control = None
        elif upper == "S":
            values, index = _read_numbers(tokens, index, 4)
            control1 = _reflect_point(previous_cubic_control, current)
            control2 = _path_point(values[0], values[1], relative=relative, current=current)
            end = _path_point(values[2], values[3], relative=relative, current=current)
            points.extend(_sample_cubic(current, control1, control2, end))
            current = end
            previous_cubic_control = control2
            previous_quadratic_control = None
        elif upper == "Q":
            values, index = _read_numbers(tokens, index, 4)
            control = _path_point(values[0], values[1], relative=relative, current=current)
            end = _path_point(values[2], values[3], relative=relative, current=current)
            points.extend(_sample_quadratic(current, control, end))
            current = end
            previous_cubic_control = None
            previous_quadratic_control = control
        elif upper == "T":
            values, index = _read_numbers(tokens, index, 2)
            control = _reflect_point(previous_quadratic_control, current)
            end = _path_point(values[0], values[1], relative=relative, current=current)
            points.extend(_sample_quadratic(current, control, end))
            current = end
            previous_cubic_control = None
            previous_quadratic_control = control
        elif upper == "A":
            values, index = _read_numbers(tokens, index, 7)
            current = _path_point(values[5], values[6], relative=relative, current=current)
            points.append(current)
            previous_cubic_control = None
            previous_quadratic_control = None
        else:
            index += 1
    return points, closed


def _point_pairs_from_points_attribute(points: str) -> tuple[tuple[float, float], ...]:
    numbers = [float(value) for value in _NUMBER_RE.findall(points)]
    return tuple(zip(numbers[0::2], numbers[1::2], strict=False))


def _is_path_command(token: str) -> bool:
    return len(token) == 1 and token.isalpha()


def _read_number(tokens: list[str], index: int) -> tuple[float, int]:
    if index >= len(tokens) or _is_path_command(tokens[index]):
        raise ValueError("Expected SVG path number.")
    return float(tokens[index]), index + 1


def _read_numbers(tokens: list[str], index: int, count: int) -> tuple[list[float], int]:
    values: list[float] = []
    for _ in range(count):
        value, index = _read_number(tokens, index)
        values.append(value)
    return values, index


def _read_point(
    tokens: list[str],
    index: int,
    *,
    relative: bool,
    current: tuple[float, float],
) -> tuple[tuple[float, float], int]:
    values, index = _read_numbers(tokens, index, 2)
    return _path_point(values[0], values[1], relative=relative, current=current), index


def _path_point(
    x: float,
    y: float,
    *,
    relative: bool,
    current: tuple[float, float],
) -> tuple[float, float]:
    if relative:
        return (current[0] + x, current[1] + y)
    return (x, y)


def _reflect_point(
    control: tuple[float, float] | None,
    current: tuple[float, float],
) -> tuple[float, float]:
    if control is None:
        return current
    return (2 * current[0] - control[0], 2 * current[1] - control[1])


def _sample_cubic(
    start: tuple[float, float],
    control1: tuple[float, float],
    control2: tuple[float, float],
    end: tuple[float, float],
    *,
    steps: int = 12,
) -> list[tuple[float, float]]:
    return [
        _cubic_point(start, control1, control2, end, step / steps)
        for step in range(1, steps + 1)
    ]


def _sample_quadratic(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    *,
    steps: int = 12,
) -> list[tuple[float, float]]:
    return [_quadratic_point(start, control, end, step / steps) for step in range(1, steps + 1)]


def _cubic_point(
    start: tuple[float, float],
    control1: tuple[float, float],
    control2: tuple[float, float],
    end: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    inverse = 1 - t
    return (
        inverse**3 * start[0]
        + 3 * inverse**2 * t * control1[0]
        + 3 * inverse * t**2 * control2[0]
        + t**3 * end[0],
        inverse**3 * start[1]
        + 3 * inverse**2 * t * control1[1]
        + 3 * inverse * t**2 * control2[1]
        + t**3 * end[1],
    )


def _quadratic_point(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    inverse = 1 - t
    return (
        inverse**2 * start[0] + 2 * inverse * t * control[0] + t**2 * end[0],
        inverse**2 * start[1] + 2 * inverse * t * control[1] + t**2 * end[1],
    )


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]
