from argparse import ArgumentParser
from itertools import chain, repeat
from shlex import join
from sys import stdout
from typing import Iterator, NoReturn, Sequence

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_commit
from ..spec_parse import SPEC, Mode, spec_parse


async def _ls_commits(regex: bool, search: str, *searches: str) -> bytes:
    proc = await call(
        "git",
        "log",
        "--all",
        "--relative",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        *(("--perl-regexp",) if regex else ("--fixed-strings",)),
        *chain.from_iterable(zip(repeat("--grep"), chain((search,), searches))),
        capture_stderr=False,
    )
    return proc.stdout.strip(b"\0")


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    parser.add_argument("search", nargs="+")

    parser.add_argument("-r", "--regex", action="store_true")
    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


def _parse_lines(lines: Sequence[str]) -> Iterator[str]:
    for line in lines:
        sha, _, _ = line.partition(" ")
        yield sha


async def _main() -> int:
    mode, lines, args = _parse_args()

    if mode is Mode.preview:
        sha, *_ = _parse_lines(lines)
        await pretty_commit(args.unified, sha=sha)

    elif mode is Mode.execute:
        stdout.write(join(_parse_lines(lines)))

    elif mode is Mode.normal:
        commits = await _ls_commits(args.regex, *args.search)
        await run_fzf(commits)

    else:
        never(mode)

    return 0


def main() -> NoReturn:
    run_main(_main())
