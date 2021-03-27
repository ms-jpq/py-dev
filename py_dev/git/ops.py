from itertools import takewhile
from os import environ
from pathlib import Path
from shlex import join, split
from shutil import which
from subprocess import check_call, check_output, run
from tempfile import NamedTemporaryFile, mkdtemp
from typing import Iterable, Optional, Tuple

from ..ccat.pprn import pprn_basic


def git_show_many(it: Iterable[Tuple[str, str]]) -> None:
    tmp = Path(mkdtemp())
    for sha, path in it:
        temp = tmp / path
        raw = check_output(("git", "show", f"{sha}:{path}"))
        temp.write_bytes(raw)

    print(join(("cd", str(tmp))))


def pprn(content: bytes, path: Optional[str]) -> None:
    cmd = "bat"
    if path and which(cmd):
        suffix = "".join(Path(path).suffixes)
        with NamedTemporaryFile(suffix=suffix) as fd:
            fd.write(content)
            fd.flush()
            check_call((cmd, "--color=always", "--", fd.name))
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
