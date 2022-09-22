from argparse import ArgumentParser
from pathlib import PurePath
from shlex import join
from sys import stdout
from typing import AsyncIterator, Iterable, Iterator, NoReturn, Sequence, Tuple

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_commit
from ..spec_parse import SPEC, Mode, spec_parse


async def _git_ls_commits(paths: Sequence[PurePath]) -> AsyncIterator[Tuple[str, str]]:
    proc = await call(
        "git",
        "log",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        "--",
        *paths,
        capture_stderr=False,
    )
    for commit in proc.stdout.decode().strip("\0").split("\0"):
        sha, _, date = commit.partition(" ")
        yield sha, date


async def _fzf_lhs(commits: Iterable[Tuple[str, str]]) -> None:
    stdin = "\0".join(f"{sha} {date}" for sha, date in commits).encode()
    await run_fzf(stdin)


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    parser.add_argument("-u", "--unified", type=int, default=3)
    parser.add_argument("paths", nargs="*", type=PurePath)
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
        commits = [el async for el in _git_ls_commits(args.paths)]
        await _fzf_lhs(commits)

    else:
        never(mode)

    return 0


def main() -> NoReturn:
    run_main(_main())
