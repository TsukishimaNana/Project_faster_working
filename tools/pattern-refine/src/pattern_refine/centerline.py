"""Centerline reconstruction from scanned ink blobs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from pattern_refine.geometry import PathGeometry, Point


@dataclass(frozen=True)
class CenterlineReport:
    path_count: int
    closed_path_count: int
    open_path_count: int
    longest_path_mm: float | None
    total_path_length_mm: float
    stitched_path_count_delta: int
    skeleton_endpoint_count: int
    skeleton_junction_count: int
    pruned_spur_count: int
    pruned_spur_length_mm: float

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "path_count": self.path_count,
            "closed_path_count": self.closed_path_count,
            "open_path_count": self.open_path_count,
            "longest_path_mm": self.longest_path_mm,
            "total_path_length_mm": self.total_path_length_mm,
            "stitched_path_count_delta": self.stitched_path_count_delta,
            "skeleton_endpoint_count": self.skeleton_endpoint_count,
            "skeleton_junction_count": self.skeleton_junction_count,
            "pruned_spur_count": self.pruned_spur_count,
            "pruned_spur_length_mm": self.pruned_spur_length_mm,
        }


def reconstruct_centerline_paths(
    lines_image: np.ndarray,
    *,
    page_width_mm: float,
    page_height_mm: float,
    dpi: int,
    min_path_length_mm: float = 8.0,
    stitch_gap_mm: float = 1.2,
    prune_spur_length_mm: float = 1.5,
) -> tuple[PathGeometry, ...]:
    """Build single-stroke centerline candidates from black-on-white linework."""

    paths, _ = reconstruct_centerline_paths_with_report(
        lines_image,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        dpi=dpi,
        min_path_length_mm=min_path_length_mm,
        stitch_gap_mm=stitch_gap_mm,
        prune_spur_length_mm=prune_spur_length_mm,
    )
    return paths


def reconstruct_centerline_paths_with_report(
    lines_image: np.ndarray,
    *,
    page_width_mm: float,
    page_height_mm: float,
    dpi: int,
    min_path_length_mm: float = 8.0,
    stitch_gap_mm: float = 1.2,
    prune_spur_length_mm: float = 1.5,
) -> tuple[tuple[PathGeometry, ...], CenterlineReport]:
    """Build centerline candidates and return reconstruction diagnostics."""

    if lines_image.ndim == 3:
        gray = cv2.cvtColor(lines_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = lines_image
    foreground = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1]
    foreground = _bridge_small_gaps(foreground, dpi=dpi)
    skeleton = _skeletonize(foreground)
    pixel_to_mm_x = page_width_mm / skeleton.shape[1]
    pixel_to_mm_y = page_height_mm / skeleton.shape[0]
    skeleton, pruned_spur_count, pruned_spur_length_mm = _prune_terminal_spurs(
        skeleton,
        max_spur_length_mm=prune_spur_length_mm,
        pixel_to_mm_x=pixel_to_mm_x,
        pixel_to_mm_y=pixel_to_mm_y,
    )
    endpoint_count, junction_count = _skeleton_node_counts(skeleton)
    paths = _trace_skeleton_paths(
        skeleton,
        pixel_to_mm_x=pixel_to_mm_x,
        pixel_to_mm_y=pixel_to_mm_y,
        min_path_length_mm=min_path_length_mm,
    )
    unstiched_count = len(paths)
    paths = _stitch_open_paths(paths, max_gap_mm=stitch_gap_mm)
    paths = _deduplicate_closed_paths(paths)
    sorted_paths = tuple(sorted(paths, key=lambda path: path.perimeter_mm, reverse=True))
    return sorted_paths, build_centerline_report(
        sorted_paths,
        unstitched_path_count=unstiched_count,
        skeleton_endpoint_count=endpoint_count,
        skeleton_junction_count=junction_count,
        pruned_spur_count=pruned_spur_count,
        pruned_spur_length_mm=pruned_spur_length_mm,
    )


def build_centerline_report(
    paths: tuple[PathGeometry, ...],
    *,
    unstitched_path_count: int | None = None,
    skeleton_endpoint_count: int = 0,
    skeleton_junction_count: int = 0,
    pruned_spur_count: int = 0,
    pruned_spur_length_mm: float = 0.0,
) -> CenterlineReport:
    path_count = len(paths)
    closed_path_count = sum(path.closed for path in paths)
    longest_path = max((path.perimeter_mm for path in paths), default=None)
    return CenterlineReport(
        path_count=path_count,
        closed_path_count=closed_path_count,
        open_path_count=path_count - closed_path_count,
        longest_path_mm=longest_path,
        total_path_length_mm=sum(path.perimeter_mm for path in paths),
        stitched_path_count_delta=(
            0 if unstitched_path_count is None else unstitched_path_count - path_count
        ),
        skeleton_endpoint_count=skeleton_endpoint_count,
        skeleton_junction_count=skeleton_junction_count,
        pruned_spur_count=pruned_spur_count,
        pruned_spur_length_mm=pruned_spur_length_mm,
    )


def write_centerline_report(report: CenterlineReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def reconstruct_centerline_paths_for_regions(
    lines_image: np.ndarray,
    regions: tuple[PathGeometry, ...],
    *,
    page_width_mm: float,
    page_height_mm: float,
    dpi: int,
    region_padding_mm: float = 4.0,
    min_path_length_mm: float = 8.0,
    stitch_gap_mm: float = 1.2,
    prune_spur_length_mm: float = 1.5,
) -> tuple[PathGeometry, ...]:
    """Reconstruct centerline paths inside per-piece regions on the render image."""

    if lines_image.ndim == 3:
        gray = cv2.cvtColor(lines_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = lines_image
    pixel_to_mm_x = page_width_mm / gray.shape[1]
    pixel_to_mm_y = page_height_mm / gray.shape[0]
    region_paths: list[PathGeometry] = []
    for region in regions:
        if not region.closed or region.area_mm2 <= 20.0:
            continue
        xmin, ymin, xmax, ymax = region.bounds
        pad_x = max(2, round(region_padding_mm / pixel_to_mm_x))
        pad_y = max(2, round(region_padding_mm / pixel_to_mm_y))
        x0 = max(0, int(np.floor(xmin / pixel_to_mm_x)) - pad_x)
        y0 = max(0, int(np.floor(ymin / pixel_to_mm_y)) - pad_y)
        x1 = min(gray.shape[1], int(np.ceil(xmax / pixel_to_mm_x)) + pad_x)
        y1 = min(gray.shape[0], int(np.ceil(ymax / pixel_to_mm_y)) + pad_y)
        if x1 - x0 < 3 or y1 - y0 < 3:
            continue
        region_image = gray[y0:y1, x0:x1]
        region_image = _apply_region_polygon_mask(
            region_image,
            region,
            x_offset_mm=x0 * pixel_to_mm_x,
            y_offset_mm=y0 * pixel_to_mm_y,
            pixel_to_mm_x=pixel_to_mm_x,
            pixel_to_mm_y=pixel_to_mm_y,
        )
        local_paths = reconstruct_centerline_paths(
            region_image,
            page_width_mm=(x1 - x0) * pixel_to_mm_x,
            page_height_mm=(y1 - y0) * pixel_to_mm_y,
            dpi=dpi,
            min_path_length_mm=min_path_length_mm,
            stitch_gap_mm=stitch_gap_mm,
            prune_spur_length_mm=prune_spur_length_mm,
        )
        x_offset_mm = x0 * pixel_to_mm_x
        y_offset_mm = y0 * pixel_to_mm_y
        for path in local_paths:
            region_paths.append(
                PathGeometry(
                    points=tuple(
                        Point(
                            point.x_mm + x_offset_mm,
                            point.y_mm + y_offset_mm,
                        )
                        for point in path.points
                    ),
                    closed=path.closed,
                )
            )
    return tuple(region_paths)


def _apply_region_polygon_mask(
    image: np.ndarray,
    region: PathGeometry,
    *,
    x_offset_mm: float,
    y_offset_mm: float,
    pixel_to_mm_x: float,
    pixel_to_mm_y: float,
) -> np.ndarray:
    if image.size == 0 or not region.points:
        return image
    polygon = np.array(
        [
            [
                int(round((point.x_mm - x_offset_mm) / pixel_to_mm_x)),
                int(round((point.y_mm - y_offset_mm) / pixel_to_mm_y)),
            ]
            for point in region.points
        ],
        dtype=np.int32,
    )
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [polygon], 255)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.dilate(mask, kernel, iterations=1)
    masked = np.full_like(image, 255)
    masked[mask > 0] = image[mask > 0]
    return masked


def _bridge_small_gaps(foreground: np.ndarray, *, dpi: int) -> np.ndarray:
    gap_px = max(3, round(dpi * 0.01))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (gap_px, gap_px))
    return cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, kernel)


def _skeletonize(foreground: np.ndarray) -> np.ndarray:
    binary = (foreground > 0).astype(np.uint8)
    while True:
        previous = binary.copy()
        step_one = _zhang_suen_subiteration(binary, first=True)
        step_two = _zhang_suen_subiteration(step_one, first=False)
        if np.array_equal(step_two, previous):
            break
        binary = step_two
    return (binary * 255).astype(np.uint8)


def _zhang_suen_subiteration(binary: np.ndarray, *, first: bool) -> np.ndarray:
    padded = np.pad(binary, 1, mode="constant")
    center = padded[1:-1, 1:-1]
    p2 = padded[:-2, 1:-1]
    p3 = padded[:-2, 2:]
    p4 = padded[1:-1, 2:]
    p5 = padded[2:, 2:]
    p6 = padded[2:, 1:-1]
    p7 = padded[2:, :-2]
    p8 = padded[1:-1, :-2]
    p9 = padded[:-2, :-2]

    neighbors = (p2, p3, p4, p5, p6, p7, p8, p9)
    neighbor_count = sum(neighbors)
    transitions = (
        ((p2 == 0) & (p3 == 1)).astype(np.uint8)
        + ((p3 == 0) & (p4 == 1)).astype(np.uint8)
        + ((p4 == 0) & (p5 == 1)).astype(np.uint8)
        + ((p5 == 0) & (p6 == 1)).astype(np.uint8)
        + ((p6 == 0) & (p7 == 1)).astype(np.uint8)
        + ((p7 == 0) & (p8 == 1)).astype(np.uint8)
        + ((p8 == 0) & (p9 == 1)).astype(np.uint8)
        + ((p9 == 0) & (p2 == 1)).astype(np.uint8)
    )
    if first:
        condition = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
    else:
        condition = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
    delete = (center == 1) & (neighbor_count >= 2) & (neighbor_count <= 6) & (transitions == 1) & condition
    result = binary.copy()
    result[delete] = 0
    return result


def _trace_skeleton_paths(
    skeleton: np.ndarray,
    *,
    pixel_to_mm_x: float,
    pixel_to_mm_y: float,
    min_path_length_mm: float,
) -> list[PathGeometry]:
    pixels = set(zip(*np.nonzero(skeleton == 255), strict=False))
    neighbors_by_pixel = {pixel: _pixel_neighbors(pixel, pixels) for pixel in pixels}
    endpoints = [
        pixel
        for pixel, neighbors in neighbors_by_pixel.items()
        if _skeleton_node_kind(pixel, neighbors) != "line"
    ]
    visited_edges: set[frozenset[tuple[int, int]]] = set()
    paths: list[PathGeometry] = []

    for start in endpoints:
        for neighbor in neighbors_by_pixel[start]:
            edge = frozenset((start, neighbor))
            if edge in visited_edges:
                continue
            path_pixels = _walk_skeleton_branch(
                start,
                neighbor,
                neighbors_by_pixel,
                visited_edges,
            )
            path = _path_from_pixels(
                path_pixels,
                pixel_to_mm_x=pixel_to_mm_x,
                pixel_to_mm_y=pixel_to_mm_y,
                closed=False,
            )
            if path.perimeter_mm >= min_path_length_mm:
                paths.append(path)

    for start in pixels:
        for neighbor in neighbors_by_pixel[start]:
            edge = frozenset((start, neighbor))
            if edge in visited_edges:
                continue
            path_pixels = _walk_skeleton_branch(
                start,
                neighbor,
                neighbors_by_pixel,
                visited_edges,
            )
            path = _path_from_pixels(
                path_pixels,
                pixel_to_mm_x=pixel_to_mm_x,
                pixel_to_mm_y=pixel_to_mm_y,
                closed=True,
            )
            if path.perimeter_mm >= min_path_length_mm:
                paths.append(path)
    return paths


def _prune_terminal_spurs(
    skeleton: np.ndarray,
    *,
    max_spur_length_mm: float,
    pixel_to_mm_x: float,
    pixel_to_mm_y: float,
) -> tuple[np.ndarray, int, float]:
    pixels = set(zip(*np.nonzero(skeleton == 255), strict=False))
    if not pixels:
        return skeleton, 0, 0.0
    pruned = set(pixels)
    pruned_count = 0
    pruned_length = 0.0
    changed = True
    while changed:
        changed = False
        neighbors_by_pixel = {pixel: _pixel_neighbors(pixel, pruned) for pixel in pruned}
        endpoints = [
            pixel
            for pixel, neighbors in neighbors_by_pixel.items()
            if _skeleton_node_kind(pixel, neighbors) == "endpoint"
        ]
        for endpoint in endpoints:
            if endpoint not in pruned:
                continue
            branch = _terminal_branch_to_junction(endpoint, neighbors_by_pixel)
            if branch is None:
                continue
            length_mm = _pixel_path_length(
                branch,
                pixel_to_mm_x=pixel_to_mm_x,
                pixel_to_mm_y=pixel_to_mm_y,
            )
            if length_mm > max_spur_length_mm:
                continue
            for pixel in branch[:-1]:
                pruned.discard(pixel)
            pruned_count += 1
            pruned_length += length_mm
            changed = True
    result = np.zeros_like(skeleton)
    if pruned:
        ys, xs = zip(*pruned, strict=False)
        result[np.array(ys), np.array(xs)] = 255
    return result, pruned_count, pruned_length


def _terminal_branch_to_junction(
    endpoint: tuple[int, int],
    neighbors_by_pixel: dict[tuple[int, int], list[tuple[int, int]]],
) -> list[tuple[int, int]] | None:
    branch = [endpoint]
    previous: tuple[int, int] | None = None
    current = endpoint
    while True:
        neighbors = [
            neighbor
            for neighbor in neighbors_by_pixel.get(current, [])
            if neighbor != previous
        ]
        if _skeleton_node_kind(current, neighbors_by_pixel.get(current, [])) == "junction":
            return branch
        if len(neighbors) != 1:
            return None
        previous, current = current, neighbors[0]
        branch.append(current)
        if _skeleton_node_kind(current, neighbors_by_pixel.get(current, [])) == "junction":
            return branch


def _skeleton_node_counts(skeleton: np.ndarray) -> tuple[int, int]:
    pixels = set(zip(*np.nonzero(skeleton == 255), strict=False))
    neighbors_by_pixel = {pixel: _pixel_neighbors(pixel, pixels) for pixel in pixels}
    endpoint_count = sum(
        _skeleton_node_kind(pixel, neighbors) == "endpoint"
        for pixel, neighbors in neighbors_by_pixel.items()
    )
    junction_count = sum(
        _skeleton_node_kind(pixel, neighbors) == "junction"
        for pixel, neighbors in neighbors_by_pixel.items()
    )
    return endpoint_count, junction_count


def _pixel_path_length(
    pixels: list[tuple[int, int]],
    *,
    pixel_to_mm_x: float,
    pixel_to_mm_y: float,
) -> float:
    if len(pixels) < 2:
        return 0.0
    length = 0.0
    for first, second in zip(pixels, pixels[1:], strict=False):
        y_delta = (second[0] - first[0]) * pixel_to_mm_y
        x_delta = (second[1] - first[1]) * pixel_to_mm_x
        length += float(np.hypot(x_delta, y_delta))
    return length


def _walk_skeleton_branch(
    start: tuple[int, int],
    next_pixel: tuple[int, int],
    neighbors_by_pixel: dict[tuple[int, int], list[tuple[int, int]]],
    visited_edges: set[frozenset[tuple[int, int]]],
) -> list[tuple[int, int]]:
    path = [start, next_pixel]
    previous = start
    current = next_pixel
    visited_edges.add(frozenset((previous, current)))
    while _skeleton_node_kind(current, neighbors_by_pixel[current]) == "line":
        candidates = [pixel for pixel in neighbors_by_pixel[current] if pixel != previous]
        if not candidates:
            break
        following = candidates[0]
        edge = frozenset((current, following))
        if following == start:
            visited_edges.add(edge)
            break
        if edge in visited_edges:
            break
        path.append(following)
        visited_edges.add(edge)
        previous, current = current, following
    return path


def _pixel_neighbors(
    pixel: tuple[int, int],
    pixels: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    y, x = pixel
    neighbors: list[tuple[int, int]] = []
    for y_delta in (-1, 0, 1):
        for x_delta in (-1, 0, 1):
            if y_delta == 0 and x_delta == 0:
                continue
            neighbor = (y + y_delta, x + x_delta)
            if neighbor in pixels:
                neighbors.append(neighbor)
    return neighbors


def _skeleton_node_kind(
    pixel: tuple[int, int],
    neighbors: list[tuple[int, int]],
) -> str:
    crossing_count = _crossing_number(pixel, set(neighbors))
    if crossing_count <= 0:
        return "isolated"
    if crossing_count == 1:
        return "endpoint"
    if crossing_count == 2:
        return "line"
    return "junction"


def _crossing_number(
    pixel: tuple[int, int],
    neighbors: set[tuple[int, int]],
) -> int:
    y, x = pixel
    ordered = (
        (y - 1, x),
        (y - 1, x + 1),
        (y, x + 1),
        (y + 1, x + 1),
        (y + 1, x),
        (y + 1, x - 1),
        (y, x - 1),
        (y - 1, x - 1),
    )
    values = [1 if neighbor in neighbors else 0 for neighbor in ordered]
    return sum(
        1
        for index, value in enumerate(values)
        if value == 0 and values[(index + 1) % len(values)] == 1
    )


def _path_from_pixels(
    pixels: list[tuple[int, int]],
    *,
    pixel_to_mm_x: float,
    pixel_to_mm_y: float,
    closed: bool,
) -> PathGeometry:
    points = tuple(
        Point(
            x_mm=(x + 0.5) * pixel_to_mm_x,
            y_mm=(y + 0.5) * pixel_to_mm_y,
        )
        for y, x in pixels
    )
    return PathGeometry(points=points, closed=closed)


def _stitch_open_paths(
    paths: list[PathGeometry],
    *,
    max_gap_mm: float,
) -> list[PathGeometry]:
    stitched = list(paths)
    changed = True
    while changed:
        changed = False
        best: tuple[float, int, int, PathGeometry] | None = None
        for first_index, first in enumerate(stitched):
            if first.closed:
                continue
            for second_index in range(first_index + 1, len(stitched)):
                second = stitched[second_index]
                if second.closed:
                    continue
                candidate = _best_stitched_path(first, second, max_gap_mm=max_gap_mm)
                if candidate is None:
                    continue
                gap, stitched_path = candidate
                if best is None or gap < best[0]:
                    best = (gap, first_index, second_index, stitched_path)
        if best is None:
            continue
        _, first_index, second_index, stitched_path = best
        stitched[first_index] = stitched_path
        stitched.pop(second_index)
        changed = True
    return stitched


def _deduplicate_closed_paths(paths: list[PathGeometry]) -> list[PathGeometry]:
    deduplicated: list[PathGeometry] = []
    for path in sorted(paths, key=lambda item: item.perimeter_mm, reverse=True):
        if path.closed and any(
            existing.closed and _bbox_overlap_ratio(path.bounds, existing.bounds) >= 0.85
            for existing in deduplicated
        ):
            continue
        deduplicated.append(path)
    return deduplicated


def _bbox_overlap_ratio(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    x_overlap = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    y_overlap = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    intersection = x_overlap * y_overlap
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    smaller = min(first_area, second_area)
    return intersection / smaller if smaller > 0 else 0.0


def _best_stitched_path(
    first: PathGeometry,
    second: PathGeometry,
    *,
    max_gap_mm: float,
) -> tuple[float, PathGeometry] | None:
    variants = (
        (first.points, second.points),
        (tuple(reversed(first.points)), second.points),
        (first.points, tuple(reversed(second.points))),
        (tuple(reversed(first.points)), tuple(reversed(second.points))),
    )
    best: tuple[float, PathGeometry] | None = None
    for left, right in variants:
        if not left or not right:
            continue
        gap = _point_distance(left[-1], right[0])
        if gap > max_gap_mm:
            continue
        if not _endpoint_directions_are_compatible(left, right):
            continue
        stitched_points = (*left, *right)
        closed = _point_distance(stitched_points[0], stitched_points[-1]) <= max_gap_mm
        if closed:
            stitched_points = stitched_points[:-1]
        path = PathGeometry(points=stitched_points, closed=closed)
        if best is None or gap < best[0]:
            best = (gap, path)
    return best


def _endpoint_directions_are_compatible(
    left: tuple[Point, ...],
    right: tuple[Point, ...],
    *,
    min_cosine: float = 0.35,
) -> bool:
    if len(left) < 2 or len(right) < 2:
        return True
    left_vector = (left[-1].x_mm - left[-2].x_mm, left[-1].y_mm - left[-2].y_mm)
    right_vector = (right[1].x_mm - right[0].x_mm, right[1].y_mm - right[0].y_mm)
    left_length = float(np.hypot(left_vector[0], left_vector[1]))
    right_length = float(np.hypot(right_vector[0], right_vector[1]))
    if left_length == 0 or right_length == 0:
        return True
    cosine = (
        left_vector[0] * right_vector[0] + left_vector[1] * right_vector[1]
    ) / (left_length * right_length)
    return cosine >= min_cosine


def _point_distance(first: Point, second: Point) -> float:
    return float(np.hypot(second.x_mm - first.x_mm, second.y_mm - first.y_mm))
