from argparse import ArgumentParser, Namespace
from sys import stdin
from typing import Optional
from pathlib import Path

from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.formatters._mapping import FORMATTERS
from pygments.lexer import Lexer
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.lexers.special import TextLexer
from pygments.styles import get_all_styles, get_style_by_name
from pygments.util import ClassNotFound


def _arg_parse() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("name", nargs="?")
    parser.add_argument("-", dest="use_stdin", action="store_true")

    themes = sorted(get_all_styles())
    parser.add_argument("-t", "--theme", choices=themes, default="friendly")

    formatters = sorted(
        name for _, _, names, *_ in FORMATTERS.values() for name in names
    )
    parser.add_argument("-f", "--formatter", choices=formatters, default="terminal16m")

    return parser.parse_args()


def _slurp(name: Optional[str], use_stdin: bool) -> str:
    if use_stdin or name is None:
        return stdin.read()
    else:
        return Path(name).read_text()

def _get_lexer(file_name: Optional[str], text: str) -> Lexer:
    try:
        return get_lexer_for_filename(file_name)
    except (ClassNotFound, TypeError):
        try:
            return guess_lexer(text)
        except ClassNotFound:
            return TextLexer()


def main() -> None:
    args = _arg_parse()
    text = _slurp(args.name, args.use_stdin)

    style = get_style_by_name(args.theme)
    formatter = get_formatter_by_name(args.formatter, style=style)

    lexer = _get_lexer(args.name, text)
    pretty = highlight(text, lexer=lexer, formatter=formatter)

    print(pretty, end="")


main()
