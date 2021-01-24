from argparse import ArgumentParser, Namespace
from enum import Enum, auto
from pathlib import Path
from sys import stderr, stdin
from typing import Callable, Mapping, Tuple

from ..run import run_main
from .md_txt import md_2_txt, txt_2_md


class _Formats(Enum):
    md = auto()
    txt = auto()


_CONVERTERS: Mapping[Tuple[_Formats, _Formats], Callable[[str], str]] = {
    (_Formats.md, _Formats.txt): md_2_txt,
    (_Formats.txt, _Formats.md): txt_2_md,
}


def _parse_args() -> Namespace:
    fmts = tuple(fmt.name for fmt in _Formats)
    parser = ArgumentParser()
    parser.add_argument("src_fmt", choices=fmts)
    parser.add_argument("dest_fmt", choices=fmts)

    parser.add_argument("-", "--stdin", action="store_true")
    parser.add_argument("src", nargs="?")

    args = parser.parse_args()
    if not args.stdin and not args.src:
        parser.print_help()
        exit(1)
    else:
        return args


def main() -> None:
    args = _parse_args()
    f_src, f_dest = _Formats[args.src_fmt], _Formats[args.dest_fmt]
    conv = _CONVERTERS.get((f_src, f_dest))
    if not conv:
        exit(1)
    else:
        input = stdin.read() if args.stdin else Path(args.src).read_text()
        try:
            output = conv(input)
        except Exception as e:
            print(e, file=stderr)
        else:
            print(output, end="")


run_main(main)
