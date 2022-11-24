from asyncio import gather
from functools import lru_cache
from os import environ, linesep
from pathlib import Path, PurePath
from shlex import join, split
from shutil import which
from sys import stdout
from tempfile import NamedTemporaryFile
from typing import Optional

from std2.asyncio.subprocess import call
from std2.shutil import hr

from ..ccat.pprn import pprn_basic


def print_argv(*args: str, escape: bool) -> None:
    stdout.write(join(args) if escape else " ".join(args))
    stdout.write(linesep)


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


@lru_cache(maxsize=None)
async def git_root() -> PurePath:
    proc = await call("git", "rev-parse", "--show-toplevel", capture_stderr=False)
    return PurePath(proc.stdout.rstrip().decode())


async def pretty_file(sha: str, path: PurePath) -> None:
    root = await git_root()
    abs = Path.cwd() / path
    rel = abs.relative_to(root)
    proc = await call(
        "git",
        "show",
        "--relative",
        f"{sha}:{rel}",
        capture_stderr=False,
    )
    await pprn(proc.stdout, path=path)


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
        "log",
        "--max-count=1",
        "--color",
        "--name-status",
        "--relative",
        sha,
        capture_stdout=False,
        capture_stderr=False,
    )
    c2 = call(
        "git",
        "show",
        "--submodule",
        "--relative",
        f"--unified={unified}",
        "--pretty=format:",
        sha,
        capture_stderr=False,
    )

    _, proc = await gather(c1, c2)

    stdout.writelines((linesep, hr(), linesep))
    stdout.flush()
    await pretty_diff(proc.stdout, path=None)
