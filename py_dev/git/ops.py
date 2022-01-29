from os import environ
from pathlib import PurePath
from shlex import split
from shutil import which
from sys import stdout
from tempfile import NamedTemporaryFile
from typing import Optional

from std2.asyncio.subprocess import call

from ..ccat.pprn import pprn_basic


async def pprn(content: bytes, path: Optional[PurePath]) -> None:
    if path and (bat := which("bat")):
        suffix = "".join(path.suffixes)
        with NamedTemporaryFile(suffix=suffix) as fd:
            fd.write(content)
            fd.flush()
            await call(
                bat,
                "--color=always",
                "--",
                fd.name,
                capture_stdout=False,
                capture_stderr=False,
            )
    else:
        pretty = pprn_basic(path, text=content.decode())
        stdout.write(pretty)


async def pretty_diff(diff: bytes, path: Optional[PurePath]) -> None:
    if args := split(environ.get("GIT_PAGER", "")):
        await call(
            *args,
            stdin=diff,
            capture_stdout=False,
            capture_stderr=False,
        )

    elif delta := which("delta"):
        await call(
            delta,
            stdin=diff,
            capture_stdout=False,
            capture_stderr=False,
        )

    else:
        await pprn(diff, path=path)


async def pretty_show_file(sha: str, path: PurePath) -> None:
    proc = await call(
        "git",
        "show",
        f"{sha}:{path}",
        capture_stderr=False,
    )
    await pprn(proc.out, path=path)
