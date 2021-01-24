from argparse import ArgumentParser, Namespace
from io import BytesIO
from os import environ, linesep
from subprocess import run, check_output
from sys import argv, stdout
from typing import Iterator, Tuple

from py_dev.run import run_main

from ...ccat.consts import DEFAULT_FORMATTER, DEFAULT_STYLE
from ...ccat.pprn import pprn

_EOF = "\04"


def _git_dead_files() -> Iterator[Tuple[str, str, str]]:
    out = check_output(
        (
            "git",
            "log",
            "--diff-filter=D",
            "--name-only",
            "--relative-date",
            "--color=always",
            "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset",
        ),
        text=True,
    )
    for commit in out.split("\0"):
        meta, *paths = commit.split(linesep)
        sha, _, date = meta.partition(" ")
        for path in paths:
            if path:
                yield sha, date, path


def _fzf_show(paths: Iterator[Tuple[str, str, str]]) -> None:
    exe = "--show={f}"
    bind = f"--bind=return:abort+execute:{exe}"
    preview_win = "--preview-window=right:70%:wrap"
    preview = "--preview={f}"
    lines: Iterator[str] = (
        f"{sha}{linesep}{date}{linesep}{path}" for sha, date, path in paths
    )
    stdin = "\0".join(lines).encode()

    run(
        ("fzf", "--read0", "--ansi", bind, preview_win, f"--preview={preview}"),
        env={**environ, "SHELL": __file__},
        input=stdin,
    ).check_returncode()


def _fzf_preview(sha: str, path: str) -> None:
    content = check_output(("git", "show", f"{sha}~:{path}")).decode()
    pretty = pprn(
        format=DEFAULT_FORMATTER, theme=DEFAULT_STYLE, filename=path, text=content
    )
    print(pretty, end="")


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--show")

    try:
        _, a1, a2 = argv
        if a1 == "-c":
            return parser.parse_args(a2.split(_EOF))
        else:
            return parser.parse_args()
    except ValueError:
        return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.show:
        sha, _, path = args.show.strip().split(linesep)
        end = linesep if stdout.isatty() else ""
        print(f"git show {sha}~:{path}", end=end)
    elif args.preview:
        sha, _, path = args.preview.strip().split(linesep)
        _fzf_preview(sha, path)
    else:
        paths = _git_dead_files()
        _fzf_show(paths)


run_main(main)
