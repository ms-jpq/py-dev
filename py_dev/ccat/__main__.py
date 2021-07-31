from argparse import ArgumentParser, Namespace
from pathlib import Path
from sys import stdin

from pygments.formatters._mapping import FORMATTERS
from pygments.styles import get_all_styles

from ..run import run_main
from .consts import DEFAULT_FORMATTER, DEFAULT_STYLE
from .pprn import pprn


def _arg_parse() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("name", nargs="?")
    parser.add_argument("-", "--stdin", action="store_true")

    themes = sorted(get_all_styles())
    parser.add_argument("-t", "--theme", choices=themes, default=DEFAULT_STYLE)

    formatters = sorted(
        name for _, _, names, *_ in FORMATTERS.values() for name in names
    )
    parser.add_argument(
        "-f", "--formatter", choices=formatters, default=DEFAULT_FORMATTER
    )

    args = parser.parse_args()
    return args


async def main() -> int:
    args = _arg_parse()
    text = stdin.read() if args.stdin or not args.name else Path(args.name).read_text()
    pretty = pprn(
        format=args.formatter, theme=args.theme, filename=args.name, text=text
    )
    print(pretty, end="")
    return 0


run_main(main())
