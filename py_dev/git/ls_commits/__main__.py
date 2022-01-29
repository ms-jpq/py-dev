from argparse import ArgumentParser, Namespace
from asyncio import gather
from os import linesep
from pathlib import Path
from sys import stdout
from typing import AsyncIterator, Iterable, Tuple

from std2.asyncio.subprocess import call
from std2.shutil import hr, hr_print

from ...log import log
from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import spec_parse


async def _git_ls_commits() -> AsyncIterator[Tuple[str, str]]:
    proc = await call(
        "git",
        "log",
        "--relative-date",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        capture_stderr=False,
    )
    for commit in proc.out.decode().strip("\0").split("\0"):
        sha, _, date = commit.partition(" ")
        yield sha, date


async def _fzf_lhs(commits: Iterable[Tuple[str, str]]) -> None:
    stdin = "\0".join(f"{sha} {date}" for sha, date in commits).encode()
    await run_fzf(stdin, p_args=("--preview={f}",), e_args=("--execute={+f}",))


async def _git_show_commit(sha: str) -> None:
    c1 = call(
        "git",
        "show",
        "--submodule",
        "--no-patch",
        "--color",
        sha,
        capture_stderr=False,
    )
    c2 = call(
        "git",
        "diff-tree",
        "--no-commit-id",
        "--find-renames",
        "--name-status",
        "-r",
        sha,
        capture_stderr=False,
    )
    c3 = call(
        "git",
        "show",
        "--submodule",
        "--pretty=format:",
        sha,
        capture_stderr=False,
    )

    p1, p2, p3 = await gather(c1, c2, c3)

    def cont() -> Iterable[str]:
        yield p1.out.decode()
        yield linesep
        yield hr()
        yield linesep
        yield p2.out.decode()
        yield hr()
        yield linesep

    stdout.writelines(cont())
    stdout.flush()

    await pretty_diff(p3.out, path=None)


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
        sha, _, _ = preview.partition(" ")
        await _git_show_commit(sha)
    elif args.execute:
        execute = Path(args.execute).read_text().rstrip("\0")

        def cont() -> Iterable[str]:
            for line in execute.split("\0"):
                sha, _, _ = line.partition(" ")
                yield sha

        log.info("%s", hr_print(linesep.join(cont())))
    else:
        commits = [el async for el in _git_ls_commits()]
        await _fzf_lhs(commits)

    return 0


run_main(main())
