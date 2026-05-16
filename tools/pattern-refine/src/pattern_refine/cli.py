"""Command line entrypoint for PatternRefine."""

from __future__ import annotations

import argparse
from pathlib import Path

from pattern_refine.delivery import format_delivery_verification, verify_delivery
from pattern_refine.evaluate import (
    evaluate_svg_piece_acceptance,
    evaluate_svg_shape,
    evaluate_svg_structure,
    write_svg_evaluation_report,
    write_svg_piece_acceptance_report,
    write_svg_shape_evaluation_report,
)
from pattern_refine.compare import (
    write_failed_piece_comparison,
    write_piece_comparison,
    write_svg_comparison,
)
from pattern_refine.pipeline import refine_pdf
from pattern_refine.production_quality import (
    evaluate_production_quality,
    write_production_quality_report,
)


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
    evaluate = subparsers.add_parser(
        "evaluate",
        help="Compare a cleaned SVG candidate with a reference SVG.",
    )
    evaluate.add_argument("candidate_svg", type=Path, help="Generated cleaned SVG to evaluate.")
    evaluate.add_argument(
        "--reference",
        type=Path,
        required=True,
        help="Reference object-level SVG to compare against.",
    )
    evaluate.add_argument("--out", type=Path, required=True, help="Directory for the JSON report.")
    evaluate.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing evaluation report.",
    )
    verify_delivery_parser = subparsers.add_parser(
        "verify-delivery",
        help="Verify final SVG delivery readiness from status and piece acceptance reports.",
    )
    verify_delivery_parser.add_argument(
        "final_svg",
        type=Path,
        help="Final SVG customer delivery candidate.",
    )
    verify_delivery_parser.add_argument(
        "--status",
        type=Path,
        required=True,
        help="Final SVG status report JSON.",
    )
    verify_delivery_parser.add_argument(
        "--piece-report",
        type=Path,
        required=True,
        help="Piece acceptance report JSON.",
    )
    verify_delivery_parser.add_argument(
        "--production-quality-report",
        type=Path,
        required=True,
        help="Production cleanliness/topology report JSON.",
    )
    production_quality_parser = subparsers.add_parser(
        "production-quality",
        help="Evaluate final SVG production cleanliness/topology.",
    )
    production_quality_parser.add_argument("input_svg", type=Path, help="Final SVG to inspect.")
    production_quality_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Directory for the JSON report.",
    )
    production_quality_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing production quality report.",
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
        print(f"Wrote high-fidelity candidate SVG: {result.candidate_svg_path}")
        print(f"Wrote cleaned SVG: {result.cleaned_svg_path}")
        print(f"Wrote overlay SVG: {result.overlay_svg_path}")
        print(f"Wrote deviation overlay SVG: {result.deviation_overlay_svg_path}")
        print(f"Wrote feature overlay SVG: {result.feature_overlay_svg_path}")
        print(f"Wrote smoothed SVG: {result.smoothed_svg_path}")
        print(f"Wrote smoothing overlay SVG: {result.smoothing_overlay_svg_path}")
        print(f"Wrote semantic SVG: {result.semantic_svg_path}")
        print(f"Wrote final SVG: {result.final_svg_path}")
        print(f"Wrote refined PDF: {result.refined_pdf_path}")
        print(f"Wrote deviation report: {result.deviation_report_path}")
        print(f"Wrote scale report: {result.scale_report_path}")
        print(f"Wrote centerline report: {result.centerline_report_path}")
        print(f"Wrote classification report: {result.classification_report_path}")
        print(f"Wrote feature report: {result.feature_report_path}")
        print(f"Wrote smoothing report: {result.smoothing_report_path}")
        print(f"Wrote semantic report: {result.semantic_report_path}")
        print(f"Wrote final SVG status report: {result.final_status_report_path}")
        if result.piece_acceptance_report is not None:
            print(f"Wrote piece acceptance report: {result.piece_acceptance_report_path}")
        print(f"Wrote production quality report: {result.production_quality_report_path}")
        print(
            "Wrote scan vs reference-guided report: "
            f"{result.scan_vs_reference_guided_report_path}"
        )
        print(f"Wrote delivery overlay report: {result.delivery_overlay_report_path}")
        print(
            "Path geometry count: "
            f"candidate={len(result.candidate_geometries)}, "
            f"raw={len(result.raw_geometries)}, "
            f"selected={len(result.selected_candidate_geometries)}, "
            f"cleaned={len(result.geometries)}, "
            f"removed={result.classification_report.removed_count}"
        )
        if result.scale_report.detected:
            candidate = result.scale_report.selected_candidate
            assert candidate is not None
            print(
                "Scale marker: "
                f"{candidate.orientation} {candidate.length_px:.1f}px "
                f"for {candidate.expected_length_mm:.1f}mm "
                f"(error {candidate.relative_error:.1%})"
            )
            print(
                "Applied scale: "
                f"{result.scale_report.applied_source} "
                f"({result.scale_report.applied_pixel_to_mm:.8f}mm/px)"
            )
        else:
            print(f"Scale marker: not detected ({result.scale_report.failure_reason})")
        print(
            "Centerline geometry: "
            f"paths={result.centerline_report.path_count}, "
            f"closed={result.centerline_report.closed_path_count}, "
            f"stitched_delta={result.centerline_report.stitched_path_count_delta}"
        )
        print(f"Feature counts: {result.feature_report.feature_counts}")
        print(
            "Smoothing: "
            f"accepted_paths={result.smoothing_report.accepted_path_count}, "
            f"moved_points={result.smoothing_report.moved_point_count}, "
            f"max_deviation={result.smoothing_report.max_deviation_mm:.3f}mm"
        )
        print(
            "Semantic geometry: "
            f"paths={result.semantic_report.path_count}, "
            f"lines={result.semantic_report.line_count}, "
            f"rects={result.semantic_report.rect_count}"
        )
        print(
            "Semantic centerline candidates: "
            f"total={result.semantic_report.centerline_candidate_count}, "
            f"closed={result.semantic_report.centerline_closed_candidate_count}, "
            f"piece_candidates={result.semantic_report.centerline_piece_candidate_count}, "
            f"missing={result.semantic_report.centerline_missing_reference_count}, "
            f"applied={result.semantic_report.centerline_replacement_applied}"
        )
        print(
            "Final SVG status: "
            f"{result.final_status_report.result_state} "
            f"(delivery_ready={result.final_status_report.delivery_ready}, "
            f"source={result.final_status_report.final_geometry_source})"
        )
        if result.piece_acceptance_report is not None:
            print(
                "Piece acceptance: "
                f"{result.piece_acceptance_report.result_state} "
                f"(max={result.piece_acceptance_report.max_deviation_mm:.3f}mm, "
                f"tolerance={result.piece_acceptance_report.tolerance_mm:.3f}mm)"
            )
        print(
            "Deviation check: "
            f"{result.deviation_report.max_deviation_mm:.3f}mm max "
            f"(tolerance {result.deviation_report.tolerance_mm:.3f}mm)"
        )
        print(
            "Page size: "
            f"{result.page_width_mm:.2f}mm x {result.page_height_mm:.2f}mm at {result.dpi} DPI"
        )
        return 0
    if args.command == "evaluate":
        report_path = args.out / f"{args.candidate_svg.stem}.evaluation-report.json"
        shape_report_path = args.out / f"{args.candidate_svg.stem}.shape-evaluation-report.json"
        piece_acceptance_report_path = (
            args.out / f"{args.candidate_svg.stem}.piece-acceptance-report.json"
        )
        comparison_svg_path = args.out / f"{args.candidate_svg.stem}.comparison.svg"
        piece_comparison_svg_path = args.out / f"{args.candidate_svg.stem}.pieces-comparison.svg"
        failed_piece_comparison_svg_path = (
            args.out / f"{args.candidate_svg.stem}.failed-pieces-comparison.svg"
        )
        if report_path.exists() and not args.overwrite:
            raise FileExistsError(f"Output already exists, pass --overwrite to replace: {report_path}")
        if shape_report_path.exists() and not args.overwrite:
            raise FileExistsError(
                f"Output already exists, pass --overwrite to replace: {shape_report_path}"
            )
        if piece_acceptance_report_path.exists() and not args.overwrite:
            raise FileExistsError(
                "Output already exists, pass --overwrite to replace: "
                f"{piece_acceptance_report_path}"
            )
        if comparison_svg_path.exists() and not args.overwrite:
            raise FileExistsError(
                f"Output already exists, pass --overwrite to replace: {comparison_svg_path}"
            )
        if piece_comparison_svg_path.exists() and not args.overwrite:
            raise FileExistsError(
                f"Output already exists, pass --overwrite to replace: {piece_comparison_svg_path}"
            )
        if failed_piece_comparison_svg_path.exists() and not args.overwrite:
            raise FileExistsError(
                "Output already exists, pass --overwrite to replace: "
                f"{failed_piece_comparison_svg_path}"
            )
        report = evaluate_svg_structure(args.candidate_svg, args.reference)
        write_svg_evaluation_report(report, report_path)
        shape_report = evaluate_svg_shape(args.candidate_svg, args.reference)
        write_svg_shape_evaluation_report(shape_report, shape_report_path)
        piece_acceptance_report = evaluate_svg_piece_acceptance(args.candidate_svg, args.reference)
        write_svg_piece_acceptance_report(
            piece_acceptance_report,
            piece_acceptance_report_path,
        )
        write_svg_comparison(args.candidate_svg, args.reference, comparison_svg_path)
        write_piece_comparison(args.candidate_svg, args.reference, piece_comparison_svg_path)
        if not piece_acceptance_report.accepted:
            write_failed_piece_comparison(
                args.candidate_svg,
                args.reference,
                failed_piece_comparison_svg_path,
            )
        print(f"Wrote evaluation report: {report_path}")
        print(f"Wrote shape evaluation report: {shape_report_path}")
        print(f"Wrote piece acceptance report: {piece_acceptance_report_path}")
        print(f"Wrote comparison SVG: {comparison_svg_path}")
        print(f"Wrote piece comparison SVG: {piece_comparison_svg_path}")
        if not piece_acceptance_report.accepted:
            print(f"Wrote failed piece comparison SVG: {failed_piece_comparison_svg_path}")
        print(
            "Object counts: "
            f"candidate={report.candidate.object_count}, "
            f"reference={report.reference.object_count}, "
            f"delta={report.object_count_delta}"
        )
        print(f"Verdict: {report.verdict}")
        print(f"Shape verdict: {shape_report.verdict}")
        print(f"Piece acceptance state: {piece_acceptance_report.result_state}")
        return 0
    if args.command == "verify-delivery":
        result = verify_delivery(
            args.final_svg,
            status_report_path=args.status,
            piece_report_path=args.piece_report,
            production_quality_report_path=args.production_quality_report,
        )
        print(format_delivery_verification(result))
        return 0 if result.passed else 1
    if args.command == "production-quality":
        report_path = args.out / f"{args.input_svg.stem}.production-quality-report.json"
        if report_path.exists() and not args.overwrite:
            raise FileExistsError(f"Output already exists, pass --overwrite to replace: {report_path}")
        report = evaluate_production_quality(args.input_svg)
        write_production_quality_report(report, report_path)
        print(f"Wrote production quality report: {report_path}")
        print(f"Accepted: {report.accepted}")
        print(f"Manual review required: {report.manual_review_required}")
        print(f"Blockers: {list(report.blockers)}")
        return 0 if report.accepted else 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
