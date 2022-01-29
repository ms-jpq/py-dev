from asyncio import gather
from os import environ, linesep
from pathlib import PurePath
from shlex import split
from shutil import which
from sys import stdout
from tempfile import NamedTemporaryFile
from typing import Iterable, Optional

from std2.asyncio.subprocess import call
from std2.shutil import hr

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


async def pretty_file(sha: str, path: PurePath) -> None:
    proc = await call(
        "git",
        "show",
        f"{sha}:{path}",
        capture_stderr=False,
    )
    await pprn(proc.out, path=path)


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


async def pretty_commit(unified: int, sha: str) -> None:
    c1 = call(
        "git",
        "show",
        "--submodule",
        "--no-patch",
        "--color",
        sha,
        capture_stderr=False,
    )
    c2 = call(
        "git",
        "diff-tree",
        "--no-commit-id",
        "--find-renames",
        "--name-status",
        "-r",
        sha,
        capture_stderr=False,
    )
    c3 = call(
        "git",
        "show",
        "--submodule",
        "--color-moved=dimmed-zebra",
        "--color-moved-ws=ignore-space-change",
        "--ignore-space-change",
        f"--unified={unified}",
        "--pretty=format:",
        sha,
        capture_stderr=False,
    )

    p1, p2, p3 = await gather(c1, c2, c3)

    def cont() -> Iterable[str]:
        yield p1.out.decode()
        yield linesep
        yield hr()
        yield linesep
        yield p2.out.decode()
        yield hr()
        yield linesep

    stdout.writelines(cont())
    stdout.flush()

    await pretty_diff(p3.out, path=None)
