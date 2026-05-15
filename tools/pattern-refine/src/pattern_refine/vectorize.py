"""Raster linework vectorization into debug SVG and geometry."""

from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree

import cv2
import numpy as np

from pattern_refine.geometry import GeometryObject, LineGeometry, PathGeometry, Point, RectGeometry

SVG_NS = "http://www.w3.org/2000/svg"


def vectorize_lines_to_svg(
    lines_image: np.ndarray,
    svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
    dpi: int,
    min_area_px: float = 100.0,
    approximation: str = "default",
) -> list[PathGeometry]:
    """Trace major pattern-piece outline candidates and write debug SVG."""

    geometries = vectorize_lines(
        lines_image,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        dpi=dpi,
        min_area_px=min_area_px,
        approximation=approximation,
    )
    write_cleaned_svg(
        geometries,
        svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
    )
    return parse_cleaned_svg(svg_path)


def vectorize_lines(
    lines_image: np.ndarray,
    *,
    page_width_mm: float,
    page_height_mm: float,
    dpi: int,
    min_area_px: float = 100.0,
    approximation: str = "default",
) -> list[PathGeometry]:
    """Convert a black-on-white line image to object-level outline candidates."""

    if approximation not in {"default", "none"}:
        raise ValueError(f"Unsupported approximation mode: {approximation}")
    if lines_image.ndim == 3:
        gray = cv2.cvtColor(lines_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = lines_image
    _, foreground = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    foreground = _prepare_outline_foreground(foreground, dpi=dpi)
    contours, _ = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pixel_to_mm = 25.4 / dpi
    geometries: list[PathGeometry] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area_px:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        if width < 10 or height < 10:
            continue
        if approximation == "none":
            approximated = contour
        else:
            epsilon = max(1.0, cv2.arcLength(contour, True) * 0.003)
            approximated = cv2.approxPolyDP(contour, epsilon, True)
        points = tuple(
            Point(x_mm=float(point[0][0]) * pixel_to_mm, y_mm=float(point[0][1]) * pixel_to_mm)
            for point in approximated
        )
        if len(points) >= 3:
            geometries.append(PathGeometry(points=points, closed=True))

    return sorted(geometries, key=lambda path: _path_area(path), reverse=True)


def write_cleaned_svg(
    geometries: list[GeometryObject],
    svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
    curve_paths: bool = False,
) -> None:
    """Write path geometry as a millimeter-based debug SVG."""

    svg_path.parent.mkdir(parents=True, exist_ok=True)
    ElementTree.register_namespace("", SVG_NS)
    svg = ElementTree.Element(
        f"{{{SVG_NS}}}svg",
        {
            "width": f"{page_width_mm:.6f}mm",
            "height": f"{page_height_mm:.6f}mm",
            "viewBox": f"0 0 {page_width_mm:.6f} {page_height_mm:.6f}",
            "version": "1.1",
        },
    )
    group = ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}g",
        {
            "id": "linework",
            "fill": "none",
            "stroke": "#000000",
            "stroke-width": "0.1",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
        },
    )
    path_index = 1
    line_index = 1
    rect_index = 1
    for geometry in geometries:
        if isinstance(geometry, PathGeometry):
            ElementTree.SubElement(
                group,
                f"{{{SVG_NS}}}path",
                {
                    "id": f"path-{path_index:04d}",
                    "d": path_to_curve_svg_d(geometry) if curve_paths else path_to_svg_d(geometry),
                },
            )
            path_index += 1
        elif isinstance(geometry, LineGeometry):
            ElementTree.SubElement(
                group,
                f"{{{SVG_NS}}}line",
                {
                    "id": f"line-{line_index:04d}",
                    "x1": f"{geometry.start.x_mm:.6f}",
                    "y1": f"{geometry.start.y_mm:.6f}",
                    "x2": f"{geometry.end.x_mm:.6f}",
                    "y2": f"{geometry.end.y_mm:.6f}",
                },
            )
            line_index += 1
        elif isinstance(geometry, RectGeometry):
            ElementTree.SubElement(
                group,
                f"{{{SVG_NS}}}rect",
                {
                    "id": f"rect-{rect_index:04d}",
                    "x": f"{geometry.x_mm:.6f}",
                    "y": f"{geometry.y_mm:.6f}",
                    "width": f"{geometry.width_mm:.6f}",
                    "height": f"{geometry.height_mm:.6f}",
                },
            )
            rect_index += 1
    tree = ElementTree.ElementTree(svg)
    tree.write(svg_path, encoding="utf-8", xml_declaration=True)


