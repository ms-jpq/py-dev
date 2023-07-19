from contextlib import suppress
from os.path import normcase
from pathlib import PurePath
from typing import Optional, cast, no_type_check

from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexer import Lexer
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.lexers.special import TextLexer
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound

from .consts import DEFAULT_FORMATTER, DEFAULT_STYLE


@no_type_check
def _get_lexer(filename: Optional[PurePath], text: str) -> Lexer:
    if filename:
        with suppress(ClassNotFound):
            return get_lexer_for_filename(normcase(filename.name))

    with suppress(ClassNotFound):
        return guess_lexer(text)

    return TextLexer()


def pprn(format: str, theme: str, filename: Optional[PurePath], text: str) -> str:
    style = get_style_by_name(theme)
    formatter = get_formatter_by_name(format, style=style)

    lexer = _get_lexer(filename, text)
    pretty = highlight(text, lexer=lexer, formatter=formatter)
    return cast(str, pretty)


def pprn_basic(filename: Optional[PurePath], text: str) -> str:
    return pprn(
        format=DEFAULT_FORMATTER, theme=DEFAULT_STYLE, filename=filename, text=text
    )
