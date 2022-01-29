from argparse import ArgumentParser, Namespace
from os import linesep
from pathlib import Path
from typing import AsyncIterator, Iterable, Tuple

from std2.asyncio.subprocess import call
from std2.shutil import hr

from ...log import log
from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_commit
from ..spec_parse import spec_parse


async def _git_ls_commits() -> AsyncIterator[Tuple[str, str]]:
    proc = await call(
        "git",
        "log",
        "--find-renames",
        "--find-copies",
        "--relative-date",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        capture_stderr=False,
    )
    for commit in proc.out.decode().strip("\0").split("\0"):
        sha, _, date = commit.partition(" ")
        yield sha, date


async def _fzf_lhs(unified: int, commits: Iterable[Tuple[str, str]]) -> None:
    stdin = "\0".join(f"{sha} {date}" for sha, date in commits).encode()
    await run_fzf(
        stdin,
        p_args=(f"--unified={unified}", "--preview={f}"),
        e_args=(f"--unified={unified}", "--execute={+f}"),
    )


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()

    if preview := args.preview:
        sha, _, _ = Path(preview).read_text().rstrip("\0").partition(" ")
        await pretty_commit(args.unified, sha=sha)

    elif execute := args.execute:

        def cont() -> Iterable[str]:
            for line in Path(execute).read_text().rstrip("\0").split("\0"):
                sha, _, _ = line.partition(" ")
                yield sha

        log.info("%s", hr(linesep.join(cont())))

    else:
        commits = [el async for el in _git_ls_commits()]
        await _fzf_lhs(args.unified, commits=commits)

    return 0


run_main(main())
