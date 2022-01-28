from argparse import ArgumentParser, Namespace
from pathlib import Path

from std2.asyncio.subprocess import call

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pprn, pretty_diff
from ..spec_parse import spec_parse


async def _git_file_log(path: str) -> bytes:
    proc = await call(
        "git",
        "log",
        "--relative-date",
        "--color=always",
        "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out.strip(b"\0")


async def _git_show_file(sha: str, path: str) -> bytes:
    proc = await call(
        "git",
        "show",
        f"{sha}:{path}",
        capture_stderr=False,
    )
    return proc.out


async def _git_show_diff(unified: int, sha: str, path: str) -> bytes:
    proc = await call(
        "git",
        "diff",
        f"--unified={unified}",
        f"{sha}~",
        sha,
        "--",
        path,
        capture_stderr=False,
    )
    return proc.out


async def _fzf_lhs(unified: int, path: str, commits: bytes) -> None:
    await run_fzf(
        commits,
        p_args=(path, f"--unified={unified}", "--preview={f}"),
        e_args=(path, f"--unified={unified}", "--execute={f}"),
    )


async def _fzf_rhs(unified: int, sha: str, path: str) -> None:
    if unified >= 0:
        diff = await _git_show_diff(unified, sha=sha, path=path)
        await pretty_diff(diff, path=path)
    else:
        content = await _git_show_file(f"{sha}~", path=path)
        await pprn(content, path=path)


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("path")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


async def main() -> int:
    args = _parse_args()

    if args.preview:
        sha, _, _ = Path(args.preview).read_text().rstrip("\0").partition(" ")
        await _fzf_rhs(args.unified, sha=sha, path=args.path)
    elif args.execute:
        sha, _, _ = Path(args.execute).read_text().rstrip("\0").partition(" ")
        await call(
            "git",
            "show",
            f"{sha}:{args.path}",
            capture_stdout=False,
            capture_stderr=False,
        )
    else:
        commits = await _git_file_log(args.path)
        await _fzf_lhs(args.unified, path=args.path, commits=commits)

    return 0


run_main(main())
