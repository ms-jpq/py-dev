from argparse import ArgumentParser, Namespace
from pathlib import Path, PurePath

from std2.asyncio.subprocess import call

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import spec_parse


async def _git_file_diff(dst: str, src: str) -> bytes:
    proc = await call(
        "git",
        "diff",
        "--name-only",
        "-z",
        dst,
        src,
        capture_stderr=False,
    )
    return proc.out.strip(b"\0")


async def _git_diff_single(unified: int, dst: str, src: str, path: PurePath) -> bytes:
    proc = await call(
        "git",
        "diff",
        "--color-moved=dimmed-zebra",
        "--color-moved-ws=ignore-space-change",
        "--ignore-space-change",
        f"--unified={unified}",
        dst,
        src,
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out


async def _fzf_lhs(unified: int, dst: str, src: str, files: bytes) -> None:
    await run_fzf(
        files,
        p_args=(dst, src, f"--unified={unified}", "--preview={f}"),
        e_args=(dst, src, f"--unified={unified}", "--execute={f}"),
    )


async def _fzf_rhs(unified: int, dst: str, src: str, path: PurePath) -> None:
    diff = await _git_diff_single(unified, dst=dst, src=src, path=path)
    await pretty_diff(diff, path=path)


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("src", nargs="?", default="HEAD")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()
    dst, src = args.dst, args.src

    if preview := args.preview:
        path = PurePath(Path(preview).read_text().rstrip("\0"))
        await _fzf_rhs(args.unified, dst=dst, src=src, path=path)

    elif execute := args.execute:
        path = PurePath(Path(execute).read_text().rstrip("\0"))
        await _fzf_rhs(args.unified, dst=dst, src=src, path=path)

    else:
        commits = await _git_file_diff(dst=dst, src=src)
        await _fzf_lhs(args.unified, dst=dst, src=src, files=commits)

    return 0


run_main(main())
