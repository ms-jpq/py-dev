from itertools import takewhile
from os import environ
from os.path import normcase
from pathlib import Path
from shlex import join, split
from shutil import which
from sys import stdout
from tempfile import NamedTemporaryFile, mkdtemp
from typing import Iterable, Optional, Tuple

from std2.asyncio.subprocess import call
from std2.shutil import hr_print

from ..ccat.pprn import pprn_basic
from ..log import log


async def git_show_many(it: Iterable[Tuple[str, str]]) -> None:
    tmp = Path(mkdtemp())
    for sha, path in it:
        temp = tmp / path
        proc = await call(
            "git",
            "show",
            f"{sha}:{path}",
            capture_stderr=False,
        )
        temp.parent.mkdir(parents=True, exist_ok=True)
        temp.write_bytes(proc.out)

    line = "\t" + join(("cd", normcase(tmp)))
    log.info("%s", hr_print(line))


async def pprn(content: bytes, path: Optional[str]) -> None:
    cmd = "bat"
    if path and which(cmd):
        suffix = "".join(Path(path).suffixes)
        with NamedTemporaryFile(suffix=suffix) as fd:
            fd.write(content)
            fd.flush()
            await call(
                cmd,
                "--color=always",
                "--",
                fd.name,
                capture_stdout=False,
                capture_stderr=False,
            )
    else:
        pretty = pprn_basic(path, text=content.decode())
        stdout.write(pretty)


async def pretty_diff(diff: bytes, path: Optional[str]) -> None:
    pager = environ.get("GIT_PAGER")
    if pager:
        parts = split(pager)
        prog, *args = reversed(tuple(takewhile(lambda p: p != "|", reversed(parts))))
        if which(prog):
            await call(
                prog,
                *args,
                stdin=diff,
                capture_stdout=False,
                capture_stderr=False,
            )
        else:
            await pprn(diff, path=path)
    else:
        await pprn(diff, path=path)
