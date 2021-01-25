from itertools import takewhile
from os import environ, linesep
from pathlib import Path
from shlex import join, split
from shutil import which
from subprocess import run
from sys import stdout
from tempfile import NamedTemporaryFile
from typing import Optional

from ..ccat.pprn import pprn_basic


def print_git_show(sha: str, path: str) -> None:
    end = linesep if stdout.isatty() else ""
    cmd = join(("git", "show", f"{sha}~:{path}"))
    print(cmd, end=end)


def pprn(content: bytes, path: Optional[str]) -> None:
    cmd = "bat"
    if path and which(cmd):
        suffix = "".join(Path(path).suffixes)
        with NamedTemporaryFile(suffix=suffix) as fd:
            fd.write(content)
            fd.flush()
            run((cmd, "--color=always", "--", fd.name)).check_returncode()
    else:
        pretty = pprn_basic(path, text=content.decode())
        print(pretty, end="")


def pretty_diff(diff: bytes, path: Optional[str]) -> None:
    pager = environ.get("GIT_PAGER")
    if pager:
        parts = split(pager)
        prog, *args = reversed(tuple(takewhile(lambda p: p != "|", reversed(parts))))
        if which(prog):
            run((prog, *args), input=diff).check_returncode()
        else:
            pprn(diff, path=path)
    else:
        pprn(diff, path=path)
