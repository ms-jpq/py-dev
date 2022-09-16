from argparse import ArgumentParser
from pathlib import PurePath
from shlex import join
from sys import stdout
from typing import Iterator, NoReturn, Sequence

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import SPEC, Mode, spec_parse


async def _git_file_diff(argv: Sequence[str]) -> bytes:
    proc = await call(
        "git",
        "diff",
        "--name-status",
        "--relative",
        "-z",
        *argv,
        capture_stderr=False,
    )

    def cont() -> Iterator[bytes]:
        it = iter(proc.stdout.rstrip(b"\0").split(b"\0"))
        while True:
            if status := next(it, None):
                if status[:1] == b"R":
                    next(it)
                yield status + b" " + next(it)
            else:
                break

    return b"\0".join(cont())


async def _git_diff_single(unified: int, path: PurePath, argv: Sequence[str]) -> bytes:
    proc = await call(
        "git",
        "diff",
        f"--unified={unified}",
        *argv,
        "--",
        path,
        capture_stderr=False,
    )
    return proc.stdout


async def _fzf_rhs(unified: int, argv: Sequence[str], path: PurePath) -> None:
    diff = await _git_diff_single(unified, path=path, argv=argv)
    await pretty_diff(diff, path=path)


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    parser.add_argument("-u", "--unified", type=int, default=3)
    parser.add_argument("lhs")
    parser.add_argument("rhs", nargs="...", default=())
    return spec_parse(parser)


def _parse_lines(lines: Sequence[str]) -> Iterator[str]:
    for line in lines:
        _, _, path = line.partition(" ")
        yield path


async def _main() -> int:
    mode, lines, args = _parse_args()
    argv = (args.lhs, *args.rhs)

    if mode is Mode.preview:
        path, *_ = _parse_lines(lines)
        await _fzf_rhs(args.unified, path=PurePath(path), argv=argv)

    elif mode is Mode.execute:
        stdout.write(join(_parse_lines(lines)))

    elif mode is Mode.normal:
        files = await _git_file_diff(argv)
        await run_fzf(files)

    else:
        never(mode)

    return 0


def main() -> NoReturn:
    run_main(_main())
