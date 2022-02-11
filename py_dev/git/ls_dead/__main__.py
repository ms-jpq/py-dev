from argparse import ArgumentParser
from os import linesep
from os.path import normcase
from pathlib import Path, PurePath
from shlex import join
from tempfile import mkdtemp
from typing import AsyncIterator, Iterable, Iterator, Sequence, Tuple

from std2.asyncio.subprocess import call
from std2.shutil import hr
from std2.types import never

from ...log import log
from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_file
from ..spec_parse import SPEC, Mode, spec_parse


async def _git_dead_files() -> AsyncIterator[Tuple[str, str, PurePath]]:
    proc = await call(
        "git",
        "log",
        "--diff-filter=D",
        "--name-only",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset",
        capture_stderr=False,
    )
    for commit in proc.out.decode().strip("\0").split("\0"):
        meta, *paths = commit.split(linesep)
        sha, _, date = meta.partition(" ")
        for path in paths:
            if path:
                yield f"{sha}~", date, PurePath(path)


async def _fzf_lhs(paths: Iterable[Tuple[str, str, PurePath]]) -> None:
    lines = (
        f"{sha}{linesep}{date}{linesep}{normcase(path)}" for sha, date, path in paths
    )
    stdin = "\0".join(lines).encode()
    await run_fzf(stdin)


async def _fzf_rhs(sha: str, path: PurePath) -> None:
    await pretty_file(sha, path)


async def _git_show_many(it: Iterable[Tuple[str, PurePath]]) -> None:
    tmp = Path(mkdtemp())
    for sha, path in it:
        temp = tmp / path
        proc = await call(
            "git",
            "show",
            f"{sha}:{path}",
            capture_stderr=False,
        )
        temp.parent.mkdir(parents=True, exist_ok=True)
        temp.write_bytes(proc.out)

    log.info("%s", normcase(tmp))


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    return spec_parse(parser)


def _parse_lines(lines: Sequence[str]) -> Iterator[Tuple[str, PurePath]]:
    for line in lines:
        sha, _, path = line.splitlines()
        yield sha, PurePath(path)


async def main() -> int:
    mode, lines, _ = _parse_args()

    if mode is Mode.preview:
        (sha, path), *_ = _parse_lines(lines)
        await _fzf_rhs(sha, path=PurePath(path))

    elif mode is Mode.execute:
        await _git_show_many(_parse_lines(lines))

    elif mode is Mode.normal:
        paths = [path async for path in _git_dead_files()]
        await _fzf_lhs(paths)

    else:
        never(mode)

    return 0


run_main(main())
