"""Raster linework vectorization into debug SVG and geometry."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

import cv2
import numpy as np

from pattern_refine.geometry import PathGeometry, Point

SVG_NS = "http://www.w3.org/2000/svg"


def vectorize_lines_to_svg(
    lines_image: np.ndarray,
    svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
    dpi: int,
    min_area_px: float = 100.0,
) -> list[PathGeometry]:
    """Trace major pattern-piece outline candidates and write debug SVG."""

    geometries = vectorize_lines(
        lines_image,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        dpi=dpi,
        min_area_px=min_area_px,
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
) -> list[PathGeometry]:
    """Convert a black-on-white line image to object-level outline candidates."""

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
    geometries: list[PathGeometry],
    svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
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
    for index, geometry in enumerate(geometries, start=1):
        ElementTree.SubElement(
            group,
            f"{{{SVG_NS}}}path",
            {
                "id": f"path-{index:04d}",
                "d": path_to_svg_d(geometry),
            },
        )
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


def _prepare_outline_foreground(foreground: np.ndarray, *, dpi: int) -> np.ndarray:
    gap_px = max(3, round(dpi * 0.02))
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (gap_px, gap_px))
    return cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, close_kernel)
