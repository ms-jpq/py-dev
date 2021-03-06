from argparse import ArgumentParser, Namespace
from pathlib import Path
from subprocess import check_call, check_output

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pprn, pretty_diff
from ..spec_parse import spec_parse


def _git_file_log(path: str) -> bytes:
    return check_output(
        (
            "git",
            "log",
            "--relative-date",
            "--color=always",
            "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
            "--",
            path,
        ),
    ).strip(b"\0")


def _git_show_file(sha: str, path: str) -> bytes:
    return check_output(("git", "show", f"{sha}:{path}"))


def _git_show_diff(unified: int, sha: str, path: str) -> bytes:
    return check_output(
        ("git", "diff", f"--unified={unified}", f"{sha}~", sha, "--", path)
    )


def _fzf_lhs(unified: int, path: str, commits: bytes) -> None:
    run_fzf(
        commits,
        p_args=(path, f"--unified={unified}", "--preview={f}"),
        e_args=(path, f"--unified={unified}", "--execute={f}"),
    )


def _fzf_rhs(unified: int, sha: str, path: str) -> None:
    if unified >= 0:
        diff = _git_show_diff(unified, sha=sha, path=path)
        pretty_diff(diff, path=path)
    else:
        content = _git_show_file(sha, path=path)
        pprn(content, path=path)


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("path")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


def main() -> None:
    args = _parse_args()

    if args.preview:
        sha, _, _ = Path(args.preview).read_text().rstrip("\0").partition(" ")
        _fzf_rhs(args.unified, sha=sha, path=args.path)
    elif args.execute:
        sha, _, _ = Path(args.execute).read_text().rstrip("\0").partition(" ")
        check_call(("git", "show", f"{sha}:{args.path}"))
    else:
        commits = _git_file_log(args.path)
        _fzf_lhs(args.unified, path=args.path, commits=commits)


run_main(main)

