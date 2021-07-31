from os import environ
from typing import Iterable

from std2.asyncio.subprocess import call

from .spec_parse import EOF, EXEC_SELF

_SHARED_OPTS = (
    "--read0",
    "--print0",
    "--multi",
    "--ansi",
    "--preview-window=right:70%:wrap",
)


async def run_fzf(stdin: bytes, p_args: Iterable[str], e_args: Iterable[str]) -> None:
    fin = f"--bind=return:abort+execute:{EOF.join(e_args)}"
    rhs = f"--preview={EOF.join(p_args)}"
    await call(
        "fzf",
        *_SHARED_OPTS,
        rhs,
        fin,
        env={**environ, "LC_ALL": "C", "SHELL": EXEC_SELF},
        stdin=stdin,
        capture_stdout=False,
        capture_stderr=False,
    )
