from argparse import ArgumentParser, Namespace
from os import linesep
from pathlib import Path
from subprocess import check_output
from typing import Iterator, Tuple

from ...run import run_main
from ..fzf import run_fzf
from ..ops import git_show_many, pprn
from ..spec_parse import spec_parse


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
    for commit in out.strip("\0").split("\0"):
        meta, *paths = commit.split(linesep)
        sha, _, date = meta.partition(" ")
        for path in paths:
            if path:
                yield f"{sha}~", date, path


def _fzf_lhs(paths: Iterator[Tuple[str, str, str]]) -> None:
    lines = (f"{sha}{linesep}{date}{linesep}{path}" for sha, date, path in paths)
    stdin = "\0".join(lines).encode()
    run_fzf(stdin, p_args=("--preview={f}",), e_args=("--execute={{f}}",))


def _fzf_rhs(sha: str, path: str) -> None:
    content = check_output(("git", "show", f"{sha}:{path}"))
    pprn(content, path=path)


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")
    return spec_parse(parser)


def main() -> None:
    args = _parse_args()
    if args.preview:
        preview = Path(args.preview).read_text().rstrip("\0")
        sha, _, path = preview.split(linesep)
        _fzf_rhs(sha, path=path)
    elif args.execute:
        lines = Path(args.execute).read_text().rstrip("\0").split("\0")

        def cont() -> Iterator[Tuple[str, str]]:
            for line in lines:
                sha, _, path = line.split(linesep)
                yield sha, path

        git_show_many(cont())
    else:
        paths = _git_dead_files()
        _fzf_lhs(paths)


run_main(main)
