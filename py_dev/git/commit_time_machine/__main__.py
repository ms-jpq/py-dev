from argparse import ArgumentParser, Namespace
from pathlib import Path, PurePath

from std2.asyncio.subprocess import call

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import spec_parse


async def _git_file_diff(sha1: str, sha2: str) -> bytes:
    proc = await call(
        "git",
        "diff",
        "--name-only",
        "-z",
        sha1,
        sha2,
        capture_stderr=False,
    )
    return proc.out.strip(b"\0")


async def _git_diff_single(unified: int, sha1: str, sha2: str, path: PurePath) -> bytes:
    proc = await call(
        "git",
        "diff",
        f"--unified={unified}",
        sha1,
        sha2,
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out


async def _fzf_lhs(unified: int, sha1: str, sha2: str, files: bytes) -> None:
    await run_fzf(
        files,
        p_args=(sha1, sha2, f"--unified={unified}", "--preview={f}"),
        e_args=(sha1, sha2, f"--unified={unified}", "--execute={f}"),
    )


async def _fzf_rhs(unified: int, sha1: str, sha2: str, path: PurePath) -> None:
    diff = await _git_diff_single(unified, sha1=sha1, sha2=sha2, path=path)
    await pretty_diff(diff, path=path)


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("sha1")
    parser.add_argument("sha2")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()

    if args.preview:
        path = PurePath(Path(args.preview).read_text().rstrip("\0"))
        await _fzf_rhs(args.unified, sha1=args.sha1, sha2=args.sha2, path=path)
    elif args.execute:
        path = PurePath(Path(args.execute).read_text().rstrip("\0"))
        await _fzf_rhs(args.unified, sha1=args.sha1, sha2=args.sha2, path=path)
    else:
        commits = await _git_file_diff(sha1=args.sha1, sha2=args.sha2)
        await _fzf_lhs(args.unified, sha1=args.sha1, sha2=args.sha2, files=commits)

    return 0


run_main(main())
