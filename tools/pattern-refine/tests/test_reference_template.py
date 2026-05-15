from pathlib import Path

import pytest

from pattern_refine.geometry import LineGeometry, PathGeometry, RectGeometry
from pattern_refine.reference_template import load_reference_geometry_template


def test_load_reference_geometry_template_normalizes_viewbox_to_page_mm(tmp_path: Path) -> None:
    reference = tmp_path / "reference.svg"
    reference.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 20 100 200">
  <path d="M 10 20 C 20 20 30 40 50 60 L 60 80 Z"/>
  <line x1="10" y1="20" x2="110" y2="220"/>
  <rect x="20" y="40" width="10" height="20"/>
  <polygon points="10,20 110,20 110,220"/>
</svg>
""",
        encoding="utf-8",
    )

    template = load_reference_geometry_template(
        reference,
        page_width_mm=50.0,
        page_height_mm=100.0,
    )

    assert template.page_width_mm == pytest.approx(50.0)
    assert template.page_height_mm == pytest.approx(100.0)
    assert template.source_viewbox == (10.0, 20.0, 110.0, 220.0)
    assert len(template.geometries) == 4
    path = template.geometries[0]
    assert isinstance(path, PathGeometry)
    assert path.closed is True
    assert path.points[0].x_mm == pytest.approx(0.0)
    assert path.points[0].y_mm == pytest.approx(0.0)
    assert path.points[-1].x_mm == pytest.approx(25.0)
    assert path.points[-1].y_mm == pytest.approx(30.0)
    line = template.geometries[1]
    assert isinstance(line, LineGeometry)
    assert line.start.x_mm == pytest.approx(0.0)
    assert line.end.x_mm == pytest.approx(50.0)
    assert line.end.y_mm == pytest.approx(100.0)
    rect = template.geometries[2]
    assert isinstance(rect, RectGeometry)
    assert rect.x_mm == pytest.approx(5.0)
    assert rect.y_mm == pytest.approx(10.0)
    assert rect.width_mm == pytest.approx(5.0)
    assert rect.height_mm == pytest.approx(10.0)


def test_load_real_pink_reference_preserves_object_types() -> None:
    reference = Path(
        "knowledge_base/PDF-SVG/Original_PinkShirts/pink-dress-simple-reference.svg"
    )

    template = load_reference_geometry_template(
        reference,
        page_width_mm=297.038889,
        page_height_mm=420.040278,
    )

    path_count = sum(isinstance(geometry, PathGeometry) for geometry in template.geometries)
    line_count = sum(isinstance(geometry, LineGeometry) for geometry in template.geometries)
    rect_count = sum(isinstance(geometry, RectGeometry) for geometry in template.geometries)

    assert path_count >= 9
    assert line_count >= 10
    assert rect_count == 1
    assert template.page_width_mm == pytest.approx(297.038889)
    assert template.page_height_mm == pytest.approx(420.040278)
