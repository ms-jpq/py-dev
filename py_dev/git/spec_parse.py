from argparse import ArgumentParser, Namespace
from enum import Enum, auto
from os import environ
from pathlib import Path
from typing import Sequence

from std2.string import removeprefix

EOF = "\04"
ARGV_ENV = "__PY_DEV_ARGV__"

EXECUTE_HEAD = "execute::"
PREVIEW_HEAD = "preview::"


class Mode(Enum):
    normal = auto()
    preview = auto()
    execute = auto()


SPEC = tuple[Mode, Sequence[str], Namespace]


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-c", dest="cmd", required=True)
    return parser.parse_args()


def spec_parse(parser: ArgumentParser) -> SPEC:
    if (fzf_argv := environ.get(ARGV_ENV)) is not None:
        cmd = _parse_args().cmd
        argv = fzf_argv.split(EOF) if fzf_argv else ()

        if cmd.startswith(PREVIEW_HEAD):
            mode = Mode.preview
            tmp = Path(removeprefix(cmd, PREVIEW_HEAD))
        elif cmd.startswith(EXECUTE_HEAD):
            mode = Mode.execute
            tmp = Path(removeprefix(cmd, EXECUTE_HEAD))
        else:
            assert False, cmd

        args = parser.parse_args(argv)
        lines = tmp.read_text().rstrip("\0").split("\0")
        return mode, lines, args
    else:
        return Mode.normal, (), parser.parse_args()
