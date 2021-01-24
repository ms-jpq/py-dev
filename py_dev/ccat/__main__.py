from argparse import ArgumentParser, Namespace
from pathlib import Path
from sys import stdin
from typing import Optional

from pygments.formatters._mapping import FORMATTERS
from pygments.styles import get_all_styles

from ..run import run_main
from .consts import DEFAULT_FORMATTER, DEFAULT_STYLE
from .pprn import pprn


def _arg_parse() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("name", nargs="?")
    parser.add_argument("-", dest="use_stdin", action="store_true")

    themes = sorted(get_all_styles())
    parser.add_argument("-t", "--theme", choices=themes, default=DEFAULT_STYLE)

    formatters = sorted(
        name for _, _, names, *_ in FORMATTERS.values() for name in names
    )
    parser.add_argument(
        "-f", "--formatter", choices=formatters, default=DEFAULT_FORMATTER
    )

    return parser.parse_args()


def _slurp(name: Optional[str], use_stdin: bool) -> str:
    if use_stdin or name is None:
        return stdin.read()
    else:
        return Path(name).read_text()


def main() -> None:
    args = _arg_parse()
    text = _slurp(args.name, args.use_stdin)
    pretty = pprn(
        format=args.formatter, theme=args.theme, filename=args.name, text=text
    )
    print(pretty, end="")


run_main(main)
