from argparse import ArgumentParser, Namespace
from pathlib import Path, PurePath
from posixpath import normcase
from shlex import join
from shutil import which
from sys import stdout
from typing import AsyncIterator, Iterable, Iterator

from std2.asyncio.subprocess import call

from ...run import run_main
from ..fzf import run_fzf
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


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")
    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()

    if preview := args.preview:
        preview_path = Path(preview).read_text().rstrip("\0")
        await _git_show_blame(PurePath(preview_path))

    elif execute := args.execute:

        def cont() -> Iterator[str]:
            for path in Path(execute).read_text().split("\0"):
                yield path

        stdout.write(join(cont()))

    else:
        paths = [el async for el in _git_ls_files()]
        await _fzf_lhs(paths)

    return 0


run_main(main())
