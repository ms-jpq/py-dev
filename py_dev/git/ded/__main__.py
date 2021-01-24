from argparse import ArgumentParser, Namespace
from os import environ, linesep
from pathlib import Path
from shlex import join
from subprocess import check_output, run
from sys import stdout
from typing import Iterator, Tuple

from py_dev.run import run_main

from ...ccat.consts import DEFAULT_FORMATTER, DEFAULT_STYLE
from ...ccat.pprn import pprn
from ..spec_parse import EXEC_SELF, spec_parse


def _git_show(sha: str, path: str) -> None:
    end = linesep if stdout.isatty() else ""
    cmd = join(("git", "show", f"{sha}~:{path}"))
    print(cmd, end=end)


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
    lines = (f"{sha}{linesep}{date}{linesep}{path}" for sha, date, path in paths)
    stdin = "\0".join(lines).encode()

    run(
        ("fzf", "--read0", "--ansi", bind, preview_win, f"--preview={preview}"),
        env={**environ, "SHELL": EXEC_SELF},
        input=stdin,
    )


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
    return spec_parse(parser)


def main() -> None:
    args = _parse_args()
    if args.show:
        show = Path(args.show).read_text().strip()
        sha, _, path = show.split(linesep)
        _git_show(sha, path=path)
    elif args.preview:
        preview = Path(args.preview).read_text().strip()
        sha, _, path = preview.split(linesep)
        _fzf_preview(sha, path=path)
    else:
        paths = _git_dead_files()
        _fzf_show(paths)


run_main(main)
