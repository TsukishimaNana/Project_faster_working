"""Command line entrypoint for PatternRefine."""

from __future__ import annotations

import argparse
from pathlib import Path

from pattern_refine.pipeline import refine_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pattern-refine",
        description="Refine scanned BJD pattern PDFs into cleaned vector outputs.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the PatternRefine version.",
    )
    subparsers = parser.add_subparsers(dest="command")
    refine = subparsers.add_parser(
        "refine",
        help="Render a scanned PDF page and generate cleaned linework outputs.",
    )
    refine.add_argument("input_pdf", type=Path, help="Scanned pattern PDF to refine.")
    refine.add_argument("--out", type=Path, required=True, help="Directory for generated outputs.")
    refine.add_argument("--dpi", type=int, default=600, help="Render DPI. Defaults to 600.")
    refine.add_argument(
        "--scale",
        default="auto",
        choices=["auto"],
        help="Scale calibration mode. Only auto is supported in this MVP slice.",
    )
    refine.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing generated outputs.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        from pattern_refine import __version__

        print(__version__)
        return 0
    if args.command == "refine":
        result = refine_pdf(
            args.input_pdf,
            args.out,
            dpi=args.dpi,
            scale=args.scale,
            overwrite=args.overwrite,
        )
        print(f"Rendered page {result.page_number}: {result.render_path}")
        print(f"Extracted line image: {result.lines_path}")
        print(f"Wrote cleaned SVG: {result.cleaned_svg_path}")
        print(f"Parsed path geometry count: {len(result.geometries)}")
        print(
            "Page size: "
            f"{result.page_width_mm:.2f}mm x {result.page_height_mm:.2f}mm at {result.dpi} DPI"
        )
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
