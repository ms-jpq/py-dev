from argparse import ArgumentParser
from pathlib import PurePath
from shlex import join
from sys import stdout
from typing import Iterator, Sequence

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import SPEC, Mode, spec_parse


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


async def _fzf_rhs(unified: int, older: str, newer: str, path: PurePath) -> None:
    diff = await _git_diff_single(unified, older=older, newer=newer, path=path)
    await pretty_diff(diff, path=path)


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    parser.add_argument("older")
    parser.add_argument("newer", nargs="?", default="HEAD")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


def _parse_lines(lines: Sequence[str]) -> Iterator[str]:
    for line in lines:
        _, _, path = line.partition(" ")
        yield path


async def main() -> int:
    mode, lines, args = _parse_args()
    older, newer = args.older, args.newer

    if mode is Mode.preview:
        path, *_ = _parse_lines(lines)
        await _fzf_rhs(args.unified, older=older, newer=newer, path=PurePath(path))

    elif mode is Mode.execute:
        stdout.write(join(_parse_lines(lines)))

    elif mode is Mode.normal:
        files = await _git_file_diff(older=older, newer=newer)
        await run_fzf(files)

    else:
        never(mode)

    return 0


run_main(main())
