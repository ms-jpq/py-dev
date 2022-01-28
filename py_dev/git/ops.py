from itertools import takewhile
from os import environ
from os.path import normcase
from pathlib import Path, PurePath
from shlex import split
from shutil import which
from sys import stdout
from tempfile import NamedTemporaryFile
from typing import Optional

from std2.asyncio.subprocess import call

from ..ccat.pprn import pprn_basic


async def pprn(content: bytes, path: Optional[PurePath]) -> None:
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
        pretty = pprn_basic(normcase(path) if path else None, text=content.decode())
        stdout.write(pretty)


async def pretty_diff(diff: bytes, path: Optional[PurePath]) -> None:
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
