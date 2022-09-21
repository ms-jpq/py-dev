from argparse import ArgumentParser
from pathlib import PurePath
from typing import NoReturn

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_file
from ..spec_parse import SPEC, Mode, spec_parse


async def _git_reflog() -> bytes:
    proc = await call(
        "git",
        "log",
        "--walk-reflogs",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        capture_stderr=False,
    )
    return proc.stdout


async def _fzf_lhs(reflog: bytes) -> None:
    await run_fzf(reflog)


async def _fzf_rhs(sha: str, path: PurePath) -> None:
    await pretty_file(sha, path)


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    parser.add_argument("path", type=PurePath)
    return spec_parse(parser)


async def _main() -> int:
    mode, lines, args = _parse_args()

    if mode is Mode.preview:
        line, *_ = lines
        sha, *_ = line
        await _fzf_rhs(sha, path=args.path)

    elif mode is Mode.execute:
        line, *_ = lines
        sha, *_ = line
        print(sha)

    elif mode is Mode.normal:
        reflog = await _git_reflog()
        await _fzf_lhs(reflog)

    else:
        never(mode)

    return 0


def main() -> NoReturn:
    run_main(_main())
