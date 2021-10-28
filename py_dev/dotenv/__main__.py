from argparse import ArgumentParser, Namespace
from configparser import ConfigParser
from itertools import chain
from os import environ, linesep
from pathlib import Path
from shlex import split
from string import Template, ascii_letters, digits
from sys import stderr, stdin, stdout
from typing import Iterable, Iterator, Tuple
from uuid import uuid4

from ..run import run_main


def _parse(text: str) -> Iterator[Tuple[str, str]]:
    class _Parser(ConfigParser):
        def optionxform(self, optionstr: str) -> str:
            return optionstr

    lines = "".join(chain((f"[{uuid4()}]", linesep), text))
    parser = _Parser(allow_no_value=True, strict=False, interpolation=None)
    parser.read_string(lines)
    for section in parser.values():
        yield from section.items()


def _trans(stream: Iterable[Tuple[str, str]]) -> Iterator[Tuple[str, str]]:
    legal = {*ascii_letters, digits, "_"}
    seen = {**environ}
    for key, val in stream:
        if {*key} <= legal:
            if parts := split(val):
                part, *_ = parts
                tpl = Template(part)
                seen[key] = rhs = tpl.safe_substitute(seen)
                yield key, rhs


def _arg_parse() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path.cwd() / ".env")
    parser.add_argument("-", "--stdin", action="store_true")
    args = parser.parse_args()
    return args


async def main() -> int:
    args = _arg_parse()
    text = stdin.read() if args.stdin else Path(args.path).read_text()
    for lhs, rhs in _trans(_parse(text)):
        line = f"{lhs}={rhs}"
        stderr.write(line)
        stderr.write(linesep)
        stdout.write(f"export {line}")
        stdout.write(linesep)

    return 0


run_main(main())
