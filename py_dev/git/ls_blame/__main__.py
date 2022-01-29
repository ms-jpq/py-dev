from argparse import ArgumentParser, Namespace
from asyncio import gather
from os import linesep
from pathlib import Path, PurePath
from posixpath import normcase
from sys import stdout
from typing import AsyncIterator, Iterable, Tuple

from std2.asyncio.subprocess import call
from std2.shutil import hr

from ...log import log
from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import spec_parse


async def _git_ls_files() -> AsyncIterator[PurePath]:
    proc = await call(
        "git",
        "ls-files",
        "-z",
        capture_stderr=False,
    )
    for path in proc.out.decode().strip("\0").split("\0"):
        yield PurePath(path)


async def _fzf_lhs(paths: Iterable[PurePath]) -> None:
    stdin = "\0".join(map(normcase, paths)).encode()
    await run_fzf(stdin, p_args=("--preview={f}",), e_args=("--execute={+f}",))


async def _git_show_blame(paths: Iterable[PurePath]) -> None:
    for path in paths:
        await call(
            "git",
            "blame",
            "--",
            path,
            capture_stdout=False,
            capture_stderr=False,
        )


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")
    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()
    if args.preview:
        preview = Path(args.preview).read_text().rstrip("\0")
        paths = map(PurePath, preview.splitlines())
        await _git_show_blame(paths)
    elif args.execute:
        execute = Path(args.execute).read_text().rstrip("\0")
        paths = map(PurePath, execute.splitlines())
        await _git_show_blame(paths)
    else:
        paths = [el async for el in _git_ls_files()]
        await _fzf_lhs(paths)

    return 0


run_main(main())
