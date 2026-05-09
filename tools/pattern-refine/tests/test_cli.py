from pattern_refine.cli import build_parser


def test_cli_parser_accepts_version_flag() -> None:
    parser = build_parser()

    args = parser.parse_args(["--version"])

    assert args.version is True


def test_cli_parser_accepts_refine_command() -> None:
    parser = build_parser()

    args = parser.parse_args(["refine", "input.pdf", "--out", "out"])

    assert args.command == "refine"
    assert args.dpi == 600
    assert args.scale == "auto"
    assert args.overwrite is False
