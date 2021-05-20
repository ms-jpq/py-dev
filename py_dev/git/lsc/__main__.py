from argparse import ArgumentParser, Namespace
from os import linesep
from pathlib import Path
from subprocess import check_call, check_output
from typing import Iterable, Iterator, Tuple

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import spec_parse


def _git_ls_commits() -> Iterator[Tuple[str, str]]:
    out = check_output(
        (
            "git",
            "log",
            "--relative-date",
            "--color",
            "--pretty=format:%x00%Cgreen%h%Creset %Cblue%ad%Creset %s",
        ),
        text=True,
    )
    for commit in out.strip("\0").split("\0"):
        sha, _, date = commit.partition(" ")
        yield sha, date


def _fzf_lhs(commits: Iterable[Tuple[str, str]]) -> None:
    stdin = "\0".join(f"{sha} {date}" for sha, date in commits).encode()
    run_fzf(stdin, p_args=("--preview={f}",), e_args=("--execute={f}",))


def _git_show_commit(sha: str) -> None:
    check_call(("git", "show", "--submodule", "--stat", "--color", sha))
    print(linesep * 3)
    diffs = check_output(
        (
            "git",
            "show",
            "--submodule",
            "--pretty=format:",
            sha,
        )
    )
    pretty_diff(diffs, path=None)


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
        _git_show_commit(sha)
    elif args.execute:
        execute = Path(args.execute).read_text().rstrip("\0")
        sha, _, _ = execute.partition(" ")
    else:
        commits = _git_ls_commits()
        _fzf_lhs(commits)


run_main(main)
