from argparse import ArgumentParser, Namespace
from pathlib import Path, PurePath
from shlex import join
from sys import stdout
from typing import Iterator

from std2.asyncio.subprocess import call

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import spec_parse


async def _git_file_diff(older: str, newer: str) -> bytes:
    proc = await call(
        "git",
        "diff",
        "--name-status",
        "-z",
        older,
        newer,
        capture_stderr=False,
    )

    def cont() -> Iterator[bytes]:
        it = iter(proc.out.rstrip(b"\0").split(b"\0"))
        while True:
            if status := next(it, None):
                if status[:1] == b"R":
                    next(it)
                yield status + b" " + next(it)
            else:
                break

    return b"\0".join(cont())


async def _git_diff_single(
    unified: int, older: str, newer: str, path: PurePath
) -> bytes:
    proc = await call(
        "git",
        "diff",
        f"--unified={unified}",
        older,
        newer,
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out


async def _fzf_lhs(unified: int, older: str, newer: str, files: bytes) -> None:
    await run_fzf(
        files,
        p_args=(older, newer, f"--unified={unified}", "--preview={f}"),
        e_args=(older, newer, f"--unified={unified}", "--execute={+f}"),
    )


async def _fzf_rhs(unified: int, older: str, newer: str, path: PurePath) -> None:
    diff = await _git_diff_single(unified, older=older, newer=newer, path=path)
    await pretty_diff(diff, path=path)


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("older")
    parser.add_argument("newer", nargs="?", default="HEAD")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()
    older, newer = args.older, args.newer

    if preview := args.preview:
        _, _, path = Path(preview).read_text().rstrip("\0").partition(" ")
        await _fzf_rhs(args.unified, older=older, newer=newer, path=PurePath(path))

    elif execute := args.execute:

        def cont() -> Iterator[str]:
            for line in Path(execute).read_text().split("\0"):
                _, _, path = line.partition(" ")
                yield path

        stdout.write(join(cont()))

    else:
        files = await _git_file_diff(older=older, newer=newer)
        await _fzf_lhs(args.unified, older=older, newer=newer, files=files)

    return 0


run_main(main())
