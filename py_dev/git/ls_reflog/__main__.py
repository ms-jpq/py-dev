from argparse import ArgumentParser
from pathlib import PurePath
from re import compile
from typing import NoReturn, Optional

from std2.asyncio.subprocess import call
from std2.types import never

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_commit, pretty_diff, pretty_file
from ..spec_parse import SPEC, Mode, spec_parse


async def _git_reflog(path: Optional[PurePath]) -> bytes:
    proc = await call(
        "git",
        "log",
        "--walk-reflogs",
        "--color",
        "--pretty=format:%x00%Cgreen%gD%Creset %Cblue%ad%Creset %s",
        "--",
        *((path,) if path else ()),
        capture_stderr=False,
    )
    return proc.stdout.strip(b"\0")


async def _fzf_lhs(reflog: bytes) -> None:
    await run_fzf(reflog)


async def _git_show_diff(unified: int, ref: str, path: PurePath) -> None:
    re = compile(r"HEAD@\{(\d+)\}")
    m = re.match(ref)
    assert m
    cur = int(m.group(1))
    proc = await call(
        "git",
        "diff",
        f"--unified={unified}",
        f"HEAD@{{{cur}}}",
        f"HEAD@{{{cur + 1}}}",
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
    parser.add_argument("path", nargs="?", type=PurePath)
    parser.add_argument("-d", "--diff", action="store_true")
    parser.add_argument("-u", "--unified", type=int, default=3)
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
        print(ref)

    elif mode is Mode.normal:
        reflog = await _git_reflog(args.path)
        await _fzf_lhs(reflog)

    else:
        never(mode)

    return 0


def main() -> NoReturn:
    run_main(_main())
