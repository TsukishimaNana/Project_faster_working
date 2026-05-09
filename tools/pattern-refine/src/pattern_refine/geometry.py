"""Geometry primitives used between vectorization and exporters."""

from __future__ import annotations

from dataclasses import dataclass


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
