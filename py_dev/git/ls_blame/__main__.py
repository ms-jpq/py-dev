from argparse import ArgumentParser
from pathlib import PurePath
from posixpath import normcase
from shlex import join
from shutil import which
from sys import stdout
from typing import AsyncIterator, Iterable

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..spec_parse import SPEC, Mode, spec_parse


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
    await run_fzf(stdin)


async def _git_show_blame(path: PurePath) -> None:
    proc = await call(
        "git",
        "blame",
        "-w",
        "--",
        path,
        capture_stderr=False,
    )
    if delta := which("delta"):
        await call(
            delta,
            stdin=proc.out,
            capture_stdout=False,
            capture_stderr=False,
        )
    else:
        stdout.buffer.write(proc.out)


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    return spec_parse(parser)


async def main() -> int:
    mode, lines, _ = _parse_args()

    if mode is Mode.preview:
        preview_path, *_ = lines
        await _git_show_blame(PurePath(preview_path))

    elif mode is Mode.execute:
        stdout.write(join(lines))

    elif mode is Mode.normal:
        paths = [el async for el in _git_ls_files()]
        await _fzf_lhs(paths)

    else:
        never(mode)

    return 0


run_main(main())
