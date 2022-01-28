from argparse import ArgumentParser, Namespace
from os import linesep
from pathlib import Path
from typing import AsyncIterator, Iterable, Iterator, Tuple

from std2.asyncio.subprocess import call

from ...run import run_main
from ..fzf import run_fzf
from ..ops import git_show_many, pprn
from ..spec_parse import spec_parse


async def _git_dead_files() -> AsyncIterator[Tuple[str, str, str]]:
    proc = await call(
        "git",
        "log",
        "--diff-filter=D",
        "--name-only",
        "--relative-date",
        "--color=always",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset",
        capture_stderr=False,
    )
    for commit in proc.out.decode().strip("\0").split("\0"):
        meta, *paths = commit.split(linesep)
        sha, _, date = meta.partition(" ")
        for path in paths:
            if path:
                yield f"{sha}~", date, path


async def _fzf_lhs(paths: Iterable[Tuple[str, str, str]]) -> None:
    lines = (f"{sha}{linesep}{date}{linesep}{path}" for sha, date, path in paths)
    stdin = "\0".join(lines).encode()
    await run_fzf(stdin, p_args=("--preview={f}",), e_args=("--execute={+f}",))


async def _fzf_rhs(sha: str, path: str) -> None:
    proc = await call(
        "git",
        "show",
        f"{sha}:{path}",
        capture_stderr=False,
    )
    await pprn(proc.out, path=path)


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
        sha, _, path = preview.split(linesep)
        await _fzf_rhs(sha, path=path)
    elif args.execute:
        lines = Path(args.execute).read_text().rstrip("\0").split("\0")

        def cont() -> Iterator[Tuple[str, str]]:
            for line in lines:
                sha, _, path = line.split(linesep)
                yield sha, path

        await git_show_many(cont())
    else:
        paths = [path async for path in _git_dead_files()]
        await _fzf_lhs(paths)

    return 0


run_main(main())
