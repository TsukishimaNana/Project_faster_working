"""Debug visualization SVG helpers."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from pattern_refine.deviation import SimplificationDeviationReport
from pattern_refine.features import FeatureReport
from pattern_refine.geometry import PathGeometry
from pattern_refine.vectorize import SVG_NS, path_to_svg_d


def write_overlay_svg(
    candidate_geometries: tuple[PathGeometry, ...],
    cleaned_geometries: tuple[PathGeometry, ...],
    svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
) -> None:
    """Write an SVG overlay comparing high-fidelity candidates and filtered geometry."""

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
    _append_group(
        svg,
        candidate_geometries,
        group_id="high-fidelity-candidate",
        stroke="#00bcd4",
        stroke_width="0.08",
        opacity="0.65",
    )
    _append_group(
        svg,
        cleaned_geometries,
        group_id="filtered-cleaned",
        stroke="#f44336",
        stroke_width="0.12",
        opacity="0.95",
    )
    ElementTree.ElementTree(svg).write(svg_path, encoding="utf-8", xml_declaration=True)


def write_feature_overlay_svg(
    geometries: tuple[PathGeometry, ...],
    report: FeatureReport,
    svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
) -> None:
    """Write cleaned geometry with classified protection features overlaid."""

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
    _append_group(
        svg,
        geometries,
        group_id="cleaned-geometry",
        stroke="#424242",
        stroke_width="0.1",
        opacity="0.75",
    )
    feature_group = ElementTree.SubElement(svg, f"{{{SVG_NS}}}g", {"id": "features"})
    for index, feature in enumerate(report.features, start=1):
        color = _feature_color(feature.kind)
        ElementTree.SubElement(
            feature_group,
            f"{{{SVG_NS}}}circle",
            {
                "id": f"feature-{index:04d}",
                "cx": f"{feature.position.x_mm:.6f}",
                "cy": f"{feature.position.y_mm:.6f}",
                "r": "0.9",
                "fill": color,
                "fill-opacity": "0.85",
            },
        )
    ElementTree.ElementTree(svg).write(svg_path, encoding="utf-8", xml_declaration=True)


def _feature_color(kind: str) -> str:
    if kind == "right_angle_candidate":
        return "#d32f2f"
    if kind == "corner_candidate":
        return "#ff9800"
    if kind == "straight_edge_candidate":
        return "#1976d2"
    if kind == "short_alignment_mark_candidate":
        return "#7b1fa2"
    if kind == "notch_candidate":
        return "#c2185b"
    if kind == "triangle_mark_candidate":
        return "#00897b"
    return "#212121"


def write_deviation_overlay_svg(
    candidate_geometries: tuple[PathGeometry, ...],
    cleaned_geometries: tuple[PathGeometry, ...],
    report: SimplificationDeviationReport,
    svg_path: Path,
    *,
    page_width_mm: float,
    page_height_mm: float,
) -> None:
    """Write an overlay where simplified paths are colored by deviation acceptance."""

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
    _append_group(
        svg,
        candidate_geometries,
        group_id="high-fidelity-candidate",
        stroke="#9e9e9e",
        stroke_width="0.06",
        opacity="0.35",
    )
    accepted: list[PathGeometry] = []
    rejected: list[PathGeometry] = []
    for path_report in report.path_deviations:
        if not path_report.matched or path_report.simplified_index is None:
            continue
        geometry = cleaned_geometries[path_report.simplified_index - 1]
        if path_report.accepted:
            accepted.append(geometry)
        else:
            rejected.append(geometry)
    _append_group(
        svg,
        tuple(accepted),
        group_id="accepted-cleaned",
        stroke="#2e7d32",
        stroke_width="0.14",
        opacity="0.95",
    )
    _append_group(
        svg,
        tuple(rejected),
        group_id="rejected-cleaned",
        stroke="#d32f2f",
        stroke_width="0.18",
        opacity="0.95",
    )
    ElementTree.ElementTree(svg).write(svg_path, encoding="utf-8", xml_declaration=True)


def _append_group(
    svg: ElementTree.Element,
    geometries: tuple[PathGeometry, ...],
    *,
    group_id: str,
    stroke: str,
    stroke_width: str,
    opacity: str,
) -> None:
    group = ElementTree.SubElement(
        svg,
        f"{{{SVG_NS}}}g",
        {
            "id": group_id,
            "fill": "none",
            "stroke": stroke,
            "stroke-width": stroke_width,
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "opacity": opacity,
        },
    )
    for index, geometry in enumerate(geometries, start=1):
        ElementTree.SubElement(
            group,
            f"{{{SVG_NS}}}path",
            {
                "id": f"{group_id}-{index:04d}",
                "d": path_to_svg_d(geometry),
            },
        )
