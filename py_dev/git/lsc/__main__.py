from argparse import ArgumentParser, Namespace
from locale import strxfrm
from pathlib import Path, PurePath
from subprocess import check_output
from typing import (
    Iterable,
    Iterator,
    Literal,
    Mapping,
    MutableMapping,
    MutableSet,
    Tuple,
)

from std2.tree import recur_sort

from ...run import run_main
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


_REGISTRY = MutableMapping[PurePath, MutableMapping[PurePath, Literal[True]]]
_INDEX = Mapping[PurePath, Mapping[PurePath, Literal[True]]]


def _recur(path: PurePath, registry: _REGISTRY) -> None:
    parent = path.parent
    if parent != path:
        children = registry.setdefault(parent, {})
        children[parent] = True
        _recur(parent, registry=registry)


def _key_by(path: PurePath) -> Tuple[int, str]:
    return len(path.parents), strxfrm(str(path))


def _git_show_diff(sha: str) -> None:
    out = check_output(("git", "diff", f"--name-only", "-z", f"{sha}~", sha), text=True)
    files = tuple(map(PurePath, out.strip("\0").split("\0")))

    registry: _REGISTRY = {}
    for file in files:
        _recur(file, registry=registry)

    index: _INDEX = recur_sort(registry, key=_key_by)
    for key, val in index.items():
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
