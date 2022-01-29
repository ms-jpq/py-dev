from argparse import ArgumentParser, Namespace
from os import linesep
from os.path import normcase
from pathlib import Path, PurePath
from shlex import join
from tempfile import mkdtemp
from typing import AsyncIterator, Iterable, Iterator, Tuple

from std2.asyncio.subprocess import call
from std2.shutil import hr

from ...log import log
from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_file
from ..spec_parse import spec_parse


async def _git_dead_files() -> AsyncIterator[Tuple[str, str, PurePath]]:
    proc = await call(
        "git",
        "log",
        "--diff-filter=D",
        "--name-only",
        "--relative-date",
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
    await run_fzf(stdin, p_args=("--preview={f}",), e_args=("--execute={+f}",))


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

    line = "\t" + join(("cd", normcase(tmp)))
    log.info("%s", hr(line))


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")
    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()

    if preview := args.preview:
        sha, _, path = Path(preview).read_text().rstrip("\0").split(linesep)
        await _fzf_rhs(sha, path=PurePath(path))

    elif execute := args.execute:

        def cont() -> Iterator[Tuple[str, PurePath]]:
            for line in Path(execute).read_text().rstrip("\0").split("\0"):
                sha, _, path = line.split(linesep)
                yield sha, PurePath(path)

        await _git_show_many(cont())

    else:
        paths = [path async for path in _git_dead_files()]
        await _fzf_lhs(paths)

    return 0


run_main(main())
