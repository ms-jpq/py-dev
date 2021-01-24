from argparse import ArgumentParser, Namespace
from locale import strxfrm
from os import linesep
from pathlib import Path, PurePath
from subprocess import check_output
from typing import Iterable, Iterator, MutableMapping, MutableSet, Tuple
from std2.tree import recur_sort
from py_dev.run import run_main

from ..fzf import run_fzf
from ..spec_parse import spec_parse


def _git_ls_commits() -> Iterator[Tuple[str, str]]:
    out = check_output(
        (
            "git",
            "log",
            "--relative-date",
            "--color=always",
            "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset",
        ),
        text=True,
    )
    for commit in out.strip("\0").split("\0"):
        sha, _, date = commit.partition(" ")
        yield sha, date


def _fzf_lhs(commits: Iterable[Tuple[str, str]]) -> None:
    stdin = "\0".join(f"{sha} {date}" for sha, date in commits).encode()
    run_fzf(stdin, p_args=("--preview={f}",), e_args=("--execute={f}",))


def _git_show_diff(sha: str) -> bytes:
    root = check_output(("git", "rev-parse", "--show-toplevel"), text=True).rstrip()
    out = check_output(("git", "diff", f"--name-only", "-z", f"{sha}~", sha), text=True)
    files = tuple(map(PurePath, out.strip("\0").split("\0")))

    registry: MutableMapping[PurePath, MutableSet[PurePath]] = {}

    def _recur(path: PurePath) -> None:
        if path.parent != path:
            children = registry.setdefault(path.parent, set())
            children.add(path)

    for file in files:
        _recur(file)

    for key, val in registry.items():
        print(key, val)


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
        sha, _, _ = preview.partition(" ")
        _git_show_diff(sha)
    elif args.execute:
        execute = Path(args.execute).read_text().rstrip("\0")
        sha, _, _ = execute.partition(" ")
    else:
        commits = _git_ls_commits()
        _fzf_lhs(commits)


run_main(main)
