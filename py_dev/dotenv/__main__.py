from argparse import ArgumentParser, Namespace
from configparser import ConfigParser, ParsingError
from itertools import chain
from os import linesep
from pathlib import Path
from string import ascii_letters, digits
from sys import stderr, stdin, stdout
from uuid import uuid4

from ..log import log
from ..run import run_main


class _Parser(ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr


def _arg_parse() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path.cwd() / ".env")
    parser.add_argument("-", "--stdin", action="store_true")
    args = parser.parse_args()
    return args


async def main() -> int:
    args = _arg_parse()
    text = stdin.read() if args.stdin else Path(args.path).read_text()
    lines = "".join(chain((f"[{uuid4()}]", linesep), text))
    parser = _Parser(allow_no_value=True)

    try:
        parser.read_string(lines)
    except ParsingError as e:
        log.critical("%s", e)
        return 1
    else:
        legal = {*ascii_letters, digits, "_"}
        for section in parser.values():
            for key, val in section.items():
                if {*key} < legal:
                    line = f"{key}={val}"
                    stderr.write(line)
                    stderr.write(linesep)
                    stdout.write(f"export {line}")
                    stdout.write(linesep)

        return 0


run_main(main())
