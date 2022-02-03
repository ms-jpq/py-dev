from argparse import ArgumentParser, Namespace
from itertools import chain, repeat
from pathlib import Path
from shlex import join
from sys import stdout
from typing import Iterator

from std2.asyncio.subprocess import call

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_commit
from ..spec_parse import spec_parse


async def _ls_commits(regex: bool, search: str, *searches: str) -> bytes:
    proc = await call(
        "git",
        "log",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        *(() if regex else ("--fixed-strings",)),
        *chain.from_iterable(zip(repeat("-G"), chain((search,), searches))),
        capture_stderr=False,
    )
    return proc.out.strip(b"\0")


async def _fzf_lhs(unified: int, *search: str, commits: bytes) -> None:
    await run_fzf(
        commits,
        p_args=(*search, f"--unified={unified}", "--preview={f}"),
        e_args=(*search, f"--unified={unified}", "--execute={+f}"),
    )


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("search", nargs="+")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-r", "--regex", action="store_true")
    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()

    if preview := args.preview:
        sha, _, _ = Path(preview).read_text().rstrip("\0").partition(" ")
        await pretty_commit(args.unified, sha=sha)

    elif execute := args.execute:

        def cont() -> Iterator[str]:
            for line in Path(execute).read_text().split("\0"):
                sha, _, _ = line.partition(" ")
                yield sha

        stdout.write(join(cont()))

    else:
        commits = await _ls_commits(args.regex, *args.search)
        await _fzf_lhs(args.unified, *args.search, commits=commits)

    return 0


run_main(main())
