"""Geometry primitives used between vectorization and exporters."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import TypeAlias


@dataclass(frozen=True)
class Point:
    x_mm: float
    y_mm: float


@dataclass(frozen=True)
class PathGeometry:
    points: tuple[Point, ...]
    closed: bool

    @property
    def is_empty(self) -> bool:
        return len(self.points) == 0

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        if self.is_empty:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [point.x_mm for point in self.points]
        ys = [point.y_mm for point in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def area_mm2(self) -> float:
        if len(self.points) < 3:
            return 0.0
        area = 0.0
        for index, point in enumerate(self.points):
            next_point = self.points[(index + 1) % len(self.points)]
            area += point.x_mm * next_point.y_mm - next_point.x_mm * point.y_mm
        return abs(area) / 2

    @property
    def perimeter_mm(self) -> float:
        if len(self.points) < 2:
            return 0.0
        length = 0.0
        segment_count = len(self.points) if self.closed else len(self.points) - 1
        for index in range(segment_count):
            start = self.points[index]
            end = self.points[(index + 1) % len(self.points)]
            length += hypot(end.x_mm - start.x_mm, end.y_mm - start.y_mm)
        return length


@dataclass(frozen=True)
class LineGeometry:
    start: Point
    end: Point

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (
            min(self.start.x_mm, self.end.x_mm),
            min(self.start.y_mm, self.end.y_mm),
            max(self.start.x_mm, self.end.x_mm),
            max(self.start.y_mm, self.end.y_mm),
        )

    @property
    def length_mm(self) -> float:
        return hypot(self.end.x_mm - self.start.x_mm, self.end.y_mm - self.start.y_mm)


@dataclass(frozen=True)
class RectGeometry:
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (
            self.x_mm,
            self.y_mm,
            self.x_mm + self.width_mm,
            self.y_mm + self.height_mm,
        )


GeometryObject: TypeAlias = PathGeometry | LineGeometry | RectGeometry
