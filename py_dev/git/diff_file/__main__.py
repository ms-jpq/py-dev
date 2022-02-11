from argparse import ArgumentParser
from itertools import chain
from os.path import normcase
from pathlib import PurePath
from shlex import join
from sys import stdout
from typing import Iterator, Sequence

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff, pretty_file
from ..spec_parse import SPEC, Mode, spec_parse


async def _git_file_log(path: PurePath) -> bytes:
    proc = await call(
        "git",
        "log",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out.strip(b"\0")


async def _git_show_diff(unified: int, sha: str, path: PurePath) -> bytes:
    proc = await call(
        "git",
        "diff",
        f"--unified={unified}",
        f"{sha}~",
        sha,
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out


async def _fzf_rhs(unified: int, sha: str, path: PurePath) -> None:
    if unified >= 0:
        diff = await _git_show_diff(unified, sha=sha, path=path)
        await pretty_diff(diff, path=path)
    else:
        await pretty_file(sha, path=path)


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    parser.add_argument("path", type=PurePath)

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


def _parse_lines(lines: Sequence[str]) -> Iterator[str]:
    for line in lines:
        sha, _, _ = line.partition(" ")
        yield sha


async def main() -> int:
    mode, lines, args = _parse_args()

    if mode is Mode.preview:
        sha, *_ = _parse_lines(lines)
        await _fzf_rhs(args.unified, sha=sha, path=args.path)

    elif mode is Mode.execute:
        stdout.write(join(chain(_parse_lines(lines), (normcase(args.path),))))

    elif mode is Mode.normal:
        commits = await _git_file_log(args.path)
        await run_fzf(commits)

    else:
        never(mode)

    return 0


run_main(main())