def parse_cleaned_svg(svg_path: Path) -> list[PathGeometry]:
    """Parse the simple path subset emitted by write_cleaned_svg."""

    root = ElementTree.parse(svg_path).getroot()
    geometries: list[PathGeometry] = []
    for path in root.findall(f".//{{{SVG_NS}}}path"):
        d = path.attrib.get("d", "")
        geometry = parse_svg_d(d)
        if not geometry.is_empty:
            geometries.append(geometry)
    return geometries


def path_to_svg_d(geometry: PathGeometry) -> str:
    if geometry.is_empty:
        return ""
    first, *rest = geometry.points
    commands = [f"M {first.x_mm:.6f} {first.y_mm:.6f}"]
    commands.extend(f"L {point.x_mm:.6f} {point.y_mm:.6f}" for point in rest)
    if geometry.closed:
        commands.append("Z")
    return " ".join(commands)


def path_to_curve_svg_d(geometry: PathGeometry) -> str:
    """Encode a path with cubic commands while protecting sharp feature points."""

    if geometry.is_empty:
        return ""
    if len(geometry.points) < 4:
        return path_to_svg_d(geometry)
    points = geometry.points
    protected = _protected_turn_indices(geometry)
    commands = [f"M {points[0].x_mm:.6f} {points[0].y_mm:.6f}"]
    segment_count = len(points) if geometry.closed else len(points) - 1
    for index in range(segment_count):
        start = points[index]
        end = points[(index + 1) % len(points)]
        if index in protected or ((index + 1) % len(points)) in protected:
            control1 = start
            control2 = end
        else:
            previous_point = points[index - 1] if index > 0 else points[0]
            next_next_index = index + 2
            if geometry.closed:
                next_next = points[next_next_index % len(points)]
            else:
                next_next = points[next_next_index] if next_next_index < len(points) else end
            control1 = Point(
                start.x_mm + (end.x_mm - previous_point.x_mm) / 6,
                start.y_mm + (end.y_mm - previous_point.y_mm) / 6,
            )
            control2 = Point(
                end.x_mm - (next_next.x_mm - start.x_mm) / 6,
                end.y_mm - (next_next.y_mm - start.y_mm) / 6,
            )
        commands.append(
            "C "
            f"{control1.x_mm:.6f} {control1.y_mm:.6f} "
            f"{control2.x_mm:.6f} {control2.y_mm:.6f} "
            f"{end.x_mm:.6f} {end.y_mm:.6f}"
        )
    if geometry.closed:
        commands.append("Z")
    return " ".join(commands)


def parse_svg_d(d: str) -> PathGeometry:
    tokens = d.replace(",", " ").split()
    points: list[Point] = []
    closed = False
    index = 0
    while index < len(tokens):
        command = tokens[index]
        if command in {"M", "L"}:
            if index + 2 >= len(tokens):
                raise ValueError(f"Malformed SVG path command: {d}")
            points.append(Point(x_mm=float(tokens[index + 1]), y_mm=float(tokens[index + 2])))
            index += 3
            continue
        if command == "Z":
            closed = True
            index += 1
            continue
        raise ValueError(f"Unsupported SVG path command: {command}")
    return PathGeometry(points=tuple(points), closed=closed)


def _path_area(path: PathGeometry) -> float:
    if len(path.points) < 3:
        return 0.0
    area = 0.0
    points = path.points
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        area += point.x_mm * next_point.y_mm - next_point.x_mm * point.y_mm
    return abs(area) / 2


def _protected_turn_indices(geometry: PathGeometry) -> set[int]:
    if len(geometry.points) < 3:
        return set()
    protected: set[int] = set()
    points = geometry.points
    indices = range(len(points)) if geometry.closed else range(1, len(points) - 1)
    for index in indices:
        previous_point = points[index - 1]
        point = points[index]
        next_point = points[(index + 1) % len(points)]
        incoming = _distance(previous_point, point)
        outgoing = _distance(point, next_point)
        if incoming < 0.5 or outgoing < 0.5:
            protected.add(index)
            continue
        angle = _turn_angle_degrees(previous_point, point, next_point)
        if 35 <= angle <= 145:
            protected.add(index)
    return protected


def _turn_angle_degrees(previous_point: Point, point: Point, next_point: Point) -> float:
    v1 = (previous_point.x_mm - point.x_mm, previous_point.y_mm - point.y_mm)
    v2 = (next_point.x_mm - point.x_mm, next_point.y_mm - point.y_mm)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])
    if mag1 == 0 or mag2 == 0:
        return 180.0
    cosine = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cosine))


def _distance(start: Point, end: Point) -> float:
    return math.hypot(end.x_mm - start.x_mm, end.y_mm - start.y_mm)


def _prepare_outline_foreground(foreground: np.ndarray, *, dpi: int) -> np.ndarray:
    gap_px = max(3, round(dpi * 0.02))
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (gap_px, gap_px))
    return cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, close_kernel)
