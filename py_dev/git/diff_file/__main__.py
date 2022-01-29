from argparse import ArgumentParser, Namespace
from os.path import normcase
from pathlib import Path, PurePath

from std2.asyncio.subprocess import call

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff, pretty_file
from ..spec_parse import spec_parse


async def _git_file_log(path: PurePath) -> bytes:
    proc = await call(
        "git",
        "log",
        "--find-renames",
        "--find-copies",
        "--relative-date",
        "--color",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out.strip(b"\0")


async def _git_show_diff(unified: int, sha: str, path: PurePath) -> bytes:
    proc = await call(
        "git",
        "diff",
        "--find-renames",
        "--find-copies",
        "--color-moved=dimmed-zebra",
        "--color-moved-ws=ignore-space-change",
        "--ignore-space-change",
        f"--unified={unified}",
        f"{sha}~",
        sha,
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out


async def _fzf_lhs(unified: int, path: PurePath, commits: bytes) -> None:
    await run_fzf(
        commits,
        p_args=(normcase(path), f"--unified={unified}", "--preview={f}"),
        e_args=(normcase(path), f"--unified={unified}", "--execute={f}"),
    )


async def _fzf_rhs(unified: int, sha: str, path: PurePath) -> None:
    if unified >= 0:
        diff = await _git_show_diff(unified, sha=sha, path=path)
        await pretty_diff(diff, path=path)
    else:
        await pretty_file(sha, path=path)


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("path", type=PurePath)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()

    if preview := args.preview:
        sha, _, _ = Path(preview).read_text().rstrip("\0").partition(" ")
        await _fzf_rhs(args.unified, sha=sha, path=args.path)

    elif execute := args.execute:
        sha, _, _ = Path(execute).read_text().rstrip("\0").partition(" ")
        await pretty_file(sha, path=args.path)

    else:
        commits = await _git_file_log(args.path)
        await _fzf_lhs(args.unified, path=args.path, commits=commits)

    return 0


run_main(main())
