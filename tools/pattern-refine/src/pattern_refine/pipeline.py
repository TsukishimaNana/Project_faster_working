"""First-pass PDF rendering and raster line extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import fitz
import numpy as np

from pattern_refine.geometry import PathGeometry
from pattern_refine.vectorize import vectorize_lines_to_svg


@dataclass(frozen=True)
class PageRenderResult:
    """Metadata for a rendered PDF page."""

    page_number: int
    render_path: Path
    lines_path: Path
    cleaned_svg_path: Path
    page_width_mm: float
    page_height_mm: float
    dpi: int
    geometries: tuple[PathGeometry, ...]


def refine_pdf(
    input_pdf: Path,
    output_dir: Path,
    *,
    dpi: int = 600,
    scale: str = "auto",
    overwrite: bool = False,
) -> PageRenderResult:
    """Render the first PDF page and extract black linework into debug rasters."""

    if scale != "auto":
        raise ValueError("Only --scale auto is supported in this MVP slice.")
    if dpi <= 0:
        raise ValueError("--dpi must be a positive integer.")
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF does not exist: {input_pdf}")
    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError(f"Input must be a PDF: {input_pdf}")

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_pdf.stem
    render_path = output_dir / f"{stem}-page-001-render.png"
    lines_path = output_dir / f"{stem}-page-001-lines.png"
    cleaned_svg_path = output_dir / f"{stem}.cleaned.svg"
    _ensure_can_write(render_path, overwrite=overwrite)
    _ensure_can_write(lines_path, overwrite=overwrite)
    _ensure_can_write(cleaned_svg_path, overwrite=overwrite)

    with fitz.open(input_pdf) as document:
        if document.page_count < 1:
            raise ValueError(f"Input PDF has no pages: {input_pdf}")
        page = document.load_page(0)
        render = _render_page(page, dpi=dpi)
        page_width_mm = page.rect.width * 25.4 / 72
        page_height_mm = page.rect.height * 25.4 / 72

    cv2.imwrite(str(render_path), render)
    lines = extract_black_lines(render)
    cv2.imwrite(str(lines_path), lines)
    geometries = vectorize_lines_to_svg(
        lines,
        cleaned_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        dpi=dpi,
    )

    return PageRenderResult(
        page_number=1,
        render_path=render_path,
        lines_path=lines_path,
        cleaned_svg_path=cleaned_svg_path,
        page_width_mm=page_width_mm,
        page_height_mm=page_height_mm,
        dpi=dpi,
        geometries=tuple(geometries),
    )


def extract_black_lines(image: np.ndarray) -> np.ndarray:
    """Extract dark linework from a white or near-white scanned page."""

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU,
    )
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    return 255 - cleaned


def _render_page(page: fitz.Page, *, dpi: int) -> np.ndarray:
    zoom = dpi / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height,
        pixmap.width,
        pixmap.n,
    )
    if pixmap.n == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    return np.ascontiguousarray(image)


def _ensure_can_write(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists, pass --overwrite to replace: {path}")
