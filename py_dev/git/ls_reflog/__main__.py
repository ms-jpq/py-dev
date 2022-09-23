from argparse import ArgumentParser
from itertools import chain, repeat
from pathlib import PurePath
from re import compile
from typing import NoReturn, Optional, Sequence

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_commit, pretty_diff, pretty_file, print_argv
from ..spec_parse import SPEC, Mode, spec_parse


def _ref(ref: str) -> tuple[str, int]:
    m = compile(r"([^@]+)@\{(\d+)\}$").match(ref)
    assert m
    refname, pos = m.group(1, 2)
    return refname, int(pos)


async def _git_reflog(
    regex: bool, path: Optional[PurePath], search: Sequence[str]
) -> bytes:
    proc = await call(
        "git",
        "log",
        "--walk-reflogs",
        "--color",
        "--remove-empty",
        "--pretty=format:%x00%Cgreen%gD%Creset %Cblue%ad%Creset %s",
        *(("--perl-regexp",) if regex else ("--fixed-strings",)),
        *chain.from_iterable(zip(repeat("--grep-reflog"), search)),
        "--",
        *((path,) if path else ()),
        capture_stderr=False,
    )
    return proc.stdout.strip(b"\0")


async def _fzf_lhs(reflog: bytes) -> None:
    await run_fzf(reflog)


async def _git_show_diff(unified: int, ref: str, path: PurePath) -> None:
    re, cur = _ref(ref)
    proc = await call(
        "git",
        "diff",
        f"--unified={unified}",
        f"{re}@{{{cur}}}",
        f"{re}@{{{cur + 1}}}",
        "--",
        path,
        capture_stderr=False,
    )
    await pretty_diff(proc.stdout, path=path)


async def _fzf_rhs(
    diff: bool, unified: int, ref: str, path: Optional[PurePath]
) -> None:
    if path:
        if diff:
            await _git_show_diff(unified, ref=ref, path=path)
        else:
            await pretty_file(ref, path=path)
    else:
        await pretty_commit(unified, sha=ref)


def _parse_args() -> SPEC:
    parser = ArgumentParser()
    parser.add_argument("-d", "--diff", action="store_true")
    parser.add_argument("-u", "--unified", type=int, default=3)
    parser.add_argument("-p", "--path", type=PurePath)

    parser.add_argument("-r", "--regex", action="store_true")
    parser.add_argument("search", nargs="*", default=())

    return spec_parse(parser)


async def _main() -> int:
    mode, lines, args = _parse_args()

    if mode is Mode.preview:
        line, *_ = lines
        ref, *_ = line.split()
        await _fzf_rhs(diff=args.diff, unified=args.unified, ref=ref, path=args.path)

    elif mode is Mode.execute:
        line, *_ = lines
        ref, *_ = line.split()
        re, pos = _ref(ref)
        print_argv(f"{re}@{{{pos + 1}}}")

    elif mode is Mode.normal:
        reflog = await _git_reflog(args.regex, path=args.path, search=args.search)
        await _fzf_lhs(reflog)

    else:
        never(mode)

    return 0


def main() -> NoReturn:
    run_main(_main())
