from itertools import takewhile
from os import environ, linesep
from shlex import join, split
from shutil import which
from subprocess import run
from sys import stdout

from ..ccat.pprn import pprn_basic


def print_git_show(sha: str, path: str) -> None:
    end = linesep if stdout.isatty() else ""
    cmd = join(("git", "show", f"{sha}~:{path}"))
    print(cmd, end=end)


def pretty_diff(diff: bytes, path: str) -> None:
    pager = environ.get("GIT_PAGER")
    if pager:
        parts = split(pager)
        prog, *args = reversed(tuple(takewhile(lambda p: p != "|", reversed(parts))))
        if which(prog):
            run((prog, *args), input=diff).check_returncode()
        else:
            pretty = pprn_basic(path, text=diff.decode())
            print(pretty, end="")
    else:
        pretty = pprn_basic(path, text=diff.decode())
        print(pretty, end="")
