from argparse import ArgumentParser, Namespace
from pathlib import Path
from subprocess import check_output

from ...ccat.consts import DEFAULT_FORMATTER, DEFAULT_STYLE
from ...ccat.pprn import pprn
from ...run import run_main
from ..fzf import run_fzf
from ..ops import print_git_show
from ..spec_parse import spec_parse


def _git_file_log(path: str) -> bytes:
    return check_output(
        (
            "git",
            "log",
            "--relative-date",
            "--color=always",
            "--pretty=format:%Cgreen%h%Creset %Cblue%ad%Creset %s",
            "--",
            path,
        ),
    )


def _git_show_file(sha: str, path: str) -> bytes:
    return check_output(("git", "show", f"{sha}:{path}"))


def _git_show_diff(unified: int, sha: str, path: str) -> bytes:
    return check_output(
        ("git", "diff", f"--unified={unified}", f"{sha}~", sha, "--", path)
    )


def _fzf_lhs(unified: int, path: str, commits: bytes) -> None:
    run_fzf(
        commits,
        f_args=(path, f"--unified={unified}", "--show-sha={+f1}"),
        p_args=(path, f"--unified={unified}", "--preview-sha={f1}"),
    )


# def _prettify_diff(diff: bytes) -> None:
#     pager = environ.get("GIT_PAGER", "tee")
#     cmd = next(iter(pager.split("|", 1)))
#     prog, *args = cmd.split(" ")
#     ret = run((prog, *(a for a in args if a)), input=diff)
#     ret.check_returncode()


def _fzf_rhs(unified: int, sha: str, path: str) -> None:
    if unified >= 0:
        text = _git_show_diff(unified, sha=sha, path=path).decode()
    else:
        text = _git_show_file(sha, path=path).decode()

    pretty = pprn(
        format=DEFAULT_FORMATTER, theme=DEFAULT_STYLE, filename=path, text=text
    )
    print(pretty, end="")


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("path")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview-sha")
    group.add_argument("--show-sha")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


def main() -> None:
    args = _parse_args()

    if args.show_sha:
        sha = Path(args.show_sha).read_text().rstrip("\0")
        print_git_show(sha, path=args.path)
    elif args.preview_sha:
        sha = Path(args.preview_sha).read_text().rstrip("\0")
        _fzf_rhs(args.unified, sha=sha, path=args.path)
    else:
        commits = _git_file_log(args.path)
        _fzf_lhs(args.unified, path=args.path, commits=commits)


run_main(main)
