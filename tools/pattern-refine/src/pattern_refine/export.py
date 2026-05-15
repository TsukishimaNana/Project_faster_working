"""Export adapters for refined geometry outputs."""

from __future__ import annotations

from pathlib import Path

from reportlab.pdfgen import canvas

from pattern_refine.geometry import GeometryObject, LineGeometry, PathGeometry, RectGeometry

PT_PER_MM = 72 / 25.4


def write_refined_pdf(
    geometries: tuple[GeometryObject, ...],
    pdf_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
    stroke_width_mm: float = 0.1,
) -> None:
    """Write refined geometry as a vector PDF using millimeter coordinates."""

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    page_width_pt = page_width_mm * PT_PER_MM
    page_height_pt = page_height_mm * PT_PER_MM
    output = canvas.Canvas(str(pdf_path), pagesize=(page_width_pt, page_height_pt))
    output.setLineWidth(stroke_width_mm * PT_PER_MM)
    output.setStrokeColorRGB(0, 0, 0)
    output.setLineJoin(1)
    output.setLineCap(1)

    for geometry in geometries:
        if isinstance(geometry, PathGeometry):
            _draw_path(output, geometry, page_height_pt)
        elif isinstance(geometry, LineGeometry):
            output.line(
                geometry.start.x_mm * PT_PER_MM,
                page_height_pt - geometry.start.y_mm * PT_PER_MM,
                geometry.end.x_mm * PT_PER_MM,
                page_height_pt - geometry.end.y_mm * PT_PER_MM,
            )
        elif isinstance(geometry, RectGeometry):
            output.rect(
                geometry.x_mm * PT_PER_MM,
                page_height_pt - (geometry.y_mm + geometry.height_mm) * PT_PER_MM,
                geometry.width_mm * PT_PER_MM,
                geometry.height_mm * PT_PER_MM,
                stroke=1,
                fill=0,
            )

    output.showPage()
    output.save()


def _draw_path(output: canvas.Canvas, geometry: PathGeometry, page_height_pt: float) -> None:
    if len(geometry.points) < 2:
        return
    path = output.beginPath()
    first = geometry.points[0]
    path.moveTo(first.x_mm * PT_PER_MM, page_height_pt - first.y_mm * PT_PER_MM)
    for point in geometry.points[1:]:
        path.lineTo(point.x_mm * PT_PER_MM, page_height_pt - point.y_mm * PT_PER_MM)
    if geometry.closed:
        path.close()
    output.drawPath(path, stroke=1, fill=0)
