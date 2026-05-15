"""SVG comparison output for manual review."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from pattern_refine.evaluate import (
    SVG_NS,
    _collect_piece_shapes,
    _match_piece_shapes,
    _scale_piece_shapes_to_mm,
    _svg_viewbox_bbox,
    _viewbox_size,
    collect_svg_structure_metrics,
)
from pattern_refine.geometry import PathGeometry
from pattern_refine.semantic import CenterlinePieceDiagnostic
from pattern_refine.vectorize import path_to_svg_d

_REVIEW_TAGS = {"path", "line", "rect", "polygon", "polyline"}


def write_svg_comparison(candidate_svg: Path, reference_svg: Path, output_path: Path) -> None:
    """Write candidate/reference/overlay panels into one review SVG."""

    candidate_bbox = collect_svg_structure_metrics(candidate_svg).bbox
    reference_bbox = collect_svg_structure_metrics(reference_svg).bbox
    if candidate_bbox is None:
        raise ValueError(f"Candidate SVG has no comparable geometry: {candidate_svg}")
    if reference_bbox is None:
        raise ValueError(f"Reference SVG has no comparable geometry: {reference_svg}")

    ElementTree.register_namespace("", SVG_NS)
    width = 1200.0
    height = 520.0
    panel_width = 360.0
    panel_height = 440.0
    panel_y = 56.0
    panel_gap = 30.0
    panel_xs = (30.0, 30.0 + panel_width + panel_gap, 30.0 + (panel_width + panel_gap) * 2)

    svg = ElementTree.Element(
        f"{{{SVG_NS}}}svg",
        {
            "width": f"{width:.0f}",
            "height": f"{height:.0f}",
            "viewBox": f"0 0 {width:.0f} {height:.0f}",
            "version": "1.1",
        },
    )
    ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}rect",
        {"x": "0", "y": "0", "width": f"{width:.0f}", "height": f"{height:.0f}", "fill": "#ffffff"},
    )
    _add_label(svg, "Candidate", panel_xs[0], 30.0)
    _add_label(svg, "Reference", panel_xs[1], 30.0)
    _add_label(svg, "Overlay", panel_xs[2], 30.0)
    for panel_x in panel_xs:
        ElementTree.SubElement(
            svg,
            f"{{{SVG_NS}}}rect",
            {
                "x": f"{panel_x:.3f}",
                "y": f"{panel_y:.3f}",
                "width": f"{panel_width:.3f}",
                "height": f"{panel_height:.3f}",
                "fill": "#ffffff",
                "stroke": "#d0d5dd",
                "stroke-width": "1",
            },
        )

    _append_geometry_panel(
        svg,
        candidate_svg,
        candidate_bbox,
        panel_xs[0],
        panel_y,
        panel_width,
        panel_height,
        stroke="#111111",
    )
    _append_geometry_panel(
        svg,
        reference_svg,
        reference_bbox,
        panel_xs[1],
        panel_y,
        panel_width,
        panel_height,
        stroke="#d92d20",
    )
    _append_geometry_panel(
        svg,
        candidate_svg,
        candidate_bbox,
        panel_xs[2],
        panel_y,
        panel_width,
        panel_height,
        stroke="#111111",
        opacity="0.62",
    )
    _append_geometry_panel(
        svg,
        reference_svg,
        reference_bbox,
        panel_xs[2],
        panel_y,
        panel_width,
        panel_height,
        stroke="#d92d20",
        opacity="0.72",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ElementTree.ElementTree(svg).write(output_path, encoding="utf-8", xml_declaration=True)


def write_piece_comparison(candidate_svg: Path, reference_svg: Path, output_path: Path) -> None:
    """Write per-path shape comparison panels after object-level matching."""

    candidate_pieces = _collect_piece_shapes(candidate_svg)
    reference_pieces = _collect_piece_shapes(reference_svg)
    candidate_viewbox = _svg_viewbox_bbox(candidate_svg)
    reference_viewbox = _svg_viewbox_bbox(reference_svg)
    page_size_mm = _viewbox_size(candidate_viewbox)
    candidate_pieces_mm = _scale_piece_shapes_to_mm(
        candidate_pieces,
        candidate_viewbox,
        page_size_mm,
    )
    reference_pieces_mm = _scale_piece_shapes_to_mm(
        reference_pieces,
        reference_viewbox,
        page_size_mm,
    )
    matches, unmatched_candidate, unmatched_reference = _match_piece_shapes(
        candidate_pieces_mm,
        reference_pieces_mm,
        tolerance_mm=0.2,
        match_score_threshold=0.1,
    )
    if not matches:
        raise ValueError("No comparable pieces found for piece comparison.")

    columns = 3
    panel_width = 250.0
    panel_height = 190.0
    gap = 22.0
    margin = 28.0
    label_height = 28.0
    rows = (len(matches) + columns - 1) // columns
    width = margin * 2 + panel_width * columns + gap * (columns - 1)
    height = margin * 2 + (panel_height + label_height) * rows + gap * (rows - 1) + 76

    ElementTree.register_namespace("", SVG_NS)
    svg = ElementTree.Element(
        f"{{{SVG_NS}}}svg",
        {
            "width": f"{width:.0f}",
            "height": f"{height:.0f}",
            "viewBox": f"0 0 {width:.0f} {height:.0f}",
            "version": "1.1",
        },
    )
    ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}rect",
        {"x": "0", "y": "0", "width": f"{width:.0f}", "height": f"{height:.0f}", "fill": "#ffffff"},
    )
    _add_label(svg, "Per-Piece Overlay", margin, 32.0)
    subtitle = ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}text",
        {
            "x": f"{margin:.3f}",
            "y": "56",
            "font-family": "Arial, sans-serif",
            "font-size": "12",
            "fill": "#475467",
        },
    )
    subtitle.text = (
        f"black=candidate, red=reference, matches={len(matches)}, "
        f"unmatched candidate={len(unmatched_candidate)}, unmatched reference={len(unmatched_reference)}"
    )

    candidate_elements = _piece_elements_by_index(candidate_svg)
    reference_elements = _piece_elements_by_index(reference_svg)
    candidate_shapes = {piece.index: piece for piece in candidate_pieces}
    reference_shapes = {piece.index: piece for piece in reference_pieces}
    for match_index, match in enumerate(matches):
        row = match_index // columns
        column = match_index % columns
        x = margin + column * (panel_width + gap)
        y = 82.0 + row * (panel_height + label_height + gap)
        ElementTree.SubElement(
            svg,
            f"{{{SVG_NS}}}rect",
            {
                "x": f"{x:.3f}",
                "y": f"{y:.3f}",
                "width": f"{panel_width:.3f}",
                "height": f"{panel_height:.3f}",
                "fill": "#ffffff",
                "stroke": "#d0d5dd",
                "stroke-width": "1",
            },
        )
        caption = ElementTree.SubElement(
            svg,
            f"{{{SVG_NS}}}text",
            {
                "x": f"{x:.3f}",
                "y": f"{y - 8:.3f}",
                "font-family": "Arial, sans-serif",
                "font-size": "12",
                "fill": "#101828",
            },
        )
        caption.text = (
            f"C{match.candidate_piece_index} vs R{match.reference_piece_index} "
            f"status={'PASS' if match.accepted else 'FAIL'} "
            f"max {match.max_deviation_mm:.3f}mm "
            f"p95 {match.p95_deviation_mm:.3f}mm"
        )
        candidate_shape = candidate_shapes[match.candidate_piece_index]
        reference_shape = reference_shapes[match.reference_piece_index]
        _append_single_element_panel(
            svg,
            candidate_elements[match.candidate_piece_index],
            candidate_shape.bbox,
            x,
            y,
            panel_width,
            panel_height,
            stroke="#111111",
            opacity="0.62",
        )
        _append_single_element_panel(
            svg,
            reference_elements[match.reference_piece_index],
            reference_shape.bbox,
            x,
            y,
            panel_width,
            panel_height,
            stroke="#d92d20",
            opacity="0.72",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ElementTree.ElementTree(svg).write(output_path, encoding="utf-8", xml_declaration=True)


def write_failed_piece_comparison(
    candidate_svg: Path,
    reference_svg: Path,
    output_path: Path,
    *,
    tolerance_mm: float = 0.2,
    page_size_mm: tuple[float, float] | None = None,
    match_score_threshold: float = 0.1,
) -> None:
    """Write failed-only per-piece overlays for acceptance triage."""

    candidate_pieces = _collect_piece_shapes(candidate_svg)
    reference_pieces = _collect_piece_shapes(reference_svg)
    candidate_viewbox = _svg_viewbox_bbox(candidate_svg)
    reference_viewbox = _svg_viewbox_bbox(reference_svg)
    candidate_page_size = page_size_mm or _viewbox_size(candidate_viewbox)
    reference_page_size = page_size_mm or candidate_page_size
    candidate_pieces_mm = _scale_piece_shapes_to_mm(
        candidate_pieces,
        candidate_viewbox,
        candidate_page_size,
    )
    reference_pieces_mm = _scale_piece_shapes_to_mm(
        reference_pieces,
        reference_viewbox,
        reference_page_size,
    )
    matches, unmatched_candidate, unmatched_reference = _match_piece_shapes(
        candidate_pieces_mm,
        reference_pieces_mm,
        tolerance_mm=tolerance_mm,
        match_score_threshold=match_score_threshold,
    )
    failed_panels: list[_FailedPiecePanel] = [
        _FailedPiecePanel(
            failure_type="over-tolerance",
            candidate_index=match.candidate_piece_index,
            reference_index=match.reference_piece_index,
            max_deviation_mm=match.max_deviation_mm,
            p95_deviation_mm=match.p95_deviation_mm,
            bbox_iou=match.bbox_iou,
        )
        for match in matches
        if not match.accepted
    ]
    failed_panels.extend(
        _FailedPiecePanel(
            failure_type="unmatched-reference",
            candidate_index=None,
            reference_index=piece.index,
            max_deviation_mm=None,
            p95_deviation_mm=None,
            bbox_iou=None,
        )
        for piece in unmatched_reference
    )
    failed_panels.extend(
        _FailedPiecePanel(
            failure_type="unmatched-candidate",
            candidate_index=piece.index,
            reference_index=None,
            max_deviation_mm=None,
            p95_deviation_mm=None,
            bbox_iou=None,
        )
        for piece in unmatched_candidate
    )
    if not failed_panels:
        raise ValueError("No failed pieces found for failed piece comparison.")

    columns = 3
    panel_width = 250.0
    panel_height = 190.0
    gap = 22.0
    margin = 28.0
    label_height = 34.0
    rows = (len(failed_panels) + columns - 1) // columns
    width = margin * 2 + panel_width * columns + gap * (columns - 1)
    height = margin * 2 + (panel_height + label_height) * rows + gap * (rows - 1) + 76

    ElementTree.register_namespace("", SVG_NS)
    svg = ElementTree.Element(
        f"{{{SVG_NS}}}svg",
        {
            "width": f"{width:.0f}",
            "height": f"{height:.0f}",
            "viewBox": f"0 0 {width:.0f} {height:.0f}",
            "version": "1.1",
        },
    )
    ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}rect",
        {"x": "0", "y": "0", "width": f"{width:.0f}", "height": f"{height:.0f}", "fill": "#ffffff"},
    )
    _add_label(svg, "Failed Piece Overlay", margin, 32.0)
    subtitle = ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}text",
        {
            "x": f"{margin:.3f}",
            "y": "56",
            "font-family": "Arial, sans-serif",
            "font-size": "12",
            "fill": "#475467",
        },
    )
    subtitle.text = (
        f"failed panels={len(failed_panels)}; tolerance={tolerance_mm:.3f}mm; "
        "black=candidate, red=reference"
    )

    candidate_elements = _piece_elements_by_index(candidate_svg)
    reference_elements = _piece_elements_by_index(reference_svg)
    candidate_shapes = {piece.index: piece for piece in candidate_pieces}
    reference_shapes = {piece.index: piece for piece in reference_pieces}
    for panel_index, panel in enumerate(failed_panels):
        row = panel_index // columns
        column = panel_index % columns
        x = margin + column * (panel_width + gap)
        y = 82.0 + row * (panel_height + label_height + gap)
        ElementTree.SubElement(
            svg,
            f"{{{SVG_NS}}}rect",
            {
                "x": f"{x:.3f}",
                "y": f"{y:.3f}",
                "width": f"{panel_width:.3f}",
                "height": f"{panel_height:.3f}",
                "fill": "#ffffff",
                "stroke": "#d0d5dd",
                "stroke-width": "1",
            },
        )
        caption = ElementTree.SubElement(
            svg,
            f"{{{SVG_NS}}}text",
            {
                "x": f"{x:.3f}",
                "y": f"{y - 8:.3f}",
                "font-family": "Arial, sans-serif",
                "font-size": "12",
                "fill": "#101828",
            },
        )
        caption.text = _failed_piece_caption(panel)
        if panel.candidate_index is not None:
            candidate_shape = candidate_shapes[panel.candidate_index]
            _append_single_element_panel(
                svg,
                candidate_elements[panel.candidate_index],
                candidate_shape.bbox,
                x,
                y,
                panel_width,
                panel_height,
                stroke="#111111",
                opacity="0.62",
            )
        if panel.reference_index is not None:
            reference_shape = reference_shapes[panel.reference_index]
            _append_single_element_panel(
                svg,
                reference_elements[panel.reference_index],
                reference_shape.bbox,
                x,
                y,
                panel_width,
                panel_height,
                stroke="#d92d20",
                opacity="0.72",
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ElementTree.ElementTree(svg).write(output_path, encoding="utf-8", xml_declaration=True)


def write_matched_piece_comparison_from_diagnostics(
    candidate_svg: Path,
    reference_svg: Path,
    diagnostics: tuple[CenterlinePieceDiagnostic, ...],
    output_path: Path,
) -> None:
    """Write overlays only for diagnostics currently marked as matched."""

    matched = [diagnostic for diagnostic in diagnostics if diagnostic.matched]
    if not matched:
        raise ValueError("No matched diagnostics available for matched piece comparison.")

    columns = 3
    panel_width = 250.0
    panel_height = 190.0
    gap = 22.0
    margin = 28.0
    label_height = 28.0
    rows = (len(matched) + columns - 1) // columns
    width = margin * 2 + panel_width * columns + gap * (columns - 1)
    height = margin * 2 + (panel_height + label_height) * rows + gap * (rows - 1) + 76

    ElementTree.register_namespace("", SVG_NS)
    svg = ElementTree.Element(
        f"{{{SVG_NS}}}svg",
        {
            "width": f"{width:.0f}",
            "height": f"{height:.0f}",
            "viewBox": f"0 0 {width:.0f} {height:.0f}",
            "version": "1.1",
        },
    )
    ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}rect",
        {"x": "0", "y": "0", "width": f"{width:.0f}", "height": f"{height:.0f}", "fill": "#ffffff"},
    )
    _add_label(svg, "Matched Piece Overlay", margin, 32.0)
    subtitle = ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}text",
        {
            "x": f"{margin:.3f}",
            "y": "56",
            "font-family": "Arial, sans-serif",
            "font-size": "12",
            "fill": "#475467",
        },
    )
    subtitle.text = f"matched diagnostics={len(matched)}; black=candidate, red=reference"

    for match_index, diagnostic in enumerate(matched):
        if diagnostic.candidate_geometry is None or diagnostic.reference_geometry is None:
            continue
        row = match_index // columns
        column = match_index % columns
        x = margin + column * (panel_width + gap)
        y = 82.0 + row * (panel_height + label_height + gap)
        ElementTree.SubElement(
            svg,
            f"{{{SVG_NS}}}rect",
            {
                "x": f"{x:.3f}",
                "y": f"{y:.3f}",
                "width": f"{panel_width:.3f}",
                "height": f"{panel_height:.3f}",
                "fill": "#ffffff",
                "stroke": "#d0d5dd",
                "stroke-width": "1",
            },
        )
        caption = ElementTree.SubElement(
            svg,
            f"{{{SVG_NS}}}text",
            {
                "x": f"{x:.3f}",
                "y": f"{y - 8:.3f}",
                "font-family": "Arial, sans-serif",
                "font-size": "12",
                "fill": "#101828",
            },
        )
        score_text = "n/a" if diagnostic.score is None else f"{float(diagnostic.score):.3f}"
        caption.text = (
            f"R{diagnostic.reference_index} source={diagnostic.source or 'n/a'} "
            f"score={score_text}"
        )
        _append_path_geometry_panel(
            svg,
            diagnostic.candidate_geometry,
            x,
            y,
            panel_width,
            panel_height,
            stroke="#111111",
            opacity="0.62",
        )
        _append_path_geometry_panel(
            svg,
            diagnostic.reference_geometry,
            x,
            y,
            panel_width,
            panel_height,
            stroke="#d92d20",
            opacity="0.72",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ElementTree.ElementTree(svg).write(output_path, encoding="utf-8", xml_declaration=True)


@dataclass(frozen=True)
class _FailedPiecePanel:
    failure_type: str
    candidate_index: int | None
    reference_index: int | None
    max_deviation_mm: float | None
    p95_deviation_mm: float | None
    bbox_iou: float | None


def _failed_piece_caption(panel: _FailedPiecePanel) -> str:
    candidate = "" if panel.candidate_index is None else f"C{panel.candidate_index}"
    reference = "" if panel.reference_index is None else f"R{panel.reference_index}"
    if panel.failure_type == "over-tolerance":
        max_deviation = (
            "n/a" if panel.max_deviation_mm is None else f"{panel.max_deviation_mm:.3f}mm"
        )
        p95_deviation = (
            "n/a" if panel.p95_deviation_mm is None else f"{panel.p95_deviation_mm:.3f}mm"
        )
        return (
            f"{panel.failure_type} {candidate} vs {reference} "
            f"max {max_deviation} p95 {p95_deviation}"
        )
    if panel.failure_type == "unmatched-reference":
        return f"{panel.failure_type} {reference}"
    if panel.failure_type == "unmatched-candidate":
        return f"{panel.failure_type} {candidate}"
    return f"{panel.failure_type} {candidate} {reference}".strip()


def _append_geometry_panel(
    target_svg: ElementTree.Element,
    source_svg: Path,
    source_bbox: tuple[float, float, float, float],
    panel_x: float,
    panel_y: float,
    panel_width: float,
    panel_height: float,
    *,
    stroke: str,
    opacity: str = "1",
) -> None:
    padding = 18.0
    transform = _fit_transform(
        source_bbox,
        panel_x + padding,
        panel_y + padding,
        panel_width - padding * 2,
        panel_height - padding * 2,
    )
    group = ElementTree.SubElement(
        target_svg,
        f"{{{SVG_NS}}}g",
        {
            "transform": transform,
            "fill": "none",
            "stroke": stroke,
            "stroke-width": "1.15",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "vector-effect": "non-scaling-stroke",
            "opacity": opacity,
        },
    )
    for element in ElementTree.parse(source_svg).getroot().iter():
        if _local_name(element.tag) not in _REVIEW_TAGS:
            continue
        clone = deepcopy(element)
        clone.attrib.pop("class", None)
        clone.attrib.pop("style", None)
        clone.attrib["fill"] = "none"
        clone.attrib["stroke"] = stroke
        clone.attrib["stroke-width"] = "1.15"
        clone.attrib["vector-effect"] = "non-scaling-stroke"
        group.append(clone)


def _append_single_element_panel(
    target_svg: ElementTree.Element,
    element: ElementTree.Element,
    source_bbox: tuple[float, float, float, float],
    panel_x: float,
    panel_y: float,
    panel_width: float,
    panel_height: float,
    *,
    stroke: str,
    opacity: str,
) -> None:
    padding = 20.0
    transform = _fit_transform(
        source_bbox,
        panel_x + padding,
        panel_y + padding,
        panel_width - padding * 2,
        panel_height - padding * 2,
    )
    group = ElementTree.SubElement(
        target_svg,
        f"{{{SVG_NS}}}g",
        {
            "transform": transform,
            "fill": "none",
            "stroke": stroke,
            "stroke-width": "1.15",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "vector-effect": "non-scaling-stroke",
            "opacity": opacity,
        },
    )
    clone = deepcopy(element)
    clone.attrib.pop("class", None)
    clone.attrib.pop("style", None)
    clone.attrib["fill"] = "none"
    clone.attrib["stroke"] = stroke
    clone.attrib["stroke-width"] = "1.15"
    clone.attrib["vector-effect"] = "non-scaling-stroke"
    group.append(clone)


def _append_path_geometry_panel(
    target_svg: ElementTree.Element,
    geometry: PathGeometry,
    panel_x: float,
    panel_y: float,
    panel_width: float,
    panel_height: float,
    *,
    stroke: str,
    opacity: str,
) -> None:
    padding = 20.0
    transform = _fit_transform(
        geometry.bounds,
        panel_x + padding,
        panel_y + padding,
        panel_width - padding * 2,
        panel_height - padding * 2,
    )
    group = ElementTree.SubElement(
        target_svg,
        f"{{{SVG_NS}}}g",
        {
            "transform": transform,
            "fill": "none",
            "stroke": stroke,
            "stroke-width": "1.15",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "vector-effect": "non-scaling-stroke",
            "opacity": opacity,
        },
    )
    ElementTree.SubElement(
        group,
        f"{{{SVG_NS}}}path",
        {
            "d": path_to_svg_d(geometry),
            "fill": "none",
            "stroke": stroke,
            "stroke-width": "1.15",
            "vector-effect": "non-scaling-stroke",
        },
    )


def _fit_transform(
    bbox: tuple[float, float, float, float],
    x: float,
    y: float,
    width: float,
    height: float,
) -> str:
    xmin, ymin, xmax, ymax = bbox
    source_width = xmax - xmin
    source_height = ymax - ymin
    if source_width <= 0 or source_height <= 0:
        raise ValueError("Cannot fit an empty SVG bbox.")
    scale = min(width / source_width, height / source_height)
    x_offset = x + (width - source_width * scale) / 2
    y_offset = y + (height - source_height * scale) / 2
    e = x_offset - xmin * scale
    f = y_offset - ymin * scale
    return f"matrix({scale:.8f} 0 0 {scale:.8f} {e:.8f} {f:.8f})"


def _add_label(svg: ElementTree.Element, text: str, x: float, y: float) -> None:
    label = ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}text",
        {
            "x": f"{x:.3f}",
            "y": f"{y:.3f}",
            "font-family": "Arial, sans-serif",
            "font-size": "18",
            "font-weight": "700",
            "fill": "#101828",
        },
    )
    label.text = text


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _piece_elements_by_index(svg_path: Path) -> dict[int, ElementTree.Element]:
    elements: dict[int, ElementTree.Element] = {}
    piece_index = 0
    for element in ElementTree.parse(svg_path).getroot().iter():
        if _local_name(element.tag) not in {"path", "rect", "polygon"}:
            continue
        piece_index += 1
        elements[piece_index] = element
    return elements
