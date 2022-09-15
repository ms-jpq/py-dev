from argparse import ArgumentParser
from pathlib import PurePath
from shlex import join
from sys import stdout
from typing import NoReturn

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import SPEC, Mode, spec_parse


async def _git_commit_files(commit: str) -> bytes:
    proc = await call(
        "git",
        "show",
        "--name-only",
        "--relative",
        "--pretty=format:",
        "-z",
        commit,
        capture_stderr=False,
    )
    return proc.stdout


async def _fzf_rhs(commit: str, path: PurePath) -> None:
    proc = await call(
        "git",
        "show",
        "--relative",
        commit,
        "--",
        path,
        capture_stderr=False,
    )
    diff = proc.stdout

    await pretty_diff(diff, path=path)


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    parser.add_argument("commit")
    return spec_parse(parser)


async def _main() -> int:
    mode, lines, args = _parse_args()

    if mode is Mode.preview:
        line, *_ = map(PurePath, lines)
        await _fzf_rhs(args.commit, path=line)

    elif mode is Mode.execute:
        stdout.write(join(lines))

    elif mode is Mode.normal:
        files = await _git_commit_files(args.commit)
        await run_fzf(files)

    else:
        never(mode)

    return 0


def main() -> NoReturn:
    run_main(_main())
