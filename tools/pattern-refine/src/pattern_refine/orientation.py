"""Page orientation normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass

from pattern_refine.geometry import GeometryObject, LineGeometry, PathGeometry, Point, RectGeometry


@dataclass(frozen=True)
class PageCoordinateTransform:
    """Map rendered PDF page coordinates into unrotated page coordinates."""

    rotation: int
    render_width_mm: float
    render_height_mm: float
    page_width_mm: float
    page_height_mm: float

    def point_from_render(self, point: Point) -> Point:
        rotation = self.rotation % 360
        if rotation == 0:
            return Point(
                x_mm=point.x_mm * self.page_width_mm / self.render_width_mm,
                y_mm=point.y_mm * self.page_height_mm / self.render_height_mm,
            )
        if rotation == 90:
            return Point(
                x_mm=point.y_mm * self.page_width_mm / self.render_height_mm,
                y_mm=self.page_height_mm
                - point.x_mm * self.page_height_mm / self.render_width_mm,
            )
        if rotation == 180:
            return Point(
                x_mm=self.page_width_mm
                - point.x_mm * self.page_width_mm / self.render_width_mm,
                y_mm=self.page_height_mm
                - point.y_mm * self.page_height_mm / self.render_height_mm,
            )
        if rotation == 270:
            return Point(
                x_mm=self.page_width_mm
                - point.y_mm * self.page_width_mm / self.render_height_mm,
                y_mm=point.x_mm * self.page_height_mm / self.render_width_mm,
            )
        raise ValueError(f"Unsupported PDF page rotation: {self.rotation}")

    def point_to_render(self, point: Point) -> Point:
        rotation = self.rotation % 360
        if rotation == 0:
            return Point(
                x_mm=point.x_mm * self.render_width_mm / self.page_width_mm,
                y_mm=point.y_mm * self.render_height_mm / self.page_height_mm,
            )
        if rotation == 90:
            return Point(
                x_mm=(self.page_height_mm - point.y_mm) * self.render_width_mm / self.page_height_mm,
                y_mm=point.x_mm * self.render_height_mm / self.page_width_mm,
            )
        if rotation == 180:
            return Point(
                x_mm=(self.page_width_mm - point.x_mm) * self.render_width_mm / self.page_width_mm,
                y_mm=(self.page_height_mm - point.y_mm) * self.render_height_mm / self.page_height_mm,
            )
        if rotation == 270:
            return Point(
                x_mm=point.y_mm * self.render_width_mm / self.page_height_mm,
                y_mm=(self.page_width_mm - point.x_mm) * self.render_height_mm / self.page_width_mm,
            )
        raise ValueError(f"Unsupported PDF page rotation: {self.rotation}")


def transform_geometry(
    geometry: GeometryObject,
    transform: PageCoordinateTransform,
) -> GeometryObject:
    if isinstance(geometry, PathGeometry):
        return transform_path_geometry(geometry, transform)
    if isinstance(geometry, LineGeometry):
        return LineGeometry(
            start=transform.point_from_render(geometry.start),
            end=transform.point_from_render(geometry.end),
        )
    if isinstance(geometry, RectGeometry):
        points = (
            Point(geometry.x_mm, geometry.y_mm),
            Point(geometry.x_mm + geometry.width_mm, geometry.y_mm),
            Point(geometry.x_mm + geometry.width_mm, geometry.y_mm + geometry.height_mm),
            Point(geometry.x_mm, geometry.y_mm + geometry.height_mm),
        )
        transformed = tuple(transform.point_from_render(point) for point in points)
        xs = [point.x_mm for point in transformed]
        ys = [point.y_mm for point in transformed]
        return RectGeometry(
            x_mm=min(xs),
            y_mm=min(ys),
            width_mm=max(xs) - min(xs),
            height_mm=max(ys) - min(ys),
        )
    return geometry


def transform_path_geometry(
    geometry: PathGeometry,
    transform: PageCoordinateTransform,
) -> PathGeometry:
    return PathGeometry(
        points=tuple(transform.point_from_render(point) for point in geometry.points),
        closed=geometry.closed,
    )


def transform_path_geometry_to_render(
    geometry: PathGeometry,
    transform: PageCoordinateTransform,
) -> PathGeometry:
    return PathGeometry(
        points=tuple(transform.point_to_render(point) for point in geometry.points),
        closed=geometry.closed,
    )
