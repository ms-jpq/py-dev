#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from os import environ
from pathlib import Path
from subprocess import check_output, run

from ...ccat.consts import DEFAULT_FORMATTER, DEFAULT_STYLE
from ...ccat.pprn import pprn
from ...run import run_main
from ..spec_parse import EOF, EXEC_SELF, spec_parse


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
    exe = f"{path}{EOF}--show-sha={{+f1}}"
    bind = f"--bind=return:abort+execute:{exe}"
    preview_win = "--preview-window=right:70%:wrap"
    diff_arg = f"--unified={unified}{EOF}" if unified >= 0 else ""
    preview = f"{diff_arg}--preview-sha={{f1}}{EOF}{path}"

    run(
        ("fzf", "--ansi", "-m", bind, preview_win, f"--preview={preview}"),
        env={**environ, "SHELL": EXEC_SELF},
        input=commits,
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
        sha = Path(args.show_sha).read_text().strip()
        print(f"git show {sha}:{args.path}")
    elif args.preview_sha:
        sha = Path(args.preview_sha).read_text().strip()
        _fzf_rhs(args.unified, sha=sha, path=args.path)
    else:
        commits = _git_file_log(args.path)
        _fzf_lhs(args.unified, path=args.path, commits=commits)


run_main(main)
