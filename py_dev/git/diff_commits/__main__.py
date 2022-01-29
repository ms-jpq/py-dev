from argparse import ArgumentParser, Namespace
from pathlib import Path, PurePath

from std2.asyncio.subprocess import call
from std2.itertools import chunk

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
    lines = b"\0".join(
        status + b" " + path
        for status, path in chunk(proc.out.rstrip(b"\0").split(b"\0"), 2)
    )
    return lines


async def _git_diff_single(
    unified: int, older: str, newer: str, path: PurePath
) -> bytes:
    proc = await call(
        "git",
        "diff",
        "--color-moved=dimmed-zebra",
        "--color-moved-ws=ignore-space-change",
        "--ignore-space-change",
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
        e_args=(older, newer, f"--unified={unified}", "--execute={f}"),
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
        path, _, _ = Path(preview).read_text().rstrip("\0").partition(" ")
        await _fzf_rhs(args.unified, older=older, newer=newer, path=PurePath(path))

    elif execute := args.execute:
        path, _, _ = Path(execute).read_text().rstrip("\0").partition(" ")
        await _fzf_rhs(args.unified, older=older, newer=newer, path=PurePath(path))

    else:
        files = await _git_file_diff(older=older, newer=newer)
        await _fzf_lhs(args.unified, older=older, newer=newer, files=files)

    return 0


run_main(main())
