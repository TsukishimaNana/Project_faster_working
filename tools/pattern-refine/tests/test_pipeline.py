from pathlib import Path

import cv2
import fitz
import numpy as np
import pytest

from pattern_refine.pipeline import extract_black_lines, refine_pdf


def test_extract_black_lines_keeps_dark_linework_on_white_background() -> None:
    image = np.full((48, 48, 3), 255, dtype=np.uint8)
    image[24, 8:40] = 0

    lines = extract_black_lines(image)

    assert lines[24, 24] == 0
    assert lines[4, 4] == 255


def test_refine_pdf_renders_first_page_and_refuses_overwrite(tmp_path: Path) -> None:
    input_pdf = tmp_path / "sample.pdf"
    output_dir = tmp_path / "output"
    document = fitz.open()
    page = document.new_page(width=72, height=72)
    page.draw_rect((10, 10, 62, 62), color=(0, 0, 0), width=1)
    document.save(input_pdf)
    document.close()

    result = refine_pdf(input_pdf, output_dir, dpi=72)

    assert result.render_path.exists()
    assert result.lines_path.exists()
    assert result.cleaned_svg_path.exists()
    assert result.page_width_mm == pytest.approx(25.4)
    assert result.page_height_mm == pytest.approx(25.4)
    assert len(result.geometries) > 0
    render = cv2.imread(str(result.render_path))
    lines = cv2.imread(str(result.lines_path), cv2.IMREAD_GRAYSCALE)
    assert render is not None
    assert lines is not None
    assert render.shape[:2] == (72, 72)
    assert int(lines.min()) < 255

    with pytest.raises(FileExistsError):
        refine_pdf(input_pdf, output_dir, dpi=72)
