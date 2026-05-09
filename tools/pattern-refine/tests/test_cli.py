from pattern_refine.cli import build_parser


def test_cli_parser_accepts_version_flag() -> None:
    parser = build_parser()

    args = parser.parse_args(["--version"])

    assert args.version is True
